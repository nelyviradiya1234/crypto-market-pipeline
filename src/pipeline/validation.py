"""Validation module for checking CoinGecko API responses against schema rules."""

import logging
from typing import List, Dict, Any, Optional
from src.config import COIN_IDS

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


def validate_response(
    data: Any,
    expected_coin_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Validate that the API response conforms to schema and business logic requirements.

    Args:
        data: The unparsed/parsed response data from CoinGecko API.
        expected_coin_ids: List of coin IDs expected to be present.

    Returns:
        List of validated coin records.

    Raises:
        ValidationError: If any critical validation rule is violated.
    """
    if expected_coin_ids is None:
        expected_coin_ids = COIN_IDS

    # 1. Structure check
    if not isinstance(data, list):
        raise ValidationError(f"Invalid API response format: expected list, got {type(data).__name__}")

    if not data:
        raise ValidationError("API response is empty")

    # 2. Check complete batch presence
    received_ids = {coin.get("id") for coin in data if isinstance(coin, dict) and "id" in coin}
    missing_ids = set(expected_coin_ids) - received_ids
    if missing_ids:
        logger.error(f"Validation failed: missing coins in API response: {missing_ids}")
        raise ValidationError(
            f"Incomplete batch received. Missing {len(missing_ids)} coins: {sorted(list(missing_ids))}"
        )

    validated_records = []

    # 3. Individual coin field validation
    for item in data:
        if not isinstance(item, dict):
            raise ValidationError(f"Coin record is not an object/dict: {item}")

        coin_id = item.get("id")

        # Skip coins that were not in expected list if any extra coins return
        if coin_id not in expected_coin_ids:
            continue

        symbol = item.get("symbol")
        if not symbol or not isinstance(symbol, str):
            raise ValidationError(f"Coin '{coin_id}' has missing or non-string symbol: {symbol}")

        # Current Price validation (CRITICAL)
        price = item.get("current_price")
        if price is None:
            raise ValidationError(f"Coin '{coin_id}' is missing critical field 'current_price'")

        if not isinstance(price, (int, float)) or isinstance(price, bool):
            raise ValidationError(f"Coin '{coin_id}' has non-numeric price: {price} ({type(price).__name__})")

        if price < 0:
            raise ValidationError(f"Coin '{coin_id}' has negative price: {price}")

        # Market Cap validation (optional / nullable)
        market_cap = item.get("market_cap")
        if market_cap is not None and (not isinstance(market_cap, (int, float)) or isinstance(market_cap, bool)):
            raise ValidationError(f"Coin '{coin_id}' has invalid market_cap format: {market_cap}")

        # 24h Volume validation (optional / nullable)
        volume = item.get("total_volume")
        if volume is not None and (not isinstance(volume, (int, float)) or isinstance(volume, bool)):
            raise ValidationError(f"Coin '{coin_id}' has invalid volume format: {volume}")

        # 24h Price Change validation (optional / nullable)
        change_24h = item.get("price_change_percentage_24h")
        if change_24h is not None and (not isinstance(change_24h, (int, float)) or isinstance(change_24h, bool)):
            raise ValidationError(f"Coin '{coin_id}' has invalid price_change_percentage_24h format: {change_24h}")

        validated_records.append(item)

    logger.info(f"Successfully validated {len(validated_records)} coin records.")
    return validated_records
