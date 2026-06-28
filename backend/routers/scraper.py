from fastapi import APIRouter, BackgroundTasks, Query
from sqlalchemy import select
from backend.database import AsyncSessionLocal
from backend.models.scraper_status import ScraperStatus
from backend.scrapers.site_591 import Scraper591
from backend.scrapers.sinyi import ScraperSinyi
from backend.scrapers.yungching import ScraperYungching
from backend.scrapers.rakuya import ScraperRakuya
from backend.scrapers.etwarm import ScraperEtwarm

router = APIRouter()

SCRAPER_MAP = {
    "591": Scraper591,
    "sinyi": ScraperSinyi,
    "yungching": ScraperYungching,
    "rakuya": ScraperRakuya,
    "etwarm": ScraperEtwarm,
}

async def _run_scraper(platform: str) -> None:
    cls = SCRAPER_MAP.get(platform)
    if not cls:
        return
    async with AsyncSessionLocal() as db:
        await cls(db).run()


@router.post("/scraper/trigger")
async def trigger_scraper(
    background_tasks: BackgroundTasks,
    platform: str = Query(...),
):
    if platform not in SCRAPER_MAP:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
    background_tasks.add_task(_run_scraper, platform)
    return {"status": "triggered", "platform": platform}


@router.get("/scraper/status")
async def scraper_status():
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(select(ScraperStatus))).scalars().all()
        return [
            {
                "platform": r.platform,
                "status": r.status,
                "last_success": r.last_success,
                "last_failure": r.last_failure,
                "failure_count": r.failure_count,
                "error_log": r.error_log,
            }
            for r in rows
        ]
