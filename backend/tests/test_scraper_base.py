import pytest
from backend.scrapers.base import BaseScraper, ScrapeResult


def test_scrape_result_valid():
    r = ScrapeResult(
        source="591",
        source_id="abc123",
        url="https://591.com.tw/sale-detail-abc123.html",
        title="北區 2房 42坪",
        price=15800000,
        unit_price=38,
        area_ping=42.0,
        rooms=2,
        floor=3,
        total_floors=12,
        district="北區",
        address="台中市北區民族路三段123號",
        photos=["https://img.591.com.tw/a.jpg"],
    )
    assert r.price == 15800000
    assert r.source == "591"


@pytest.mark.asyncio
async def test_base_scraper_records_failure(db_session):
    class FailingScraper(BaseScraper):
        platform = "591"

        async def scrape(self):
            raise ValueError("selector not found")

    scraper = FailingScraper(db_session)
    await scraper.run()

    from sqlalchemy import select
    from backend.models import ScraperStatus

    result = await db_session.execute(
        select(ScraperStatus).where(ScraperStatus.platform == "591")
    )
    status = result.scalar_one_or_none()
    assert status is not None
    assert status.failure_count >= 1
    assert status.status in ("failing", "broken")
