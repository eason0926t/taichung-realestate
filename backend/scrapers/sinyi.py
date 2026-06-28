# backend/scrapers/sinyi.py
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from backend.scrapers.base import BaseScraper, ScrapeResult
from backend.scrapers.site_591 import Scraper591

SINYI_URL = "https://www.sinyi.com.tw/buy/list/Taichung-city/"

class ScraperSinyi(BaseScraper):
    platform = "sinyi"

    async def scrape(self) -> list[ScrapeResult]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
                )
            )
            await page.goto(SINYI_URL, wait_until="networkidle", timeout=30000)
            for _ in range(2):
                await page.keyboard.press("End")
                await page.wait_for_timeout(1500)
            html = await page.content()
            await browser.close()
        return self._parse_html(html)

    def _parse_html(self, html: str) -> list[ScrapeResult]:
        soup = BeautifulSoup(html, "html.parser")
        extractor = Scraper591.__new__(Scraper591)
        results = []
        for item in soup.select("[class*='house-item'], [class*='property-card'], .buy-list-item"):
            try:
                price_el = item.select_one("[class*='price']")
                if not price_el:
                    continue
                price_num = re.sub(r"[^\d]", "", price_el.get_text())
                if not price_num:
                    continue

                link_el = item.select_one("a[href]")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                source_id = re.sub(r"[^a-zA-Z0-9]", "", href)[-20:]
                url = f"https://www.sinyi.com.tw{href}" if href.startswith("/") else href

                loc_el = item.select_one("[class*='location'], [class*='address']")
                location = loc_el.get_text(strip=True) if loc_el else ""

                area_el = item.select_one("[class*='area'], [class*='size']")
                area_text = area_el.get_text(strip=True) if area_el else ""
                area_match = re.search(r"([\d.]+)\s*坪", area_text)
                area_ping = float(area_match.group(1)) if area_match else None

                photo_el = item.select_one("img[src]")
                photos = [photo_el["src"]] if photo_el else []

                results.append(ScrapeResult(
                    source="sinyi",
                    source_id=source_id,
                    url=url,
                    price=int(price_num) * 10000,
                    area_ping=area_ping,
                    district=extractor._extract_district(location),
                    address=location,
                    photos=photos,
                ))
            except Exception:
                continue
        return results
