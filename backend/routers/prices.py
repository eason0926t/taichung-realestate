from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from backend.database import get_db
from backend.models import PriceRecord

router = APIRouter()

@router.get("/prices")
async def get_prices(
    bbox: str = Query(...),
    months: int = Query(6, ge=1, le=24),
    limit: int = Query(300, le=1000),
    db: AsyncSession = Depends(get_db),
):
    try:
        west, south, east, north = [float(x) for x in bbox.split(",")]
    except (ValueError, AttributeError):
        raise HTTPException(422, "bbox 格式錯誤")

    cutoff = date.today() - timedelta(days=months * 30)

    stmt = (
        select(PriceRecord)
        .where(
            PriceRecord.lat.isnot(None),
            PriceRecord.lng.isnot(None),
            PriceRecord.lat.between(south, north),
            PriceRecord.lng.between(west, east),
            PriceRecord.transaction_date >= cutoff,
        )
        .order_by(PriceRecord.transaction_date.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(r.lng), float(r.lat)]
                },
                "properties": {
                    "id": r.id,
                    "district": r.district,
                    "price": r.price,
                    "unit_price": r.unit_price,
                    "area_ping": float(r.area_ping) if r.area_ping else None,
                    "building_type": r.building_type,
                    "transaction_date": str(r.transaction_date),
                }
            }
            for r in rows
        ]
    }
