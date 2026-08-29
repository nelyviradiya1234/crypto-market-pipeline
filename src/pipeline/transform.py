"""Transformation module to normalize raw API responses into internal data models."""

from datetime import datetime, timezone
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def transform_records(
    validated_data: List[Dict[str, Any]],
    data_source: str = "coingecko",
    timestamp: datetime = None
) -> List[Dict[str, Any]]:
    """Transform validated CoinGecko market records into internal table snapshot models.

    Args:
        validated_data: List of validated CoinGecko market dicts.
        data_source: Identifier for data origin ('coingecko' or 'synthetic').
        timestamp: Optional specific timestamp to set for `pulled_at`. Defaults to UTC now.

    Returns:
        List of dictionaries formatted for database insertion.
    """
    pulled_at = timestamp if timestamp is not None else datetime.now(timezone.utc)
    transformed_batch = []

    for item in validated_data:
        record = {
            "coin_id": item["id"],
            "symbol": item["symbol"].upper(),
            "price_usd": float(item["current_price"]),
            "market_cap_usd": float(item["market_cap"]) if item.get("market_cap") is not None else None,
            "volume_24h_usd": float(item["total_volume"]) if item.get("total_volume") is not None else None,
            "change_24h_pct": float(item["price_change_percentage_24h"]) if item.get("price_change_percentage_24h") is not None else None,
            "pulled_at": pulled_at,
            "data_source": data_source
        }
        transformed_batch.append(record)

    logger.info(f"Transformed {len(transformed_batch)} records at UTC {pulled_at.strftime('%Y-%m-%d %H:%M:%S')}")
    return transformed_batch
