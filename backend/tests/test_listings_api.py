import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_listings_returns_geojson():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/listings", params={
            "bbox": "120.5,24.0,120.8,24.3"
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data

@pytest.mark.asyncio
async def test_listings_invalid_bbox():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/listings", params={"bbox": "bad"})
    assert resp.status_code == 422
