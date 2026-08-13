"""SEC EDGAR 13F 공시 수집기."""
from __future__ import annotations

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import httpx

from app.config import EDGAR_BASE, EDGAR_ARCHIVE, EDGAR_HEADERS

logger = logging.getLogger("13f.edgar")

_NS = {
    "": "http://www.sec.gov/edgar/document/thirteenf/informationtable",
    "n1": "http://www.sec.gov/edgar/document/thirteenf/informationtable",
    "n2": "http://www.sec.gov/edgar/thirteenf/informationtable",
}


def _strip_ns(tag: str) -> str:
    return re.sub(r"\{[^}]+\}", "", tag)


async def get_recent_13f_filings(cik: str, limit: int = 8) -> list[dict]:
    """최근 13F-HR 공시 목록 반환."""
    cik_padded = cik.lstrip("0").zfill(10)
    url = f"{EDGAR_BASE}/submissions/CIK{cik_padded}.json"

    async with httpx.AsyncClient(timeout=20, headers=EDGAR_HEADERS) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accessions = filings.get("accessionNumber", [])
    periods = filings.get("reportDate", [])

    results = []
    for i, form in enumerate(forms):
        if form in ("13F-HR", "13F-HR/A") and len(results) < limit:
            results.append({
                "form": form,
                "filed_at": dates[i] if i < len(dates) else "",
                "period_of_report": periods[i] if i < len(periods) else "",
                "accession_number": accessions[i] if i < len(accessions) else "",
            })

    return results


async def get_13f_holdings(cik: str, accession: str) -> list[dict]:
    """특정 13F 공시에서 보유 종목 파싱."""
    cik_num = cik.lstrip("0")
    acc_clean = accession.replace("-", "")
    index_url = f"{EDGAR_ARCHIVE}/{cik_num}/{acc_clean}/{accession}-index.htm"

    async with httpx.AsyncClient(timeout=30, headers=EDGAR_HEADERS, follow_redirects=True) as client:
        # 인덱스에서 XML 파일명 찾기
        try:
            idx_resp = await client.get(index_url)
            xml_filename = _find_infotable_filename(idx_resp.text, accession)
        except Exception:
            xml_filename = None

        if not xml_filename:
            xml_filename = await _guess_xml_filename(client, cik_num, acc_clean, accession)

        if not xml_filename:
            logger.warning(f"[edgar] XML not found: {cik} {accession}")
            return []

        xml_url = f"{EDGAR_ARCHIVE}/{cik_num}/{acc_clean}/{xml_filename}"
        xml_resp = await client.get(xml_url)
        xml_resp.raise_for_status()

    return _parse_infotable(xml_resp.text)


def _find_infotable_filename(html: str, accession: str) -> Optional[str]:
    """인덱스 HTML에서 informationTable XML 파일명 찾기."""
    patterns = [
        r'href="([^"]*(?:infotable|information[_-]?table|13f)[^"]*\.xml)"',
        r'href="([^"]*\.xml)"',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            fname = m.group(1)
            if "/" in fname:
                fname = fname.split("/")[-1]
            return fname
    return None


async def _guess_xml_filename(client: httpx.AsyncClient, cik: str, acc_clean: str, accession: str) -> Optional[str]:
    """일반적인 파일명 패턴 시도."""
    candidates = [
        f"{accession}-0002.txt",
        "informationtable.xml",
        "infotable.xml",
        "form13fInfoTable.xml",
        f"{acc_clean}-0002.txt",
    ]
    base = f"{EDGAR_ARCHIVE}/{cik}/{acc_clean}/"
    for name in candidates:
        try:
            r = await client.head(base + name)
            if r.status_code == 200:
                return name
        except Exception:
            continue
    return None


def _parse_infotable(xml_text: str) -> list[dict]:
    """13F XML informationTable 파싱."""
    holdings = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"[edgar] XML parse error: {e}")
        return []

    for entry in root.iter():
        if _strip_ns(entry.tag) not in ("infoTable",):
            continue

        def _txt(tag: str) -> str:
            for child in entry:
                if _strip_ns(child.tag) == tag:
                    return (child.text or "").strip()
            return ""

        def _nested(parent_tag: str, child_tag: str) -> str:
            for child in entry:
                if _strip_ns(child.tag) == parent_tag:
                    for gc in child:
                        if _strip_ns(gc.tag) == child_tag:
                            return (gc.text or "").strip()
            return "0"

        name = _txt("nameOfIssuer")
        cusip = _txt("cusip")
        value_str = _txt("value")
        shares_str = _nested("shrsOrPrnAmt", "sshPrnamt")
        share_type = _nested("shrsOrPrnAmt", "sshPrnamtType")

        if not cusip or not name:
            continue

        try:
            value = float(value_str) if value_str else 0
            shares = int(shares_str) if shares_str else 0
        except ValueError:
            continue

        holdings.append({
            "company_name": name,
            "cusip": cusip,
            "value": value,
            "shares": shares,
            "share_type": share_type or "SH",
        })

    return holdings
