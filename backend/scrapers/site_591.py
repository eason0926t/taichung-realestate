# backend/scrapers/site_591.py
import re
import json
from playwright.async_api import async_playwright, Response
from backend.scrapers.base import BaseScraper, ScrapeResult

TAICHUNG_URL = "https://sale.591.com.tw/?type=1&regionid=8"  # 台中市
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
        captured: list[dict] = []

        async def handle_response(resp: Response):
            url = resp.url
            if "591.com.tw" in url and any(k in url for k in ["sale/list", "house/list", "v1/web"]):
                ct = resp.headers.get("content-type", "")
                if "json" in ct:
                    try:
                        body = await resp.json()
                        if isinstance(body, dict):
                            data = body.get("data", {})
                            if isinstance(data, dict):
                                for key in ["house_list", "items", "list", "data"]:
                                    val = data.get(key)
                                    if isinstance(val, list) and val:
                                        captured.extend(val)
                                        break
                            elif isinstance(data, list):
                                captured.extend(data)
                    except Exception:
                        pass

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page.on("response", handle_response)
            try:
                await page.goto(TAICHUNG_URL, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                for _ in range(3):
                    await page.keyboard.press("End")
                    await page.wait_for_timeout(1000)
            except Exception:
                pass
            finally:
                await browser.close()

        if captured:
            return self._parse_items(captured)
        return []

    def _parse_items(self, items: list[dict]) -> list[ScrapeResult]:
        results = []
        seen: set[str] = set()
        for item in items:
            try:
                raw_id = str(
                    item.get("house_id") or item.get("id") or item.get("houseId") or ""
                )
                if not raw_id or raw_id in seen:
                    continue
                seen.add(raw_id)

                price_wan = item.get("price") or item.get("totalPrice") or 0
                title = item.get("house_title") or item.get("title") or item.get("name") or ""
                location = (
                    item.get("address") or item.get("location") or
                    item.get("section_str") or ""
                )
                area_raw = item.get("area") or item.get("building_area") or item.get("ping") or ""
                area_match = re.search(r"([\d.]+)", str(area_raw))
                area_ping = float(area_match.group(1)) if area_match else None

                url = f"https://sale.591.com.tw/home/house/detail/2/{raw_id}.html"

                photos = []
                cover = item.get("img_url") or item.get("img") or item.get("photo")
                if isinstance(cover, list):
                    photos = [i for i in cover if isinstance(i, str)]
                elif isinstance(cover, str) and cover:
                    photos = [cover]

                unit_price = None
                if area_ping and price_wan:
                    try:
                        unit_price = int(float(price_wan) * 10000 / area_ping) // 10000
                    except Exception:
                        pass

                results.append(ScrapeResult(
                    source="591",
                    source_id=raw_id,
                    url=url,
                    title=title,
                    price=int(float(price_wan) * 10000) if price_wan else None,
                    unit_price=unit_price,
                    area_ping=area_ping,
                    district=_extract_district(location),
                    address=location,
                    photos=photos,
                ))
            except Exception:
                continue
        return results
