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
