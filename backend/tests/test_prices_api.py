import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.price_api import TaichungPriceAPI

@pytest.mark.asyncio
async def test_fetch_returns_price_records():
    """測試 API 回傳正確解析的物件"""
    mock_data = {
        "result": {
            "records": [
                {
                    "鄉鎮市區": "北區",
                    "交易標的": "房地(土地+建物)",
                    "土地位置建物門牌": "民族路三段123號",
                    "總價元": "8500000",
                    "單價元平方公尺": "25000",
                    "建物移轉總面積平方公尺": "138.56",
                    "交易年月日": "1150620",  # 2026-06-20, within 3 months
                    "建物型態": "公寓(5樓含以下非電梯)",
                }
            ]
        }
    }
    with patch("backend.services.price_api.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        api = TaichungPriceAPI()
        records = await api.fetch_recent(months=3)

    assert len(records) == 1
    assert records[0]["district"] == "北區"
    assert records[0]["price"] == 8500000
    assert abs(records[0]["area_ping"] - 41.9) < 0.5   # 138.56m² ≈ 41.9坪
