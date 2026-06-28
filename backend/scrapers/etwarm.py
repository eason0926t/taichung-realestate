# backend/scrapers/etwarm.py
import re
import json
import asyncio
from playwright.async_api import async_playwright, Response
from backend.scrapers.base import BaseScraper, ScrapeResult

LIST_URL = "https://www.etwarm.com.tw/Buy/List/?city=407"  # 台中市
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


class ScraperEtwarm(BaseScraper):
    platform = "etwarm"

    async def scrape(self) -> list[ScrapeResult]:
        captured: list[dict] = []

        async def handle_response(resp: Response):
            if "buy-list-json" in resp.url or ("houses" in resp.url and "json" in resp.url):
                try:
                    body = await resp.json()
                    items = body.get("data", [])
                    if isinstance(items, list):
                        captured.extend(items)
                except Exception:
                    pass

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page.on("response", handle_response)
            await page.goto(LIST_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            # scroll to trigger more loads
            for _ in range(3):
                await page.keyboard.press("End")
                await page.wait_for_timeout(1500)
            await browser.close()

        if captured:
            return self._parse_items(captured)

        # Fallback: parse HTML if no JSON was intercepted
        return []

    def _parse_items(self, items: list[dict]) -> list[ScrapeResult]:
        results = []
        for item in items:
            try:
                raw_id = str(item.get("編號") or item.get("id") or "")
                if not raw_id:
                    continue
                price_wan = item.get("刊登售價(萬)") or item.get("price") or 0
                address_parts = [
                    item.get("縣市", ""),
                    item.get("鄉鎮市區", ""),
                    item.get("地址", ""),
                ]
                address = "".join(p for p in address_parts if p)
                area = item.get("建物坪數") or item.get("area")
                area_match = re.search(r"([\d.]+)", str(area)) if area else None
                area_ping = float(area_match.group(1)) if area_match else None

                photos_raw = (item.get("多媒體") or {}).get("照片") or []
                photos = [p for p in photos_raw if isinstance(p, str)]

                detail_path = item.get("物件詳細頁", "")
                url = (
                    f"https://www.etwarm.com.tw{detail_path}"
                    if detail_path.startswith("/")
                    else detail_path or f"https://www.etwarm.com.tw/Buy/Detail/{raw_id}"
                )

                age_raw = item.get("屋齡", "")
                age_match = re.search(r"(\d+)", str(age_raw)) if age_raw else None
                building_age = int(age_match.group(1)) if age_match else None

                results.append(ScrapeResult(
                    source="etwarm",
                    source_id=raw_id,
                    url=url,
                    price=int(float(price_wan) * 10000) if price_wan else None,
                    area_ping=area_ping,
                    building_age=building_age,
                    district=_extract_district(address),
                    address=address,
                    photos=photos,
                ))
            except Exception:
                continue
        return results
