from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models import Listing

router = APIRouter()


def _listing_to_feature(row: Listing) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(row.lng), float(row.lat)]
        } if row.lat and row.lng else None,
        "properties": {
            "id": row.id,
            "source": row.source,
            "url": row.url,
            "title": row.title,
            "price": row.price,
            "unit_price": row.unit_price,
            "area_ping": float(row.area_ping) if row.area_ping else None,
            "rooms": row.rooms,
            "floor": row.floor,
            "district": row.district,
            "photo": row.photos[0] if row.photos else None,
        }
    }


@router.get("/listings")
async def get_listings(
    bbox: str = Query(..., description="west,south,east,north"),
    min_price: int | None = None,
    max_price: int | None = None,
    rooms: int | None = None,
    source: str | None = None,
    limit: int = Query(200, le=500),
    db: AsyncSession = Depends(get_db),
):
    try:
        west, south, east, north = [float(x) for x in bbox.split(",")]
    except (ValueError, AttributeError):
        raise HTTPException(422, "bbox 格式錯誤：west,south,east,north")

    stmt = select(Listing).where(
        Listing.is_active == True,
        Listing.lat.isnot(None),
        Listing.lng.isnot(None),
        Listing.lat.between(south, north),
        Listing.lng.between(west, east),
    )
    if min_price:
        stmt = stmt.where(Listing.price >= min_price * 10000)
    if max_price:
        stmt = stmt.where(Listing.price <= max_price * 10000)
    if rooms:
        stmt = stmt.where(Listing.rooms == rooms)
    if source:
        stmt = stmt.where(Listing.source.in_(source.split(",")))

    stmt = stmt.order_by(Listing.scraped_at.desc()).limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {
        "type": "FeatureCollection",
        "features": [_listing_to_feature(r) for r in rows]
    }


@router.get("/listings/{listing_id}")
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "物件不存在")
    return _listing_to_feature(row)
