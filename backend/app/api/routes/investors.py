from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import INVESTORS, INVESTOR_MAP
from app.database import get_db
from app.models import Filing, Holding

router = APIRouter()


@router.get("")
async def list_investors(db: AsyncSession = Depends(get_db)):
    results = []
    for inv in INVESTORS:
        # 최신 filing
        latest = await db.scalar(
            select(Filing)
            .where(Filing.investor_id == inv["id"])
            .order_by(Filing.period_of_report.desc())
            .limit(1)
        )
        holdings_count = 0
        if latest:
            holdings_count = await db.scalar(
                select(func.count()).where(
                    Holding.filing_id == latest.id,
                    Holding.is_sold == False,
                )
            ) or 0

        results.append({
            **inv,
            "latest_period": latest.period_of_report if latest else None,
            "latest_filed": latest.filed_at if latest else None,
            "total_value_k": latest.total_value if latest else 0,
            "total_value_m": round((latest.total_value or 0) / 1000, 1),
            "holdings_count": holdings_count,
        })
    return results


@router.get("/{investor_id}")
async def get_investor(investor_id: str, db: AsyncSession = Depends(get_db)):
    inv = INVESTOR_MAP.get(investor_id)
    if not inv:
        from fastapi import HTTPException
        raise HTTPException(404, "investor not found")

    filings = await db.scalars(
        select(Filing)
        .where(Filing.investor_id == investor_id)
        .order_by(Filing.period_of_report.desc())
    )
    filing_list = []
    for f in filings.all():
        cnt = await db.scalar(
            select(func.count()).where(Holding.filing_id == f.id)
        ) or 0
        filing_list.append({
            "id": f.id,
            "period_of_report": f.period_of_report,
            "filed_at": f.filed_at,
            "total_value_k": f.total_value,
            "total_value_m": round(f.total_value / 1000, 1),
            "holdings_count": cnt,
        })

    return {**inv, "filings": filing_list}


@router.get("/{investor_id}/holdings")
async def get_investor_holdings(
    investor_id: str,
    period: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """투자자의 보유 종목 반환. period 미지정 시 최신 분기."""
    query = select(Filing).where(Filing.investor_id == investor_id)
    if period:
        query = query.where(Filing.period_of_report == period)
    else:
        query = query.order_by(Filing.period_of_report.desc()).limit(1)

    filing = await db.scalar(query)
    if not filing:
        return {"period": None, "holdings": []}

    holdings = await db.scalars(
        select(Holding)
        .where(Holding.filing_id == filing.id)
        .order_by(Holding.value.desc())
    )

    total_value = filing.total_value or 1
    holdings_list = []
    for h in holdings.all():
        weight = h.value / total_value * 100
        holdings_list.append({
            "id": h.id,
            "ticker": h.ticker,
            "cusip": h.cusip,
            "company_name": h.company_name,
            "shares": h.shares,
            "value_k": h.value,
            "value_m": round(h.value / 1000, 2),
            "weight_pct": round(weight, 2),
            "shares_change": h.shares_change,
            "value_change_k": h.value_change,
            "is_new": h.is_new,
            "is_sold": h.is_sold,
            "current_price": h.current_price,
        })

    return {
        "investor": INVESTOR_MAP.get(investor_id),
        "period": filing.period_of_report,
        "filed_at": filing.filed_at,
        "total_value_k": filing.total_value,
        "total_value_b": round(filing.total_value / 1_000_000, 2),
        "holdings": holdings_list,
    }
