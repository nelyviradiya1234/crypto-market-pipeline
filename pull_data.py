"""Main cryptocurrency market data ingestion pipeline script."""

import os
import sys
import time
import logging
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import COIN_IDS, MAX_RETRIES, RETRY_DELAYS
from src.pipeline.logging_utils import setup_logging
from src.database.connection import get_connection, get_database_url
from src.database.queries import insert_snapshots, log_pipeline_run
from src.api.coingecko import fetch_market_data, RateLimitError, ServerError, ClientError, APIError
from src.pipeline.validation import validate_response, ValidationError
from src.pipeline.transform import transform_records

setup_logging()
logger = logging.getLogger("pull_data")


def run_pipeline():
    """Execute the data ingestion pipeline."""
    logger.info("Starting Cryptocurrency Market Data Pipeline run...")

    # 1. Database Connection Check
    conn = None
    try:
        get_database_url()  # Ensures DATABASE_URL is set
        conn = get_connection()
        logger.info("Connected to PostgreSQL database successfully.")
    except Exception as err:
        error_msg = f"Database connection failed: {err}"
        logger.error(error_msg)
        print("\n--- Pipeline Summary ---")
        print("Status: db_error")
        print("Rows written: 0")
        print(f"Error: {error_msg}")
        sys.exit(1)

    # 2. Fetch Data from API with Retry Logic
    raw_data = None
    last_exception = None
    status_code_type = "api_error"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"API Fetch Attempt {attempt}/{MAX_RETRIES}...")
            raw_data = fetch_market_data(COIN_IDS)
            break
        except RateLimitError as e:
            status_code_type = "rate_limited"
            last_exception = e
            logger.warning(f"Attempt {attempt} hit rate limit: {e}")
        except ServerError as e:
            status_code_type = "api_error"
            last_exception = e
            logger.warning(f"Attempt {attempt} encountered server error: {e}")
        except ClientError as e:
            status_code_type = "api_error"
            last_exception = e
            logger.error(f"Attempt {attempt} client error (non-retryable): {e}")
            break
        except APIError as e:
            status_code_type = "api_error"
            last_exception = e
            logger.warning(f"Attempt {attempt} API request error: {e}")

        if attempt < MAX_RETRIES:
            delay = RETRY_DELAYS[attempt - 1]
            logger.info(f"Waiting {delay} seconds before retry attempt {attempt + 1}...")
            time.sleep(delay)

    # Check if API calls failed
    if raw_data is None:
        err_detail = str(last_exception) if last_exception else "Failed to fetch CoinGecko API data"
        logger.error(f"Pipeline failed during API fetch: {err_detail}")
        log_pipeline_run(conn, status=status_code_type, rows_written=0, error_message=err_detail)
        conn.close()

        print("\n--- Pipeline Summary ---")
        print(f"Status: {status_code_type}")
        print("Rows written: 0")
        print(f"Error: {err_detail}")
        sys.exit(1)

    # 3. Validate API Response Data
    try:
        validated_data = validate_response(raw_data, expected_coin_ids=COIN_IDS)
    except ValidationError as val_err:
        err_detail = f"Data validation error: {val_err}"
        logger.error(err_detail)
        log_pipeline_run(conn, status="validation_error", rows_written=0, error_message=err_detail)
        conn.close()

        print("\n--- Pipeline Summary ---")
        print("Status: validation_error")
        print("Rows written: 0")
        print(f"Error: {err_detail}")
        sys.exit(1)

    # 4. Transform Records
    try:
        transformed_records = transform_records(validated_data, data_source="coingecko")
    except Exception as transform_err:
        err_detail = f"Transformation error: {transform_err}"
        logger.error(err_detail)
        log_pipeline_run(conn, status="validation_error", rows_written=0, error_message=err_detail)
        conn.close()

        print("\n--- Pipeline Summary ---")
        print("Status: validation_error")
        print("Rows written: 0")
        print(f"Error: {err_detail}")
        sys.exit(1)

    # 5. Database Insert Transaction
    try:
        rows_written = insert_snapshots(conn, transformed_records)
        conn.commit()
        logger.info(f"Successfully committed {rows_written} snapshot rows to database.")

        log_pipeline_run(conn, status="success", rows_written=rows_written, error_message=None)
        conn.close()

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print("\nPipeline completed successfully.")
        print(f"Coins requested: {len(COIN_IDS)}")
        print(f"Coins received: {len(validated_data)}")
        print(f"Rows written: {rows_written}")
        print(f"Pulled at: {now_utc}")
        sys.exit(0)

    except Exception as db_err:
        if conn:
            conn.rollback()
        err_detail = f"Database write error: {db_err}"
        logger.error(err_detail)

        try:
            conn_err_log = get_connection()
            log_pipeline_run(conn_err_log, status="db_error", rows_written=0, error_message=err_detail)
            conn_err_log.close()
        except Exception:
            pass

        if conn:
            conn.close()

        print("\n--- Pipeline Summary ---")
        print("Status: db_error")
        print("Rows written: 0")
        print(f"Error: {err_detail}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
