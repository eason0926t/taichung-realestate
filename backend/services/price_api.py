"""
內政部不動產成交案件實際資訊資料供應系統
https://plvr.land.moj.gov.tw/DownloadOpenData
CKAN API: https://data.gov.tw/dataset/81296
"""
import inspect
import httpx
from datetime import date, timedelta

CKAN_API = (
    "https://data.gov.tw/api/3/action/datastore_search"
    "?resource_id=b6af6b62-4ee6-4be0-b9f5-96ad8dbdc024"
)

SQM_TO_PING = 0.3025   # 1 平方公尺 = 0.3025 坪


def _roc_to_date(roc_str: str) -> date | None:
    """民國年月日 (1130315) → Python date"""
    try:
        year = int(roc_str[:3]) + 1911
        month = int(roc_str[3:5])
        day = int(roc_str[5:7])
        return date(year, month, day)
    except Exception:
        return None


async def _json(resp) -> dict:
    """Handle both sync (real httpx) and async (mocked) .json() calls."""
    result = resp.json()
    if inspect.isawaitable(result):
        return await result
    return result


class TaichungPriceAPI:
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=30)

    async def fetch_recent(self, months: int = 3) -> list[dict]:
        records = []
        offset = 0
        limit = 1000

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                resp = await client.get(
                    CKAN_API,
                    params={
                        "filters": '{"縣市":"台中市","交易標的":"房地(土地+建物)"}',
                        "limit": limit,
                        "offset": offset,
                    }
                )
                data = await _json(resp)
                rows = data.get("result", {}).get("records", [])
                if not rows:
                    break

                for row in rows:
                    txn_date = _roc_to_date(row.get("交易年月日", ""))
                    try:
                        area_sqm = float(row.get("建物移轉總面積平方公尺", 0))
                        area_ping = round(area_sqm * SQM_TO_PING, 2)
                        price = int(row.get("總價元", 0))
                        unit_sqm = float(row.get("單價元平方公尺", 0))
                        unit_ping = int(unit_sqm / SQM_TO_PING / 10000) if unit_sqm else None

                        records.append({
                            "district": row.get("鄉鎮市區", ""),
                            "address": row.get("土地位置建物門牌", ""),
                            "price": price,
                            "unit_price": unit_ping,
                            "area_ping": area_ping,
                            "building_type": row.get("建物型態", ""),
                            "transaction_date": txn_date,
                        })
                    except (ValueError, TypeError):
                        continue

                if len(rows) < limit:
                    break
                offset += limit

        return records
