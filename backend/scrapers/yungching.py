# backend/scrapers/yungching.py
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from backend.scrapers.base import BaseScraper, ScrapeResult
from backend.scrapers.site_591 import Scraper591

YUNGCHING_URL = "https://buy.yungching.com.tw/list/%E5%8F%B0%E4%B8%AD%E5%B8%82-_c/"

class ScraperYungching(BaseScraper):
    platform = "yungching"

    async def scrape(self) -> list[ScrapeResult]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            )
            await page.goto(YUNGCHING_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()
        return self._parse_html(html)

    def _parse_html(self, html: str) -> list[ScrapeResult]:
        soup = BeautifulSoup(html, "html.parser")
        extractor = Scraper591.__new__(Scraper591)
        results = []
        for item in soup.select("[class*='m-list-item'], [class*='house-list']"):
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
                source_id = re.search(r"(\d{6,})", href)
                if not source_id:
                    continue
                url = f"https://buy.yungching.com.tw{href}" if href.startswith("/") else href
                loc_el = item.select_one("[class*='info'], [class*='address']")
                location = loc_el.get_text(strip=True) if loc_el else ""
                area_el = item.select_one("[class*='area']")
                area_text = area_el.get_text(strip=True) if area_el else ""
                area_match = re.search(r"([\d.]+)\s*坪", area_text)
                area_ping = float(area_match.group(1)) if area_match else None
                photo_el = item.select_one("img[src]")
                photos = [photo_el["src"]] if photo_el else []
                results.append(ScrapeResult(
                    source="yungching",
                    source_id=source_id.group(1),
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
