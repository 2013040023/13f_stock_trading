from fastapi import APIRouter, BackgroundTasks
from app.services.sync_service import sync_all, sync_investor, update_prices
from app.config import INVESTOR_MAP

router = APIRouter()

_sync_status: dict = {"running": False, "last_result": None}


@router.post("/all")
async def trigger_sync_all(background_tasks: BackgroundTasks, force: bool = False):
    if _sync_status["running"]:
        return {"status": "already_running"}
    background_tasks.add_task(_run_sync, force=force)
    return {"status": "started"}


@router.post("/{investor_id}")
async def trigger_sync_investor(investor_id: str, background_tasks: BackgroundTasks):
    inv = INVESTOR_MAP.get(investor_id)
    if not inv:
        from fastapi import HTTPException
        raise HTTPException(404, "investor not found")
    background_tasks.add_task(sync_investor, investor_id, inv["cik"])
    return {"status": "started", "investor": investor_id}


@router.post("/prices/update")
async def trigger_price_update(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_prices)
    return {"status": "started"}


@router.get("/status")
async def sync_status():
    return _sync_status


async def _run_sync(force: bool = False):
    _sync_status["running"] = True
    try:
        result = await sync_all(force=force)
        _sync_status["last_result"] = result
    finally:
        _sync_status["running"] = False
