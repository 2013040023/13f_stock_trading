import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    sync_task = asyncio.create_task(_auto_sync())
    from app.services.telegram_service import start_bot, stop_bot
    await start_bot()
    yield
    sync_task.cancel()
    await stop_bot()


async def _auto_sync():
    """시작 시 한 번 동기화 후 24시간마다 반복."""
    from app.services.sync_service import sync_all
    import logging
    log = logging.getLogger("13f.auto_sync")
    await asyncio.sleep(3)  # 앱 초기화 대기
    while True:
        try:
            log.info("[auto_sync] starting scheduled sync...")
            await sync_all()
            log.info("[auto_sync] done")
        except Exception as e:
            log.error(f"[auto_sync] failed: {e}")
        await asyncio.sleep(86400)  # 24시간


app = FastAPI(title="13F Stock Tracker", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import investors, analysis, sync  # noqa: E402

app.include_router(investors.router, prefix="/api/investors", tags=["investors"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
