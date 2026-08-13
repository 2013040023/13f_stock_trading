"""13F 트래커 텔레그램 봇.

명령어:
  /start   도움말
  /h       도움말
  /summary 5개 기관 운용 현황 요약
  /p <id>  특정 투자자 포트폴리오 (berkshire/himalaya/pershing/appaloosa/pabrai)
  /new     최신 분기 신규 매수 TOP 15
  /con     컨센서스 매수 (2명 이상 동시 신규 매수)
  /screen  스크리닝 (고비중 신규 + 저평가 기회)
  /sync    SEC EDGAR 데이터 동기화
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger("13f.telegram")

_INVESTOR_ALIASES = {
    "berkshire": "berkshire", "berk": "berkshire", "버크셔": "berkshire", "버핏": "berkshire",
    "himalaya": "himalaya", "hima": "himalaya", "히말라야": "himalaya", "릴루": "himalaya",
    "pershing": "pershing", "persh": "pershing", "퍼싱": "pershing", "애크먼": "pershing",
    "appaloosa": "appaloosa", "appa": "appaloosa", "아팔루사": "appaloosa", "테퍼": "appaloosa",
    "pabrai": "pabrai", "파브라이": "pabrai",
}

_INVESTOR_LABEL = {
    "berkshire": "버크셔 (버핏)",
    "himalaya": "히말라야 (릴루)",
    "pershing": "퍼싱 스퀘어 (애크먼)",
    "appaloosa": "아팔루사 (테퍼)",
    "pabrai": "파브라이 (파브라이)",
}


def _fmt_b(k: float) -> str:
    b = k / 1_000_000
    if b >= 1:
        return f"${b:.1f}B"
    return f"${k / 1000:.0f}M"


class ThirteenFBot:
    def __init__(self, token: str, allowed_ids: list[int]):
        self.token = token
        self.allowed_ids = allowed_ids
        self._base = f"https://api.telegram.org/bot{token}"
        self._offset = 0
        self._running = False

    async def start(self):
        self._running = True
        logger.info("[13f-bot] started")
        while self._running:
            try:
                updates = await self._get_updates()
                for upd in updates:
                    self._offset = upd["update_id"] + 1
                    asyncio.create_task(self._handle(upd))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[13f-bot] poll error: {e}")
                await asyncio.sleep(5)

    def stop(self):
        self._running = False

    async def _get_updates(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=35) as c:
            r = await c.get(f"{self._base}/getUpdates", params={
                "offset": self._offset,
                "timeout": 30,
                "allowed_updates": ["message"],
            })
            data = r.json()
            return data.get("result", []) if data.get("ok") else []

    async def _send(self, chat_id: int, text: str, md: bool = True):
        async with httpx.AsyncClient(timeout=15) as c:
            await c.post(f"{self._base}/sendMessage", json={
                "chat_id": chat_id,
                "text": text[:4000],
                "parse_mode": "Markdown" if md else None,
                "disable_web_page_preview": True,
            })

    async def _handle(self, upd: dict):
        msg = upd.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")
        text = (msg.get("text") or "").strip()

        if not chat_id or not text.startswith("/"):
            return
        if self.allowed_ids and user_id not in self.allowed_ids:
            await self._send(chat_id, "⛔ 접근 권한 없음")
            return

        cmd_parts = text.split()
        cmd = cmd_parts[0].split("@")[0].lower()
        args = cmd_parts[1:]

        handlers = {
            "/start": self._cmd_help,
            "/h": self._cmd_help,
            "/help": self._cmd_help,
            "/summary": self._cmd_summary,
            "/s": self._cmd_summary,
            "/p": self._cmd_portfolio,
            "/portfolio": self._cmd_portfolio,
            "/new": self._cmd_newbuys,
            "/newbuys": self._cmd_newbuys,
            "/con": self._cmd_consensus,
            "/consensus": self._cmd_consensus,
            "/screen": self._cmd_screen,
            "/sync": self._cmd_sync,
        }

        handler = handlers.get(cmd)
        if handler:
            try:
                await handler(chat_id, args)
            except Exception as e:
                logger.error(f"[13f-bot] handler error: {e}")
                await self._send(chat_id, f"❌ 오류: {e}")
        else:
            await self._send(chat_id, "❓ 알 수 없는 명령어. /h 로 도움말 확인")

    # ── Command handlers ────────────────────────────────────────────────────

    async def _cmd_help(self, chat_id: int, _):
        txt = (
            "📊 *13F 거장 트래커 봇*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "SEC 13F 공시 기반 장기 가치투자 거장 5인 포트폴리오 추적\n\n"
            "*명령어*\n"
            "`/summary` — 5개 기관 운용 현황 요약\n"
            "`/p <투자자>` — 포트폴리오 상세\n"
            "    버크셔/히말라야/퍼싱/아팔루사/파브라이\n"
            "`/new` — 최신 분기 신규 매수 TOP 15\n"
            "`/con` — 컨센서스 매수 (2명↑ 동시 신규)\n"
            "`/screen` — 고비중 신규 + 저평가 기회\n"
            "`/sync` — SEC EDGAR 데이터 동기화\n\n"
            "_⚠️ 13F는 최대 45일 시차 | 롱 포지션만 공개_"
        )
        await self._send(chat_id, txt)

    async def _cmd_summary(self, chat_id: int, _):
        from app.database import async_session
        from app.api.routes.investors import list_investors
        from app.database import get_db

        # DB에서 직접 가져오기
        from sqlalchemy import select, func
        from app.models import Filing, Holding
        from app.config import INVESTORS

        async with async_session() as db:
            lines = ["📊 *13F 거장 포트폴리오 현황*\n━━━━━━━━━━━━━━━━━━━━"]
            for inv in INVESTORS:
                latest = await db.scalar(
                    select(Filing)
                    .where(Filing.investor_id == inv["id"])
                    .order_by(Filing.period_of_report.desc())
                    .limit(1)
                )
                if not latest:
                    lines.append(f"\n*{inv['name']}* ({inv['manager']})\n  ⚠️ 데이터 없음")
                    continue

                cnt = await db.scalar(
                    select(func.count()).where(
                        Holding.filing_id == latest.id,
                        Holding.is_sold == False,
                    )
                ) or 0
                new_cnt = await db.scalar(
                    select(func.count()).where(
                        Holding.filing_id == latest.id,
                        Holding.is_new == True,
                    )
                ) or 0

                lines.append(
                    f"\n*{inv['name']}* ({inv['manager']})\n"
                    f"  💰 {_fmt_b(latest.total_value)} | 📦 {cnt}종목 | 🆕 신규 {new_cnt}개\n"
                    f"  _기준: {latest.period_of_report}_"
                )

            if "exempt_note" in INVESTORS[-1]:
                lines.append(f"\n⚫ *파브라이*: AUM $100M 미만 → 13F 면제")

        await self._send(chat_id, "\n".join(lines))

    async def _cmd_portfolio(self, chat_id: int, args: list[str]):
        if not args:
            await self._send(chat_id,
                "사용법: `/p <투자자>`\n"
                "예시: `/p berkshire` `/p 버핏` `/p 퍼싱`"
            )
            return

        alias = args[0].lower()
        inv_id = _INVESTOR_ALIASES.get(alias)
        if not inv_id:
            await self._send(chat_id,
                f"❓ `{alias}` 를 찾을 수 없습니다.\n"
                "가능한 값: berkshire / himalaya / pershing / appaloosa / pabrai"
            )
            return

        from app.database import async_session
        from sqlalchemy import select
        from app.models import Filing, Holding
        from app.config import INVESTOR_MAP

        inv = INVESTOR_MAP[inv_id]
        async with async_session() as db:
            filing = await db.scalar(
                select(Filing)
                .where(Filing.investor_id == inv_id)
                .order_by(Filing.period_of_report.desc())
                .limit(1)
            )
            if not filing:
                await self._send(chat_id, f"❌ {inv['name']} 데이터 없음. `/sync` 실행 후 재시도")
                return

            holdings = await db.scalars(
                select(Holding)
                .where(Holding.filing_id == filing.id, Holding.is_sold == False)
                .order_by(Holding.value.desc())
                .limit(20)
            )
            hs = holdings.all()

        total = filing.total_value or 1
        label = _INVESTOR_LABEL.get(inv_id, inv["name"])
        lines = [
            f"💼 *{label} 포트폴리오*",
            f"_{filing.period_of_report} 기준 | 총 {_fmt_b(filing.total_value)}_",
            "━━━━━━━━━━━━━━━━━━━━",
        ]
        for i, h in enumerate(hs, 1):
            ticker = h.ticker or "—"
            weight = h.value / total * 100
            change = ""
            if h.is_new:
                change = " 🆕"
            elif h.shares_change > 0:
                change = " ▲"
            elif h.shares_change < 0:
                change = " ▼"
            lines.append(
                f"`{i:2d}.` *{ticker}*{change}  {weight:.1f}%  {_fmt_b(h.value)}\n"
                f"     {h.company_name[:28]}"
            )

        lines.append(f"\n_상위 {len(hs)}개 표시 (전체 {filing.total_value/total*100:.0f}% = {_fmt_b(filing.total_value)})_")
        await self._send(chat_id, "\n".join(lines))

    async def _cmd_newbuys(self, chat_id: int, _):
        from app.database import async_session
        from sqlalchemy import select
        from app.models import Filing, Holding
        from app.config import INVESTORS, INVESTOR_MAP
        from app.services.analysis_service import get_latest_filings

        async with async_session() as db:
            latest = await get_latest_filings(db)
            rows = []
            for inv_id, filing in latest.items():
                inv = INVESTOR_MAP.get(inv_id, {})
                total = filing.total_value or 1
                hs = await db.scalars(
                    select(Holding).where(
                        Holding.filing_id == filing.id,
                        Holding.is_new == True,
                    ).order_by(Holding.value.desc())
                )
                for h in hs.all():
                    rows.append((
                        inv.get("manager", inv_id),
                        h.ticker or "?",
                        h.company_name[:20],
                        h.value,
                        h.value / total * 100,
                        filing.period_of_report,
                    ))

        rows.sort(key=lambda x: -x[3])
        lines = ["🆕 *신규 매수 TOP 15*\n_최신 분기 기준_\n━━━━━━━━━━━━━━━━━━━━"]
        for mgr, ticker, name, val, wt, period in rows[:15]:
            star = " ⭐" if wt >= 5 else ""
            lines.append(f"*{ticker}*{star} `{wt:.1f}%`  {_fmt_b(val)}\n  {mgr} | {name}")

        if not rows:
            lines.append("데이터 없음. `/sync` 실행 후 재시도")
        await self._send(chat_id, "\n".join(lines))

    async def _cmd_consensus(self, chat_id: int, _):
        from app.database import async_session
        from app.services.analysis_service import get_consensus_buys

        async with async_session() as db:
            items = await get_consensus_buys(db, min_investors=2)

        if not items:
            await self._send(chat_id, "컨센서스 매수 없음 (데이터 부족)")
            return

        lines = ["🎯 *컨센서스 매수*\n_2명 이상 동시 신규 매수_\n━━━━━━━━━━━━━━━━━━━━"]
        for item in items[:10]:
            ticker = item["ticker"] or "—"
            n = item["investor_count"]
            managers = " · ".join(i["manager"].split("(")[0].strip() for i in item["investors"][:3])
            lines.append(
                f"*{ticker}* 👥 {n}명\n"
                f"  {item['company_name'][:25]}\n"
                f"  {managers}\n"
                f"  합계 {_fmt_b(item['total_value_k'])}"
            )

        await self._send(chat_id, "\n".join(lines))

    async def _cmd_screen(self, chat_id: int, _):
        from app.database import async_session
        from app.services.analysis_service import get_high_conviction, get_beaten_down

        async with async_session() as db:
            conviction = await get_high_conviction(db, min_weight_pct=5.0)
            beaten = await get_beaten_down(db)

        lines = ["🔍 *투자 스크리닝*\n━━━━━━━━━━━━━━━━━━━━"]

        lines.append("\n⭐ *고비중 신규 진입 (5%↑)*")
        if conviction:
            for item in conviction[:5]:
                lines.append(
                    f"  *{item['ticker'] or '—'}* `{item['weight_pct']:.1f}%`  {_fmt_b(item['value_k'])}\n"
                    f"  {item['manager']} | {item['company_name'][:22]}"
                )
        else:
            lines.append("  없음")

        lines.append("\n📉 *저평가 기회 (현재가 < 매수가 추정)*")
        if beaten:
            for item in beaten[:5]:
                lines.append(
                    f"  *{item['ticker'] or '—'}* -{item['discount_pct']:.1f}%\n"
                    f"  추정매수가 ${item['avg_cost_est']:.1f} → 현재 ${item['current_price']:.1f}\n"
                    f"  {item['manager']}"
                )
        else:
            lines.append("  없음 (현재가 데이터 부족)")

        lines.append("\n_⚠️ 추정 매수가 = 공시 당시 value÷shares. 참고용_")
        await self._send(chat_id, "\n".join(lines))

    async def _cmd_sync(self, chat_id: int, _):
        await self._send(chat_id, "🔄 SEC EDGAR 동기화 시작… (수 분 소요)")
        from app.services.sync_service import sync_all
        try:
            results = await sync_all()
            lines = ["✅ *동기화 완료*\n━━━━━━━━━━━━━━━━━━━━"]
            for inv_id, res in results.items():
                from app.config import INVESTOR_MAP
                name = INVESTOR_MAP.get(inv_id, {}).get("name", inv_id)
                status = res.get("status", "?")
                synced = res.get("synced", [])
                if synced:
                    lines.append(f"✓ *{name}*: {', '.join(synced)}")
                elif status == "no_filings":
                    lines.append(f"— *{name}*: 공시 없음")
                elif status == "ok":
                    lines.append(f"✓ *{name}*: 최신 유지")
                else:
                    lines.append(f"❌ *{name}*: {res.get('error', status)}")
            await self._send(chat_id, "\n".join(lines))
        except Exception as e:
            await self._send(chat_id, f"❌ 동기화 실패: {e}")


# ── 싱글턴 관리 ──────────────────────────────────────────────────────────────

_bot_instance: Optional[ThirteenFBot] = None
_bot_task: Optional[asyncio.Task] = None


def get_bot() -> Optional[ThirteenFBot]:
    return _bot_instance


async def start_bot():
    global _bot_instance, _bot_task
    from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_IDS

    if not TELEGRAM_BOT_TOKEN:
        logger.warning("[13f-bot] TELEGRAM_BOT_TOKEN not set, skipping bot")
        return

    allowed = [int(x.strip()) for x in TELEGRAM_ALLOWED_USER_IDS.split(",") if x.strip().isdigit()]
    _bot_instance = ThirteenFBot(TELEGRAM_BOT_TOKEN, allowed)
    _bot_task = asyncio.create_task(_bot_instance.start())
    logger.info(f"[13f-bot] running (allowed: {allowed})")


async def stop_bot():
    global _bot_instance, _bot_task
    if _bot_instance:
        _bot_instance.stop()
    if _bot_task:
        _bot_task.cancel()
