"""SEC EDGAR 13F 데이터 동기화 서비스."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import INVESTORS
from app.collectors.edgar import get_recent_13f_filings, get_13f_holdings
from app.collectors.prices import get_current_prices, resolve_ticker
from app.database import async_session
from app.models import Filing, Holding, CusipTicker

logger = logging.getLogger("13f.sync")

_SYNC_LOCK = asyncio.Lock()


async def sync_all(force: bool = False) -> dict:
    """모든 투자자의 최신 13F 동기화."""
    async with _SYNC_LOCK:
        results = {}
        for investor in INVESTORS:
            try:
                result = await sync_investor(investor["id"], investor["cik"], force=force)
                results[investor["id"]] = result
            except Exception as e:
                logger.error(f"[sync] {investor['id']} failed: {e}")
                results[investor["id"]] = {"status": "error", "error": str(e)}
        return results


async def sync_investor(investor_id: str, cik: str, force: bool = False) -> dict:
    """단일 투자자 13F 동기화."""
    logger.info(f"[sync] {investor_id} CIK={cik}")

    filings = await get_recent_13f_filings(cik, limit=4)
    if not filings:
        return {"status": "no_filings"}

    async with async_session() as db:
        synced = []
        for i, filing_meta in enumerate(reversed(filings)):
            acc = filing_meta["accession_number"]
            period = filing_meta["period_of_report"]

            # 이미 있으면 스킵 (force 아닌 경우)
            existing = await db.scalar(
                select(Filing).where(
                    Filing.investor_id == investor_id,
                    Filing.accession_number == acc,
                )
            )
            if existing and not force:
                logger.debug(f"[sync] {investor_id} {period} already exists, skip")
                continue

            logger.info(f"[sync] fetching {investor_id} {period}...")
            holdings_raw = await get_13f_holdings(cik, acc)
            if not holdings_raw:
                logger.warning(f"[sync] {investor_id} {period}: no holdings parsed")
                continue

            total_value = sum(h["value"] for h in holdings_raw)

            if existing:
                # 기존 데이터 업데이트: holdings 재생성
                await db.execute(delete(Holding).where(Holding.filing_id == existing.id))
                filing_obj = existing
                filing_obj.total_value = total_value
                filing_obj.fetched_at = datetime.utcnow()
            else:
                filing_obj = Filing(
                    investor_id=investor_id,
                    period_of_report=period,
                    filed_at=filing_meta["filed_at"],
                    accession_number=acc,
                    total_value=total_value,
                )
                db.add(filing_obj)
                await db.flush()

            # 전분기 보유 데이터 로드 (변동 계산용)
            prev_filing = await _get_prev_filing(db, investor_id, period)
            prev_map: dict[str, Holding] = {}
            if prev_filing:
                prev_holdings = await db.scalars(
                    select(Holding).where(Holding.filing_id == prev_filing.id)
                )
                prev_map = {h.cusip: h for h in prev_holdings.all()}

            # Holding 생성
            for h in holdings_raw:
                cusip = h["cusip"]
                prev = prev_map.get(cusip)
                shares_change = h["shares"] - (prev.shares if prev else 0)
                value_change = h["value"] - (prev.value if prev else 0)
                is_new = prev is None
                is_sold = False  # 이번 분기에 있으면 팔지 않은 것

                # CUSIP → ticker 캐시 확인
                ticker = await _get_ticker(db, cusip, h["company_name"])

                holding = Holding(
                    filing_id=filing_obj.id,
                    ticker=ticker,
                    cusip=cusip,
                    company_name=h["company_name"],
                    shares=h["shares"],
                    value=h["value"],
                    share_type=h["share_type"],
                    shares_change=shares_change,
                    value_change=value_change,
                    is_new=is_new,
                    is_sold=is_sold,
                )
                db.add(holding)

            # 전분기에는 있었지만 이번에 없는 종목 → sold 마킹 (전분기 filing에)
            if prev_filing:
                current_cusips = {h["cusip"] for h in holdings_raw}
                for cusip, prev_h in prev_map.items():
                    if cusip not in current_cusips:
                        prev_h.is_sold = True

            await db.commit()
            synced.append(period)

            # Rate limit 준수
            await asyncio.sleep(0.5)

        return {"status": "ok", "synced": synced}


async def _get_prev_filing(db: AsyncSession, investor_id: str, current_period: str) -> Filing | None:
    """현재 분기보다 이전 분기 공시 반환."""
    result = await db.scalars(
        select(Filing)
        .where(
            Filing.investor_id == investor_id,
            Filing.period_of_report < current_period,
        )
        .order_by(Filing.period_of_report.desc())
        .limit(1)
    )
    return result.first()


async def _get_ticker(db: AsyncSession, cusip: str, company_name: str) -> str | None:
    """CUSIP → Ticker (캐시 우선)."""
    cached = await db.get(CusipTicker, cusip)
    if cached:
        return cached.ticker

    ticker = await resolve_ticker(cusip, company_name)

    entry = CusipTicker(cusip=cusip, ticker=ticker, company_name=company_name)
    db.add(entry)
    try:
        await db.flush()
    except Exception:
        await db.rollback()

    return ticker


async def update_prices(investor_id=None) -> int:
    """최신 분기 holdings의 현재가 업데이트."""
    async with async_session() as db:
        # 최신 filing 조회
        query = select(Filing).order_by(Filing.period_of_report.desc())
        if investor_id:
            query = query.where(Filing.investor_id == investor_id)

        filings = await db.scalars(query)
        latest_per_investor: dict[str, Filing] = {}
        for f in filings.all():
            if f.investor_id not in latest_per_investor:
                latest_per_investor[f.investor_id] = f

        all_tickers: list[str] = []
        filing_holdings: dict[int, list[Holding]] = {}

        for f in latest_per_investor.values():
            holdings = await db.scalars(
                select(Holding).where(Holding.filing_id == f.id, Holding.ticker.isnot(None))
            )
            hs = holdings.all()
            filing_holdings[f.id] = hs
            all_tickers.extend([h.ticker for h in hs if h.ticker])

        if not all_tickers:
            return 0

        prices = await get_current_prices(list(set(all_tickers)))
        updated = 0
        now = datetime.utcnow()

        for hs in filing_holdings.values():
            for h in hs:
                if h.ticker and h.ticker in prices:
                    h.current_price = prices[h.ticker]
                    h.price_updated_at = now
                    updated += 1

        await db.commit()
        return updated
