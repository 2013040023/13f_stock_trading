"""13F 분석 서비스: 컨센서스 매수, 신규 진입, 저평가 스크리닝."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Filing, Holding
from app.config import INVESTOR_MAP


async def get_latest_filings(db: AsyncSession) -> dict[str, Filing]:
    """투자자별 최신 Filing 반환."""
    filings = await db.scalars(
        select(Filing).order_by(Filing.period_of_report.desc())
    )
    latest: dict[str, Filing] = {}
    for f in filings.all():
        if f.investor_id not in latest:
            latest[f.investor_id] = f
    return latest


async def get_consensus_buys(db: AsyncSession, min_investors: int = 2) -> list[dict]:
    """같은 분기에 N명 이상이 신규 매수한 종목."""
    latest = await get_latest_filings(db)
    if not latest:
        return []

    # 최신 공통 period 찾기 (대략)
    periods = sorted({f.period_of_report for f in latest.values()}, reverse=True)
    latest_period = periods[0] if periods else None

    # 같은 period의 신규 매수 집계
    cusip_investors: dict[str, list[dict]] = defaultdict(list)

    for inv_id, filing in latest.items():
        if abs_diff_quarters(filing.period_of_report, latest_period) > 1:
            continue
        holdings = await db.scalars(
            select(Holding).where(
                Holding.filing_id == filing.id,
                Holding.is_new == True,
            )
        )
        for h in holdings.all():
            inv_info = INVESTOR_MAP.get(inv_id, {})
            cusip_investors[h.cusip].append({
                "investor_id": inv_id,
                "investor_name": inv_info.get("name", inv_id),
                "manager": inv_info.get("manager", ""),
                "ticker": h.ticker,
                "company_name": h.company_name,
                "value": h.value,
                "shares": h.shares,
            })

    results = []
    for cusip, investors in cusip_investors.items():
        if len(investors) >= min_investors:
            total_value = sum(i["value"] for i in investors)
            results.append({
                "cusip": cusip,
                "ticker": investors[0]["ticker"],
                "company_name": investors[0]["company_name"],
                "investor_count": len(investors),
                "investors": investors,
                "total_value_k": total_value,
            })

    results.sort(key=lambda x: (-x["investor_count"], -x["total_value_k"]))
    return results


async def get_high_conviction(db: AsyncSession, min_weight_pct: float = 5.0) -> list[dict]:
    """포트폴리오 비중 5% 이상 신규 진입 종목."""
    latest = await get_latest_filings(db)
    results = []

    for inv_id, filing in latest.items():
        if filing.total_value == 0:
            continue
        holdings = await db.scalars(
            select(Holding).where(
                Holding.filing_id == filing.id,
                Holding.is_new == True,
            )
        )
        inv_info = INVESTOR_MAP.get(inv_id, {})
        for h in holdings.all():
            weight = h.value / filing.total_value * 100
            if weight >= min_weight_pct:
                results.append({
                    "investor_id": inv_id,
                    "investor_name": inv_info.get("name", inv_id),
                    "manager": inv_info.get("manager", ""),
                    "ticker": h.ticker,
                    "company_name": h.company_name,
                    "weight_pct": round(weight, 2),
                    "value_k": h.value,
                    "shares": h.shares,
                    "period": filing.period_of_report,
                })

    results.sort(key=lambda x: -x["weight_pct"])
    return results


async def get_beaten_down(db: AsyncSession) -> list[dict]:
    """현재가가 기관 평균 매수가보다 낮은 종목 (저평가 기회)."""
    latest = await get_latest_filings(db)
    results = []

    for inv_id, filing in latest.items():
        holdings = await db.scalars(
            select(Holding).where(
                Holding.filing_id == filing.id,
                Holding.current_price.isnot(None),
                Holding.shares > 0,
            )
        )
        inv_info = INVESTOR_MAP.get(inv_id, {})
        for h in holdings.all():
            if h.shares <= 0:
                continue
            # 평균 매수가 추정: 공시 시점 value(천달러) / shares
            avg_cost_est = (h.value * 1000) / h.shares
            if h.current_price and h.current_price < avg_cost_est:
                discount = (avg_cost_est - h.current_price) / avg_cost_est * 100
                results.append({
                    "investor_id": inv_id,
                    "investor_name": inv_info.get("name", inv_id),
                    "manager": inv_info.get("manager", ""),
                    "ticker": h.ticker,
                    "company_name": h.company_name,
                    "avg_cost_est": round(avg_cost_est, 2),
                    "current_price": round(h.current_price, 2),
                    "discount_pct": round(discount, 2),
                    "value_k": h.value,
                    "shares": h.shares,
                    "period": filing.period_of_report,
                })

    results.sort(key=lambda x: -x["discount_pct"])
    return results


def abs_diff_quarters(p1: str, p2: str) -> int:
    """두 period(YYYY-MM-DD) 간 분기 차이."""
    if not p1 or not p2:
        return 99
    try:
        y1, m1 = int(p1[:4]), int(p1[5:7])
        y2, m2 = int(p2[:4]), int(p2[5:7])
        return abs((y1 * 4 + (m1 - 1) // 3) - (y2 * 4 + (m2 - 1) // 3))
    except Exception:
        return 99
