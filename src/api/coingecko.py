"""CoinGecko API client for fetching cryptocurrency market data."""

import logging
from typing import List, Dict, Any, Optional
import requests

from src.config import MARKETS_ENDPOINT, VS_CURRENCY, API_TIMEOUT, COIN_IDS

logger = logging.getLogger(__name__)


# Custom Exception Hierarchy
class APIError(Exception):
    """Base exception for CoinGecko API failures."""
    pass


class RateLimitError(APIError):
    """Raised when API returns HTTP 429 Rate Limit Exceeded."""
    pass


class ServerError(APIError):
    """Raised when API returns HTTP 5xx Server Error."""
    pass


class ClientError(APIError):
    """Raised when API returns HTTP 4xx Client Error (other than 429)."""
    pass


def fetch_market_data(coin_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Fetch cryptocurrency market snapshot from CoinGecko API.

    Args:
        coin_ids: List of cryptocurrency string identifiers. Defaults to COIN_IDS in config.

    Returns:
        List of dictionaries containing coin market data.

    Raises:
        RateLimitError: If HTTP 429 rate limit is encountered.
        ServerError: If HTTP 5xx server error occurs.
        ClientError: If HTTP 4xx client error occurs.
        APIError: For other network, connection, or response format errors.
    """
    ids_to_fetch = coin_ids if coin_ids is not None else COIN_IDS
    params = {
        "vs_currency": VS_CURRENCY,
        "ids": ",".join(ids_to_fetch),
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "24h"
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "CryptoMarketPipeline/1.0"
    }

    logger.info(f"Requesting CoinGecko market data for {len(ids_to_fetch)} coins...")

    try:
        response = requests.get(
            MARKETS_ENDPOINT,
            params=params,
            headers=headers,
            timeout=API_TIMEOUT
        )
    except requests.exceptions.Timeout as e:
        logger.error(f"CoinGecko API request timed out after {API_TIMEOUT} seconds.")
        raise APIError(f"Request timeout: {e}") from e
    except requests.exceptions.ConnectionError as e:
        logger.error("Failed to connect to CoinGecko API endpoint.")
        raise APIError(f"Connection error: {e}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Unexpected HTTP request error: {e}")
        raise APIError(f"Request error: {e}") from e

    status_code = response.status_code
    logger.info(f"CoinGecko API responded with HTTP status {status_code}")

    if status_code == 200:
        try:
            data = response.json()
            if not isinstance(data, list):
                raise APIError(f"Expected JSON list from CoinGecko API, received {type(data).__name__}")
            return data
        except ValueError as e:
            logger.error("Failed to parse JSON response from CoinGecko.")
            raise APIError("Malformed JSON response") from e

    elif status_code == 429:
        logger.warning("CoinGecko API rate limit exceeded (HTTP 429).")
        raise RateLimitError("CoinGecko returned HTTP 429 Rate Limit Exceeded")

    elif 400 <= status_code < 500:
        logger.error(f"CoinGecko client error HTTP {status_code}: {response.text[:200]}")
        raise ClientError(f"CoinGecko returned HTTP {status_code}")

    elif 500 <= status_code < 600:
        logger.error(f"CoinGecko server error HTTP {status_code}: {response.text[:200]}")
        raise ServerError(f"CoinGecko returned HTTP {status_code}")

    else:
        logger.error(f"Unexpected HTTP status code {status_code}")
        raise APIError(f"CoinGecko returned unexpected status HTTP {status_code}")
