import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.models import Listing, ScraperStatus

SCREENSHOT_DIR = Path("/tmp/scraper_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

BROKEN_THRESHOLD = 5   # consecutive failures before status becomes "broken"


@dataclass
class ScrapeResult:
    source: str
    source_id: str
    url: str
    title: Optional[str] = None
    price: Optional[int] = None        # 元
    unit_price: Optional[int] = None   # 萬/坪
    area_ping: Optional[float] = None
    rooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    building_age: Optional[int] = None
    district: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    photos: list[str] = field(default_factory=list)


class BaseScraper(ABC):
    platform: str = ""

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def scrape(self) -> list[ScrapeResult]:
        """抓取物件，回傳 ScrapeResult 列表"""

    async def run(self) -> int:
        """執行爬蟲，更新 scraper_status，回傳成功寫入筆數"""
        now = datetime.now(timezone.utc)
        try:
            results = await self.scrape()
            await self._upsert_listings(results)
            await self._record_success(now)
            return len(results)
        except Exception as e:
            screenshot = await self._take_screenshot()
            await self._record_failure(str(e), screenshot, now)
            return 0

    async def _upsert_listings(self, results: list[ScrapeResult]):
        from sqlalchemy.dialects.postgresql import insert
        for r in results:
            stmt = insert(Listing).values(
                source=r.source, source_id=r.source_id, url=r.url,
                title=r.title, price=r.price, unit_price=r.unit_price,
                area_ping=r.area_ping, rooms=r.rooms, floor=r.floor,
                total_floors=r.total_floors, building_age=r.building_age,
                district=r.district, address=r.address,
                lat=r.lat, lng=r.lng, photos=r.photos, is_active=True,
            ).on_conflict_do_update(
                index_elements=["source", "source_id"],
                set_=dict(
                    title=r.title, price=r.price, unit_price=r.unit_price,
                    is_active=True, updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.execute(stmt)
        await self.db.commit()

    async def _record_success(self, now: datetime):
        await self.db.execute(
            update(ScraperStatus)
            .where(ScraperStatus.platform == self.platform)
            .values(status="ok", last_success=now, failure_count=0, error_log=None)
        )
        await self.db.commit()

    async def _record_failure(self, error: str, screenshot: str, now: datetime):
        result = await self.db.execute(
            select(ScraperStatus).where(ScraperStatus.platform == self.platform)
        )
        row = result.scalar_one_or_none()
        count = (row.failure_count if row else 0) + 1
        status = "broken" if count >= BROKEN_THRESHOLD else "failing"
        await self.db.execute(
            update(ScraperStatus)
            .where(ScraperStatus.platform == self.platform)
            .values(
                status=status, last_failure=now,
                failure_count=count, error_log=error[:2000],
                screenshot_path=screenshot,
            )
        )
        await self.db.commit()

    async def _take_screenshot(self) -> str:
        """嘗試用 Playwright 截圖（若 playwright 未啟動回傳空字串）"""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                path = str(SCREENSHOT_DIR / f"{self.platform}_{int(time.time())}.png")
                await page.screenshot(path=path)
                await browser.close()
                return path
        except Exception:
            return ""
