# backend/services/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from backend.database import AsyncSessionLocal
from backend.models import ScraperStatus

logger = logging.getLogger(__name__)

PLATFORM_URLS = {
    "591":       "https://sale.591.com.tw/?type=1&regionid=8",
    "sinyi":     "https://www.sinyi.com.tw/buy/list/Taichung-city/",
    "yungching": "https://buy.yungching.com.tw/list/%E5%8F%B0%E4%B8%AD%E5%B8%82-_c/",
    "rakuya":    "https://www.rakuya.com.tw/sell/result?city=13",
    "etwarm":    "https://www.etwarm.com.tw/Buy/List/?city=407",
}

SCRAPER_MAP = {
    "591":       "backend.scrapers.site_591.Scraper591",
    "sinyi":     "backend.scrapers.sinyi.ScraperSinyi",
    "yungching": "backend.scrapers.yungching.ScraperYungching",
    "rakuya":    "backend.scrapers.rakuya.ScraperRakuya",
    "etwarm":    "backend.scrapers.etwarm.ScraperEtwarm",
}


def _load_class(dotpath: str):
    module_path, cls_name = dotpath.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, cls_name)


async def run_all_scrapers():
    """Runs all platform scrapers every 2 hours."""
    logger.info("排程爬蟲啟動")
    async with AsyncSessionLocal() as db:
        for platform, cls_path in SCRAPER_MAP.items():
            try:
                cls = _load_class(cls_path)
                scraper = cls(db)
                count = await scraper.run()
                logger.info(f"[{platform}] 完成，寫入 {count} 筆")
            except Exception as e:
                logger.error(f"[{platform}] 排程失敗: {e}")


async def run_health_check():
    """Checks scraper health every 30 minutes; triggers recovery for broken ones."""
    from backend.scrapers.recovery import attempt_recovery
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScraperStatus).where(ScraperStatus.status == "broken")
        )
        broken = result.scalars().all()
        for row in broken:
            url = PLATFORM_URLS.get(row.platform, "")
            if url:
                logger.info(f"[{row.platform}] 觸發自動修復...")
                success = await attempt_recovery(row.platform, url, db)
                logger.info(f"[{row.platform}] 修復結果: {success}")


async def sync_price_records():
    """Syncs 實價登錄 data daily at 06:00."""
    from backend.services.price_api import TaichungPriceAPI
    from backend.models import PriceRecord
    from sqlalchemy import delete
    from datetime import date, timedelta

    logger.info("實價登錄同步啟動")
    api = TaichungPriceAPI()
    records = await api.fetch_recent(months=3)
    if not records:
        logger.info("實價登錄同步：無資料")
        return

    cutoff = date.today() - timedelta(days=90)
    async with AsyncSessionLocal() as db:
        # Delete the window we're about to re-populate to avoid duplicates
        await db.execute(
            delete(PriceRecord).where(PriceRecord.transaction_date >= cutoff)
        )
        for r in records:
            if not r.get("transaction_date"):
                continue
            db.add(PriceRecord(**r))
        await db.commit()
    logger.info(f"實價登錄同步完成，{len(records)} 筆")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_all_scrapers,  IntervalTrigger(hours=2),    id="scrapers")
    scheduler.add_job(run_health_check,  IntervalTrigger(minutes=30), id="health_check")
    scheduler.add_job(sync_price_records, CronTrigger(hour=6, minute=0), id="price_sync")
    return scheduler
