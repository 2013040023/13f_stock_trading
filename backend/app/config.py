from typing import ClassVar

INVESTORS = [
    {
        "id": "berkshire",
        "name": "버크셔 해서웨이",
        "manager": "워런 버핏",
        "style": "장기 가치투자",
        "cik": "0001067983",
        "color": "#3b82f6",
    },
    {
        "id": "himalaya",
        "name": "히말라야 캐피털",
        "manager": "릴루 (Li Lu)",
        "style": "집중 가치투자",
        "cik": "0001709323",
        "color": "#8b5cf6",
    },
    {
        "id": "pershing",
        "name": "퍼싱 스퀘어",
        "manager": "빌 애크먼",
        "style": "행동주의 집중투자",
        "cik": "0001336528",
        "color": "#10b981",
    },
    {
        "id": "appaloosa",
        "name": "아팔루사 매니지먼트",
        "manager": "데이비드 테퍼",
        "style": "시클리컬/빅테크",
        "cik": "0001656456",
        "color": "#f59e0b",
    },
    {
        "id": "pabrai",
        "name": "파브라이 인베스트먼트",
        "manager": "모니시 파브라이",
        "style": "고배당/저평가 가치주",
        "cik": "0001173334",
        "color": "#ef4444",
        "exempt_note": "AUM $100M 미만으로 2012년 이후 13F 공시 면제. 공개 인터뷰·컨퍼런스 발언으로만 포트폴리오 파악 가능.",
    },
]

INVESTOR_MAP = {inv["id"]: inv for inv in INVESTORS}
CIK_MAP = {inv["cik"]: inv["id"] for inv in INVESTORS}

EDGAR_BASE = "https://data.sec.gov"
EDGAR_ARCHIVE = "https://www.sec.gov/Archives/edgar/data"
EDGAR_HEADERS = {
    "User-Agent": "13f-tracker research@example.com",
    "Accept-Encoding": "gzip, deflate",
}

DATABASE_URL = "sqlite+aiosqlite:///./data/13f.db"
SYNC_INTERVAL_HOURS = 24
