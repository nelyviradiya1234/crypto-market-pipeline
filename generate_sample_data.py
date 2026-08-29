"""Generate realistic synthetic historical data for development and demonstration purposes."""

import os
import sys
import random
from datetime import datetime, timedelta, timezone
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import COIN_IDS
from src.database.connection import get_connection
from src.database.queries import insert_snapshots
from src.pipeline.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger("generate_sample_data")

# Real market baseline values for 8 tracked cryptocurrencies
BASE_COIN_DATA = {
    "bitcoin": {"symbol": "BTC", "price": 78800.0, "market_cap": 1550000000000.0, "volume": 32000000000.0, "volatility": 0.004},
    "ethereum": {"symbol": "ETH", "price": 2490.0, "market_cap": 300000000000.0, "volume": 16000000000.0, "volatility": 0.005},
    "solana": {"symbol": "SOL", "price": 101.50, "market_cap": 48000000000.0, "volume": 3800000000.0, "volatility": 0.008},
    "binancecoin": {"symbol": "BNB", "price": 705.00, "market_cap": 102000000000.0, "volume": 1400000000.0, "volatility": 0.004},
    "ripple": {"symbol": "XRP", "price": 1.41, "market_cap": 80000000000.0, "volume": 2100000000.0, "volatility": 0.006},
    "cardano": {"symbol": "ADA", "price": 0.21, "market_cap": 7500000000.0, "volume": 450000000.0, "volatility": 0.007},
    "dogecoin": {"symbol": "DOGE", "price": 0.087, "market_cap": 12800000000.0, "volume": 890000000.0, "volatility": 0.009},
    "polkadot": {"symbol": "DOT", "price": 0.87, "market_cap": 1250000000.0, "volume": 180000000.0, "volatility": 0.007},
}


def generate_synthetic_history(days: int = 7):
    """Populate database with smooth, realistic synthetic historical market data."""
    logger.info(f"Generating {days} days of clean synthetic historical cryptocurrency data...")

    conn = get_connection()
    cursor = conn.cursor()

    # Purge any previous synthetic records and logs for clean re-seed
    logger.info("Purging old synthetic snapshots and synthetic execution logs...")
    cursor.execute("DELETE FROM price_snapshots WHERE data_source = 'synthetic';")
    cursor.execute("DELETE FROM pipeline_log WHERE error_message LIKE '%Synthetic%';")
    conn.commit()
    cursor.close()

    now = datetime.now(timezone.utc)
    interval_minutes = 30
    total_steps = int((days * 24 * 60) / interval_minutes)
    start_time = now - timedelta(minutes=total_steps * interval_minutes)

    # Initialize price trajectory with smooth random walk
    price_series = {coin_id: [] for coin_id in COIN_IDS}
    for coin_id in COIN_IDS:
        base_p = BASE_COIN_DATA[coin_id]["price"]
        vol = BASE_COIN_DATA[coin_id]["volatility"]
        current = base_p * 0.95  # start slightly lower 7 days ago

        for step in range(total_steps + 1):
            # Smooth momentum random walk
            drift = 0.00015
            noise = random.gauss(0, vol)
            current = max(current * (1 + drift + noise), 0.0001)
            price_series[coin_id].append(current)

    all_snapshots = []
    log_entries = []

    steps_in_24h = 48  # 24 hours / 30 mins

    for step in range(total_steps + 1):
        timestamp = start_time + timedelta(minutes=step * interval_minutes)

        # Occasional synthetic status simulation
        rand_val = random.random()
        if rand_val < 0.015:
            log_entries.append((timestamp, "rate_limited", 0, "Synthetic: Rate limit HTTP 429"))
            continue
        elif rand_val < 0.025:
            log_entries.append((timestamp, "api_error", 0, "Synthetic: Upstream API HTTP 500"))
            continue

        step_count = 0
        for coin_id in COIN_IDS:
            base_info = BASE_COIN_DATA[coin_id]
            price = price_series[coin_id][step]

            # Calculate accurate 24h percentage change from step - 48
            idx_24h = max(0, step - steps_in_24h)
            price_24h_ago = price_series[coin_id][idx_24h]
            change_24h_pct = ((price - price_24h_ago) / price_24h_ago) * 100.0

            mcap = price * (base_info["market_cap"] / base_info["price"])
            vol = base_info["volume"] * (0.9 + 0.2 * random.random())

            record = {
                "coin_id": coin_id,
                "symbol": base_info["symbol"],
                "price_usd": round(price, 6 if price < 1 else 2),
                "market_cap_usd": round(mcap, 2),
                "volume_24h_usd": round(vol, 2),
                "change_24h_pct": round(change_24h_pct, 2),
                "pulled_at": timestamp,
                "data_source": "synthetic"
            }
            all_snapshots.append(record)
            step_count += 1

        log_entries.append((timestamp, "success", step_count, None))

    logger.info(f"Writing {len(all_snapshots)} synthetic price snapshots in batch...")
    insert_snapshots(conn, all_snapshots)

    logger.info(f"Writing {len(log_entries)} pipeline_log records...")
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO pipeline_log (run_at, status, rows_written, error_message) VALUES (%s, %s, %s, %s);",
        log_entries
    )
    conn.commit()
    cursor.close()
    conn.close()

    logger.info(f"[SUCCESS] Generated {len(all_snapshots)} clean snapshots across {total_steps} 30-min intervals.")


if __name__ == "__main__":
    generate_synthetic_history(days=7)
