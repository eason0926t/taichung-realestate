from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models import ScraperStatus

router = APIRouter()

async def _run_scraper(platform: str, db: AsyncSession):
    from backend.scrapers.site_591 import Scraper591
    scrapers = {"591": Scraper591}
    cls = scrapers.get(platform)
    if cls:
        await cls(db).run()

@router.post("/scraper/trigger")
async def trigger_scraper(
    platform: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    background_tasks.add_task(_run_scraper, platform, db)
    return {"status": "triggered", "platform": platform}

@router.get("/scraper/status")
async def scraper_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScraperStatus))
    rows = result.scalars().all()
    return [
        {
            "platform": r.platform,
            "status": r.status,
            "last_success": str(r.last_success) if r.last_success else None,
            "failure_count": r.failure_count,
        }
        for r in rows
    ]
