"""Centralized configuration settings for the cryptocurrency market monitoring system."""

import os

# Cryptocurrencies to track
COIN_IDS = [
    "bitcoin",
    "ethereum",
    "solana",
    "binancecoin",
    "ripple",
    "cardano",
    "dogecoin",
    "polkadot",
]

# Centralized Cryptocurrency Metadata Mapping
COIN_METADATA = {
    "bitcoin": {"symbol": "BTC", "name": "Bitcoin"},
    "ethereum": {"symbol": "ETH", "name": "Ethereum"},
    "solana": {"symbol": "SOL", "name": "Solana"},
    "binancecoin": {"symbol": "BNB", "name": "Binance Coin"},
    "ripple": {"symbol": "XRP", "name": "Ripple"},
    "cardano": {"symbol": "ADA", "name": "Cardano"},
    "dogecoin": {"symbol": "DOGE", "name": "Dogecoin"},
    "polkadot": {"symbol": "DOT", "name": "Polkadot"},
}


def get_coin_symbol(coin_id: str) -> str:
    """Return asset symbol (e.g. BTC) for a given coin ID."""
    meta = COIN_METADATA.get(coin_id.lower())
    return meta["symbol"] if meta else coin_id.upper()


def get_coin_name(coin_id: str) -> str:
    """Return user-friendly asset name (e.g. Binance Coin) for a given coin ID."""
    meta = COIN_METADATA.get(coin_id.lower())
    return meta["name"] if meta else coin_id.capitalize()


def get_display_name(coin_id: str) -> str:
    """Return formatted display string e.g. BTC (Bitcoin)."""
    meta = COIN_METADATA.get(coin_id.lower())
    if meta:
        return f"{meta['symbol']} — {meta['name']}"
    return coin_id.capitalize()


# CoinGecko API settings
API_BASE_URL = "https://api.coingecko.com/api/v3"
MARKETS_ENDPOINT = f"{API_BASE_URL}/coins/markets"
VS_CURRENCY = "usd"
API_TIMEOUT = 30  # seconds

# Pipeline retry settings (exponential backoff delays in seconds)
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 45]

# Monitoring & Alert thresholds
STALE_THRESHOLD_MINUTES = 45

# Dashboard settings
DASHBOARD_REFRESH_SECONDS = 300  # 5 minutes
