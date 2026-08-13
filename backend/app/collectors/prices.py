"""yfinance로 현재 주가 조회."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger("13f.prices")


# CUSIP → Ticker 변환 (SEC EDGAR 매핑 활용)
_KNOWN_CUSIP: dict[str, str] = {
    "037833100": "AAPL",
    "594918104": "MSFT",
    "02079K305": "GOOGL",
    "023135106": "AMZN",
    "67066G104": "NVDA",
    "30303M102": "META",
    "88160R101": "TSLA",
    "46625H100": "JPM",
    "172967424": "BRK-B",
    "931142103": "WMT",
}


async def resolve_ticker(cusip: str, company_name: str) -> Optional[str]:
    """CUSIP → Ticker 변환. 캐시 → SEC API → yfinance search 순으로 시도."""
    if cusip in _KNOWN_CUSIP:
        return _KNOWN_CUSIP[cusip]

    # SEC EDGAR CUSIP 검색
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://efts.sec.gov/LATEST/search-index?q=%22{cusip}%22&forms=10-K,10-Q&hits.hits.total.value=1"
            r = await client.get(url, headers={"User-Agent": "13f-tracker research@example.com"})
            if r.status_code == 200:
                data = r.json()
                hits = data.get("hits", {}).get("hits", [])
                if hits:
                    ticker = hits[0].get("_source", {}).get("period_of_report")
    except Exception:
        pass

    # yfinance로 회사명 검색
    try:
        ticker = await _search_by_name(company_name)
        if ticker:
            _KNOWN_CUSIP[cusip] = ticker
            return ticker
    except Exception:
        pass

    return None


async def _search_by_name(name: str) -> Optional[str]:
    """회사명으로 ticker 검색."""
    import yfinance as yf
    # 회사명 정리
    clean = name.replace(" INC", "").replace(" CORP", "").replace(" CO", "").replace(" LTD", "").strip()
    try:
        results = await asyncio.to_thread(lambda: yf.Search(clean, max_results=1))
        quotes = results.quotes
        if quotes:
            return quotes[0].get("symbol")
    except Exception:
        pass
    return None


async def get_current_prices(tickers: list[str]) -> dict[str, float]:
    """여러 ticker의 현재가를 한 번에 조회."""
    if not tickers:
        return {}
    import yfinance as yf

    try:
        valid = [t for t in tickers if t]
        if not valid:
            return {}
        data = await asyncio.to_thread(lambda: yf.download(
            " ".join(valid),
            period="1d",
            progress=False,
            auto_adjust=True,
        ))
        if data.empty:
            return {}

        prices: dict[str, float] = {}
        if len(valid) == 1:
            close = data["Close"]
            if not close.empty:
                prices[valid[0]] = float(close.iloc[-1])
        else:
            for t in valid:
                try:
                    col = ("Close", t)
                    if col in data.columns:
                        val = data[col].dropna()
                        if not val.empty:
                            prices[t] = float(val.iloc[-1])
                except Exception:
                    pass
        return prices
    except Exception as e:
        logger.warning(f"[prices] batch fetch failed: {e}")
        return {}
