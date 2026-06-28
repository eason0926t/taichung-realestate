# backend/scrapers/site_591.py
import re
import asyncio
from playwright.async_api import async_playwright
from backend.scrapers.base import BaseScraper, ScrapeResult

TAICHUNG_URL = "https://sale.591.com.tw/?type=1&regionid=8"  # 台中市
BFF_API = "https://bff-house.591.com.tw/v1/web/sale/list"
DISTRICTS = [
    "中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區",
    "豐原區", "大里區", "太平區", "清水區", "沙鹿區", "梧棲區", "烏日區",
    "神岡區", "大雅區", "潭子區", "大甲區", "后里區", "東勢區", "石岡區",
    "新社區", "和平區", "龍井區", "大肚區", "霧峰區",
]


def _extract_district(text: str) -> str:
    for d in DISTRICTS:
        if d in text:
            return d
    return ""


class Scraper591(BaseScraper):
    platform = "591"

    async def scrape(self) -> list[ScrapeResult]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # Step 1: Visit site to establish session + get cookies
            try:
                await page.goto(TAICHUNG_URL, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

            # Step 2: Call BFF API with session cookies
            try:
                response = await page.evaluate("""async () => {
                    const r = await fetch('https://bff-house.591.com.tw/v1/web/sale/list?type=1&regionid=8&limit=30', {
                        credentials: 'include',
                        headers: {'deviceid': 'web', 'X-CSRF-TOKEN': document.cookie.match(/(?:^|;)\\s*_591_session=([^;]+)/)?.[1] || ''}
                    });
                    return await r.json();
                }""")
                await browser.close()
                return self._parse_bff(response)
            except Exception:
                pass

            await browser.close()
            return []

    def _parse_bff(self, data: dict) -> list[ScrapeResult]:
        items = []
        if isinstance(data, dict):
            d = data.get("data", {})
            if isinstance(d, dict):
                items = d.get("house_list", d.get("list", []))
            elif isinstance(d, list):
                items = d

        results = []
        seen: set[str] = set()
        for item in items:
            try:
                raw_id = str(item.get("house_id") or item.get("id") or "")
                if not raw_id or raw_id in seen:
                    continue
                seen.add(raw_id)
                price_wan = item.get("price") or 0
                location = item.get("address") or item.get("location") or item.get("section_str") or ""
                title = item.get("house_title") or item.get("title") or ""
                area_raw = item.get("area") or item.get("building_area") or ""
                area_match = re.search(r"([\d.]+)", str(area_raw))
                area_ping = float(area_match.group(1)) if area_match else None
                cover = item.get("img_url") or item.get("img") or ""
                photos = [cover] if cover else []

                results.append(ScrapeResult(
                    source="591",
                    source_id=raw_id,
                    url=f"https://sale.591.com.tw/home/house/detail/2/{raw_id}.html",
                    title=title,
                    price=int(float(price_wan) * 10000) if price_wan else None,
                    area_ping=area_ping,
                    district=_extract_district(location),
                    address=location,
                    photos=photos,
                ))
            except Exception:
                continue
        return results
