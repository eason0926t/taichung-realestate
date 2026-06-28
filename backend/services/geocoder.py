# backend/services/geocoder.py
import asyncio
import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.models import Listing

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
BATCH = 10   # listings per geocoding run
DELAY = 1.2  # seconds between requests (Nominatim rate limit: 1 req/s)

# Approximate centroids for each Taichung district (fallback when address is too vague)
DISTRICT_CENTROIDS: dict[str, tuple[float, float]] = {
    "中區": (24.1389, 120.6839), "東區": (24.1393, 120.7031),
    "南區": (24.1213, 120.6838), "西區": (24.1481, 120.6632),
    "北區": (24.1594, 120.6858), "西屯區": (24.1670, 120.6219),
    "南屯區": (24.1202, 120.6434), "北屯區": (24.1850, 120.7048),
    "豐原區": (24.2534, 120.7186), "大里區": (24.1014, 120.6777),
    "太平區": (24.1248, 120.7271), "清水區": (24.2660, 120.5603),
    "沙鹿區": (24.2335, 120.5775), "梧棲區": (24.2567, 120.5330),
    "烏日區": (24.0883, 120.6482), "神岡區": (24.2541, 120.6620),
    "大雅區": (24.2204, 120.6466), "潭子區": (24.2121, 120.7169),
    "大甲區": (24.3484, 120.6211), "后里區": (24.3088, 120.6990),
    "東勢區": (24.2570, 120.8213), "石岡區": (24.2716, 120.7798),
    "新社區": (24.2256, 120.8004), "和平區": (24.3631, 121.0728),
    "龍井區": (24.1777, 120.5497), "大肚區": (24.1527, 120.5390),
    "霧峰區": (24.0591, 120.7214),
}


async def geocode_address(client: httpx.AsyncClient, address: str) -> tuple[float, float] | None:
    """Return (lat, lng) or None."""
    if not address:
        return None
    query = address if "台中" in address else f"台中市 {address}"
    try:
        resp = await client.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "tw"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.debug(f"geocode failed for '{address}': {e}")
    return None


async def geocode_missing(db: AsyncSession, limit: int = BATCH) -> int:
    """Geocode listings that are missing lat/lng. Returns count updated."""
    result = await db.execute(
        select(Listing)
        .where(Listing.lat.is_(None), Listing.address.isnot(None))
        .limit(limit)
    )
    rows = result.scalars().all()
    if not rows:
        return 0

    updated = 0
    async with httpx.AsyncClient(headers=HEADERS) as client:
        for row in rows:
            coords = await geocode_address(client, row.address or "")
            if not coords and row.district and row.district in DISTRICT_CENTROIDS:
                # Fallback: district centroid with small random offset to avoid stacking
                import random
                clat, clng = DISTRICT_CENTROIDS[row.district]
                coords = (clat + random.uniform(-0.003, 0.003), clng + random.uniform(-0.003, 0.003))
            if coords:
                lat, lng = coords
                await db.execute(
                    update(Listing)
                    .where(Listing.id == row.id)
                    .values(lat=lat, lng=lng)
                )
                updated += 1
            await asyncio.sleep(DELAY)

    await db.commit()
    logger.info(f"geocode_missing: {updated}/{len(rows)} 成功")
    return updated
