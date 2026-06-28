# backend/scrapers/etwarm.py
import re
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper, ScrapeResult
from backend.scrapers.site_591 import Scraper591

ETWARM_URL = "https://www.etwarm.com.tw/Buy/List/?city=407"  # 台中市

class ScraperEtwarm(BaseScraper):
    platform = "etwarm"

    async def scrape(self) -> list[ScrapeResult]:
        headers = {"User-Agent": "Mozilla/5.0 Chrome/124.0.0.0"}
        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            resp = await client.get(ETWARM_URL)
            resp.raise_for_status()
        return self._parse_html(resp.text)

    def _parse_html(self, html: str) -> list[ScrapeResult]:
        soup = BeautifulSoup(html, "html.parser")
        extractor = Scraper591.__new__(Scraper591)
        results = []
        for item in soup.select("[class*='item'], [class*='property']"):
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
                source_id = re.search(r"(\d{5,})", href)
                if not source_id:
                    continue
                url = f"https://www.etwarm.com.tw{href}" if href.startswith("/") else href
                loc_el = item.select_one("[class*='addr'], [class*='location']")
                location = loc_el.get_text(strip=True) if loc_el else ""
                area_el = item.select_one("[class*='area']")
                area_text = area_el.get_text(strip=True) if area_el else ""
                area_match = re.search(r"([\d.]+)\s*坪", area_text)
                area_ping = float(area_match.group(1)) if area_match else None
                photo_el = item.select_one("img[src]")
                photos = [photo_el["src"]] if photo_el else []
                results.append(ScrapeResult(
                    source="etwarm",
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
