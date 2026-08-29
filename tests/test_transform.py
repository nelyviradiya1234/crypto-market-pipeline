"""Unit tests for the data transformation module."""

from datetime import datetime, timezone
from src.pipeline.transform import transform_records

RAW_VALIDATED_RECORDS = [
    {
        "id": "solana",
        "symbol": "sol",
        "current_price": 145.50,
        "market_cap": 67000000000.0,
        "total_volume": 2500000000.0,
        "price_change_percentage_24h": 5.25
    }
]


def test_transform_records_mapping():
    """Test mapping of CoinGecko fields into normalized schema."""
    fixed_time = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
    transformed = transform_records(RAW_VALIDATED_RECORDS, data_source="coingecko", timestamp=fixed_time)

    assert len(transformed) == 1
    record = transformed[0]

    assert record["coin_id"] == "solana"
    assert record["symbol"] == "SOL"
    assert record["price_usd"] == 145.50
    assert record["market_cap_usd"] == 67000000000.0
    assert record["volume_24h_usd"] == 2500000000.0
    assert record["change_24h_pct"] == 5.25
    assert record["pulled_at"] == fixed_time
    assert record["data_source"] == "coingecko"


def test_transform_records_null_handling():
    """Test handling of null optional fields during transformation."""
    records_with_nulls = [
        {
            "id": "cardano",
            "symbol": "ada",
            "current_price": 0.45,
            "market_cap": None,
            "total_volume": None,
            "price_change_percentage_24h": None
        }
    ]
    transformed = transform_records(records_with_nulls)
    record = transformed[0]

    assert record["coin_id"] == "cardano"
    assert record["symbol"] == "ADA"
    assert record["price_usd"] == 0.45
    assert record["market_cap_usd"] is None
    assert record["volume_24h_usd"] is None
    assert record["change_24h_pct"] is None
    assert record["pulled_at"].tzinfo == timezone.utc
