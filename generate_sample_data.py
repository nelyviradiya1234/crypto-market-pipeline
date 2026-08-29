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
from src.database.queries import insert_snapshots, log_pipeline_run
from src.pipeline.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger("generate_sample_data")

BASE_COIN_DATA = {
    "bitcoin": {"symbol": "BTC", "price": 64500.0, "market_cap": 1270000000000.0, "volume": 28000000000.0},
    "ethereum": {"symbol": "ETH", "price": 3450.0, "market_cap": 415000000000.0, "volume": 15000000000.0},
    "solana": {"symbol": "SOL", "price": 145.0, "market_cap": 67000000000.0, "volume": 2500000000.0},
    "binancecoin": {"symbol": "BNB", "price": 575.0, "market_cap": 84000000000.0, "volume": 1100000000.0},
    "ripple": {"symbol": "XRP", "price": 0.56, "market_cap": 31000000000.0, "volume": 950000000.0},
    "cardano": {"symbol": "ADA", "price": 0.46, "market_cap": 16500000000.0, "volume": 420000000.0},
    "dogecoin": {"symbol": "DOGE", "price": 0.125, "market_cap": 18200000000.0, "volume": 680000000.0},
    "polkadot": {"symbol": "DOT", "price": 6.80, "market_cap": 9800000000.0, "volume": 210000000.0},
}


def generate_synthetic_history(days: int = 10):
    """Populate database with synthetic historical market data in efficient batch operations."""
    logger.info(f"Generating {days} days of synthetic cryptocurrency historical data...")

    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing synthetic data first for clean re-runs
    logger.info("Clearing existing synthetic records...")
    cursor.execute("DELETE FROM price_snapshots WHERE data_source = 'synthetic';")
    cursor.execute("DELETE FROM pipeline_log WHERE error_message LIKE '%Synthetic%';")
    conn.commit()
    cursor.close()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)

    interval_minutes = 30
    total_steps = int((days * 24 * 60) / interval_minutes)

    current_prices = {coin_id: BASE_COIN_DATA[coin_id]["price"] for coin_id in COIN_IDS}

    all_snapshots = []
    log_entries = []

    for step in range(total_steps):
        timestamp = start_time + timedelta(minutes=step * interval_minutes)

        rand_val = random.random()
        if rand_val < 0.02:
            log_entries.append((timestamp, "rate_limited", 0, "Synthetic: CoinGecko returned HTTP 429"))
            continue
        elif rand_val < 0.035:
            log_entries.append((timestamp, "api_error", 0, "Synthetic: CoinGecko returned HTTP 500"))
            continue

        step_count = 0
        for coin_id in COIN_IDS:
            base_info = BASE_COIN_DATA[coin_id]
            prev_price = current_prices[coin_id]

            change_pct = random.uniform(-0.012, 0.0125)
            new_price = max(prev_price * (1 + change_pct), 0.0001)
            current_prices[coin_id] = new_price

            change_24h = random.uniform(-8.5, 10.2)
            mcap = new_price * (base_info["market_cap"] / base_info["price"])
            vol = base_info["volume"] * random.uniform(0.85, 1.25)

            record = {
                "coin_id": coin_id,
                "symbol": base_info["symbol"],
                "price_usd": round(new_price, 6 if new_price < 1 else 2),
                "market_cap_usd": round(mcap, 2),
                "volume_24h_usd": round(vol, 2),
                "change_24h_pct": round(change_24h, 2),
                "pulled_at": timestamp,
                "data_source": "synthetic"
            }
            all_snapshots.append(record)
            step_count += 1

        log_entries.append((timestamp, "success", step_count, None))

    logger.info(f"Inserting {len(all_snapshots)} snapshot records in a single batch...")
    insert_snapshots(conn, all_snapshots)

    logger.info(f"Inserting {len(log_entries)} pipeline_log records...")
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO pipeline_log (run_at, status, rows_written, error_message) VALUES (%s, %s, %s, %s);",
        log_entries
    )
    conn.commit()
    cursor.close()
    conn.close()

    logger.info(f"[SUCCESS] Fast batch generation completed. Inserted {len(all_snapshots)} snapshots and {len(log_entries)} logs.")


if __name__ == "__main__":
    generate_synthetic_history(days=10)
