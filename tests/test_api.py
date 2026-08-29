"""Unit tests for CoinGecko API client using mocked HTTP requests."""

from unittest.mock import patch, MagicMock
import pytest
import requests

from src.api.coingecko import (
    fetch_market_data,
    RateLimitError,
    ServerError,
    ClientError,
    APIError,
)


@patch("requests.get")
def test_fetch_market_data_success(mock_get):
    """Test successful API response (HTTP 200)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "bitcoin", "symbol": "btc", "current_price": 65000.0}]
    mock_get.return_value = mock_response

    result = fetch_market_data(["bitcoin"])
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == "bitcoin"


@patch("requests.get")
def test_fetch_market_data_rate_limit(mock_get):
    """Test HTTP 429 Rate Limit error handling."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_get.return_value = mock_response

    with pytest.raises(RateLimitError, match="HTTP 429 Rate Limit Exceeded"):
        fetch_market_data(["bitcoin"])


@patch("requests.get")
def test_fetch_market_data_server_error(mock_get):
    """Test HTTP 500 Server error handling."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    with pytest.raises(ServerError, match="HTTP 500"):
        fetch_market_data(["bitcoin"])


@patch("requests.get")
def test_fetch_market_data_client_error(mock_get):
    """Test HTTP 404 Client error handling."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    with pytest.raises(ClientError, match="HTTP 404"):
        fetch_market_data(["bitcoin"])


@patch("requests.get")
def test_fetch_market_data_timeout(mock_get):
    """Test network timeout exception handling."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    with pytest.raises(APIError, match="Request timeout"):
        fetch_market_data(["bitcoin"])


@patch("requests.get")
def test_fetch_market_data_connection_error(mock_get):
    """Test network connection failure exception handling."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

    with pytest.raises(APIError, match="Connection error"):
        fetch_market_data(["bitcoin"])
