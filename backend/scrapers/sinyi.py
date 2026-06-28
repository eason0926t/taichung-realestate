# backend/scrapers/sinyi.py
import re
import json
from playwright.async_api import async_playwright, Response
from backend.scrapers.base import BaseScraper, ScrapeResult

LIST_URL = "https://www.sinyi.com.tw/buy/list/Taichung-city/"
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


class ScraperSinyi(BaseScraper):
    platform = "sinyi"

    async def scrape(self) -> list[ScrapeResult]:
        captured: list[dict] = []

        async def handle_response(resp: Response):
            url = resp.url
            # Intercept listing JSON responses
            if any(k in url for k in ["/api/", "/buy/list", "house", "property"]):
                ct = resp.headers.get("content-type", "")
                if "json" in ct:
                    try:
                        body = await resp.json()
                        if isinstance(body, dict):
                            for key in ["data", "items", "list", "result", "records"]:
                                val = body.get(key)
                                if isinstance(val, list) and val:
                                    captured.extend(val)
                                    break
                        elif isinstance(body, list):
                            captured.extend(body)
                    except Exception:
                        pass

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page.on("response", handle_response)
            try:
                await page.goto(LIST_URL, wait_until="networkidle", timeout=30000)
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
                # Try various field name patterns for source ID
                raw_id = str(
                    item.get("caseId") or item.get("id") or
                    item.get("houseId") or item.get("propertyId") or ""
                )
                if not raw_id or raw_id in seen:
                    continue
                seen.add(raw_id)

                price_wan = (
                    item.get("price") or item.get("totalPrice") or
                    item.get("salePrice") or 0
                )
                address = (
                    item.get("address") or item.get("location") or
                    item.get("addr") or ""
                )
                title = item.get("name") or item.get("title") or item.get("caseName") or ""
                area = item.get("area") or item.get("buildingArea") or item.get("ping")
                area_match = re.search(r"([\d.]+)", str(area)) if area else None
                area_ping = float(area_match.group(1)) if area_match else None

                url_path = item.get("url") or item.get("link") or f"/buy/{raw_id}"
                url = (
                    f"https://www.sinyi.com.tw{url_path}"
                    if url_path.startswith("/")
                    else url_path
                )

                photos = []
                img = item.get("image") or item.get("photo") or item.get("img") or item.get("cover")
                if isinstance(img, list):
                    photos = [i for i in img if isinstance(i, str)]
                elif isinstance(img, str) and img:
                    photos = [img]

                results.append(ScrapeResult(
                    source="sinyi",
                    source_id=raw_id,
                    url=url,
                    title=title,
                    price=int(float(price_wan) * 10000) if price_wan else None,
                    area_ping=area_ping,
                    district=_extract_district(address),
                    address=address,
                    photos=photos,
                ))
            except Exception:
                continue
        return results
