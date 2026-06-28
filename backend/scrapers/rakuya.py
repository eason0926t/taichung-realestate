# backend/scrapers/rakuya.py
import re
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper, ScrapeResult

RAKUYA_URL = "https://www.rakuya.com.tw/sell/result?city=13"  # 台中市=13

class ScraperRakuya(BaseScraper):
    platform = "rakuya"

    async def scrape(self) -> list[ScrapeResult]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-TW,zh;q=0.9",
        }
        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            resp = await client.get(RAKUYA_URL)
            resp.raise_for_status()
        return self._parse_html(resp.text)

    def _parse_html(self, html: str) -> list[ScrapeResult]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.select(".house-item, .item-info, [class*='house-card']"):
            try:
                price_el = item.select_one("[class*='price'], .house-price")
                if not price_el:
                    continue
                price_text = re.sub(r"[^\d]", "", price_el.get_text())
                if not price_text:
                    continue
                price_wan = int(price_text)

                title_el = item.select_one("[class*='title'], h3, h2")
                title = title_el.get_text(strip=True) if title_el else ""

                link_el = item.select_one("a[href*='/sell/']")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                id_match = re.search(r"/sell/(\w+)", href)
                if not id_match:
                    continue
                source_id = id_match.group(1)
                url = f"https://www.rakuya.com.tw{href}" if href.startswith("/") else href

                area_el = item.select_one("[class*='area'], [class*='size']")
                area_text = area_el.get_text(strip=True) if area_el else ""
                area_match = re.search(r"([\d.]+)\s*坪", area_text)
                area_ping = float(area_match.group(1)) if area_match else None

                photo_el = item.select_one("img")
                photos = [photo_el["src"]] if photo_el and photo_el.get("src") else []

                results.append(ScrapeResult(
                    source="rakuya",
                    source_id=source_id,
                    url=url,
                    title=title,
                    price=price_wan * 10000,
                    area_ping=area_ping,
                    photos=photos,
                ))
            except Exception:
                continue
        return results
