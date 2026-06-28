# backend/scrapers/site_591.py
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from backend.scrapers.base import BaseScraper, ScrapeResult

TAICHUNG_URL = (
    "https://sale.591.com.tw/?type=1&regionid=8"  # regionid=8 = 台中市
)


class Scraper591(BaseScraper):
    platform = "591"

    async def scrape(self) -> list[ScrapeResult]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            await page.goto(TAICHUNG_URL, wait_until="networkidle", timeout=30000)
            # 捲動觸發懶加載
            for _ in range(3):
                await page.keyboard.press("End")
                await page.wait_for_timeout(1000)
            html = await page.content()
            await browser.close()
        return self._parse_html(html)

    def _parse_html(self, html: str) -> list[ScrapeResult]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.select("li.item, div.item-container"):
            try:
                price_text = (item.select_one(".price-main") or item.select_one("[class*='price']"))
                if not price_text:
                    continue
                price_num = re.sub(r"[^\d]", "", price_text.get_text())
                if not price_num:
                    continue
                price_wan = int(price_num)  # 591 顯示「萬」為單位

                title_el = item.select_one(".item-title, [class*='title']")
                title = title_el.get_text(strip=True) if title_el else ""

                area_el = item.select_one(".item-area, [class*='area']")
                area_text = area_el.get_text(strip=True) if area_el else ""
                area_match = re.search(r"([\d.]+)\s*坪", area_text)
                area_ping = float(area_match.group(1)) if area_match else None

                loc_el = item.select_one(".location, [class*='location'], [class*='address']")
                location = loc_el.get_text(strip=True) if loc_el else ""
                district = self._extract_district(location)

                link_el = item.select_one("a[href*='sale-detail'], a.link")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                source_id = re.search(r"(\d+)", href)
                if not source_id:
                    continue
                source_id = source_id.group(1)
                url = f"https://sale.591.com.tw{href}" if href.startswith("/") else href

                photo_el = item.select_one("img[src*='591']")
                photos = [photo_el["src"]] if photo_el else []

                unit_price = int(price_wan * 10000 / area_ping) // 10000 if area_ping else None

                results.append(ScrapeResult(
                    source="591",
                    source_id=source_id,
                    url=url,
                    title=title,
                    price=price_wan * 10000,
                    unit_price=unit_price,
                    area_ping=area_ping,
                    district=district,
                    address=location,
                    photos=photos,
                ))
            except Exception:
                continue
        return results

    def _extract_district(self, text: str) -> str:
        districts = ["中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區",
                     "豐原區", "大里區", "太平區", "清水區", "沙鹿區", "梧棲區", "烏日區",
                     "神岡區", "大雅區", "潭子區", "大甲區", "后里區", "東勢區", "石岡區",
                     "新社區", "和平區", "龍井區", "大肚區", "霧峰區"]
        for d in districts:
            if d in text:
                return d
        return ""
