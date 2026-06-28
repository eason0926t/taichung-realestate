# backend/scrapers/yungching.py
import httpx
from backend.scrapers.base import BaseScraper, ScrapeResult

API_URL = "https://buy.yungching.com.tw/api/v2/recommend/listpromote"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://buy.yungching.com.tw/",
}
DISTRICTS = [
    "中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區",
    "豐原區", "大里區", "太平區", "清水區", "沙鹿區", "梧棲區", "烏日區",
    "神岡區", "大雅區", "潭子區", "大甲區", "后里區", "東勢區", "石岡區",
    "新社區", "和平區", "龍井區", "大肚區", "霧峰區",
]


def _extract_district(address: str) -> str:
    for d in DISTRICTS:
        if d in address:
            return d
    return ""


class ScraperYungching(BaseScraper):
    platform = "yungching"

    async def scrape(self) -> list[ScrapeResult]:
        results: list[ScrapeResult] = []
        seen: set[str] = set()
        async with httpx.AsyncClient(headers=HEADERS, timeout=20) as client:
            for page in range(1, 6):  # 5 pages × 20 = up to 100 listings
                resp = await client.get(API_URL, params={"county": "台中市", "count": 20, "page": page})
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data", {}).get("list", [])
                if not items:
                    break
                for item in items:
                    case_id = str(item.get("caseSId", ""))
                    if not case_id or case_id in seen:
                        continue
                    seen.add(case_id)
                    price_wan = item.get("price") or 0
                    address = item.get("address", "")
                    area = (item.get("pinInfo") or {}).get("regArea")
                    cover = item.get("cover", "")
                    if cover.startswith("//"):
                        cover = "https:" + cover
                    # Remove {0}/{1} width/height template tokens
                    cover = cover.replace("{0}", "400").replace("{1}", "300")
                    results.append(ScrapeResult(
                        source="yungching",
                        source_id=case_id,
                        url=f"https://buy.yungching.com.tw/case/{case_id}",
                        title=item.get("caseName"),
                        price=int(price_wan * 10000) if price_wan else None,
                        area_ping=float(area) if area else None,
                        building_age=int(item.get("buildAge") or 0) or None,
                        district=_extract_district(address),
                        address=address,
                        photos=[cover] if cover else [],
                    ))
        return results
