from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analysis_service import (
    get_consensus_buys,
    get_high_conviction,
    get_beaten_down,
)

router = APIRouter()


@router.get("/consensus")
async def consensus_buys(
    min_investors: int = Query(2, ge=2, le=5),
    db: AsyncSession = Depends(get_db),
):
    """N명 이상이 같은 분기에 신규 매수한 종목."""
    return await get_consensus_buys(db, min_investors=min_investors)


@router.get("/high-conviction")
async def high_conviction(
    min_weight: float = Query(5.0, ge=1.0),
    db: AsyncSession = Depends(get_db),
):
    """포트폴리오 비중 N% 이상 신규 진입 종목."""
    return await get_high_conviction(db, min_weight_pct=min_weight)


@router.get("/beaten-down")
async def beaten_down(db: AsyncSession = Depends(get_db)):
    """현재가 < 기관 평균 매수가 추정치 종목 (저평가 기회)."""
    return await get_beaten_down(db)


@router.get("/new-buys")
async def all_new_buys(db: AsyncSession = Depends(get_db)):
    """전체 투자자의 최신 분기 신규 매수 종목."""
    from sqlalchemy import select
    from app.models import Filing, Holding
    from app.config import INVESTOR_MAP
    from app.services.analysis_service import get_latest_filings

    latest = await get_latest_filings(db)
    results = []
    for inv_id, filing in latest.items():
        inv_info = INVESTOR_MAP.get(inv_id, {})
        holdings = await db.scalars(
            select(Holding).where(
                Holding.filing_id == filing.id,
                Holding.is_new == True,
            ).order_by(Holding.value.desc())
        )
        total = filing.total_value or 1
        for h in holdings.all():
            results.append({
                "investor_id": inv_id,
                "investor_name": inv_info.get("name", inv_id),
                "manager": inv_info.get("manager", ""),
                "color": inv_info.get("color", "#888"),
                "ticker": h.ticker,
                "company_name": h.company_name,
                "value_k": h.value,
                "value_m": round(h.value / 1000, 2),
                "shares": h.shares,
                "weight_pct": round(h.value / total * 100, 2),
                "period": filing.period_of_report,
            })
    results.sort(key=lambda x: -x["value_k"])
    return results
