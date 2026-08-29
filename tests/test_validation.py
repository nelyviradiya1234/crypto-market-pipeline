"""Unit tests for the data validation module."""

import pytest
from src.pipeline.validation import validate_response, ValidationError

SAMPLE_VALID_RESPONSE = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 65000.0,
        "market_cap": 1280000000000.0,
        "total_volume": 25000000000.0,
        "price_change_percentage_24h": 2.5
    },
    {
        "id": "ethereum",
        "symbol": "eth",
        "name": "Ethereum",
        "current_price": 3500.0,
        "market_cap": 420000000000.0,
        "total_volume": 15000000000.0,
        "price_change_percentage_24h": -1.2
    }
]

EXPECTED_IDS = ["bitcoin", "ethereum"]


def test_validate_response_valid():
    """Test that a fully valid payload passes validation."""
    validated = validate_response(SAMPLE_VALID_RESPONSE, expected_coin_ids=EXPECTED_IDS)
    assert len(validated) == 2
    assert validated[0]["id"] == "bitcoin"
    assert validated[1]["id"] == "ethereum"


def test_validate_response_not_a_list():
    """Test that a non-list response raises ValidationError."""
    with pytest.raises(ValidationError, match="expected list"):
        validate_response({"id": "bitcoin"}, expected_coin_ids=EXPECTED_IDS)


def test_validate_response_empty():
    """Test that an empty list raises ValidationError."""
    with pytest.raises(ValidationError, match="empty"):
        validate_response([], expected_coin_ids=EXPECTED_IDS)


def test_validate_response_incomplete_batch():
    """Test that a batch missing expected coins is rejected."""
    partial_response = [SAMPLE_VALID_RESPONSE[0]]  # Only bitcoin, missing ethereum
    with pytest.raises(ValidationError, match="Incomplete batch received"):
        validate_response(partial_response, expected_coin_ids=EXPECTED_IDS)


def test_validate_response_missing_price():
    """Test that missing current_price raises ValidationError."""
    invalid_data = [
        {"id": "bitcoin", "symbol": "btc", "market_cap": 1000},
        {"id": "ethereum", "symbol": "eth", "current_price": 3500.0}
    ]
    with pytest.raises(ValidationError, match="missing critical field 'current_price'"):
        validate_response(invalid_data, expected_coin_ids=EXPECTED_IDS)


def test_validate_response_negative_price():
    """Test that a negative price raises ValidationError."""
    invalid_data = [
        {"id": "bitcoin", "symbol": "btc", "current_price": -100.0},
        {"id": "ethereum", "symbol": "eth", "current_price": 3500.0}
    ]
    with pytest.raises(ValidationError, match="negative price"):
        validate_response(invalid_data, expected_coin_ids=EXPECTED_IDS)


def test_validate_response_non_numeric_price():
    """Test that a non-numeric string price raises ValidationError."""
    invalid_data = [
        {"id": "bitcoin", "symbol": "btc", "current_price": "65000"},
        {"id": "ethereum", "symbol": "eth", "current_price": 3500.0}
    ]
    with pytest.raises(ValidationError, match="non-numeric price"):
        validate_response(invalid_data, expected_coin_ids=EXPECTED_IDS)


def test_validate_response_nullable_fields_allowed_none():
    """Test that null market_cap, volume, or 24h change are accepted."""
    valid_with_nulls = [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "current_price": 65000.0,
            "market_cap": None,
            "total_volume": None,
            "price_change_percentage_24h": None
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "current_price": 3500.0,
            "market_cap": 420000000000.0,
            "total_volume": 15000000000.0,
            "price_change_percentage_24h": -1.2
        }
    ]
    validated = validate_response(valid_with_nulls, expected_coin_ids=EXPECTED_IDS)
    assert len(validated) == 2
    assert validated[0]["market_cap_usd"] is None if "market_cap_usd" in validated[0] else True
