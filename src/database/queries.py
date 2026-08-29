"""Parameterized database query functions for data ingestion and dashboard analytics."""

import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Ingestion Writes
# ----------------------------------------------------------------------

def insert_snapshots(conn, records: List[Dict[str, Any]]) -> int:
    """Insert price snapshot records in a single database transaction.

    Args:
        conn: psycopg2 database connection.
        records: List of transformed record dictionaries.

    Returns:
        Number of rows inserted.
    """
    if not records:
        return 0

    query = """
        INSERT INTO price_snapshots (
            coin_id, symbol, price_usd, market_cap_usd, volume_24h_usd, change_24h_pct, pulled_at, data_source
        ) VALUES (
            %(coin_id)s, %(symbol)s, %(price_usd)s, %(market_cap_usd)s, %(volume_24h_usd)s, %(change_24h_pct)s, %(pulled_at)s, %(data_source)s
        );
    """

    cursor = conn.cursor()
    try:
        cursor.executemany(query, records)
        rows_written = cursor.rowcount
        cursor.close()
        return rows_written
    except Exception as e:
        cursor.close()
        logger.error(f"Failed to execute batch insert: {e}")
        raise e


def log_pipeline_run(conn, status: str, rows_written: int, error_message: Optional[str] = None) -> None:
    """Record execution status and stats in pipeline_log table.

    Args:
        conn: psycopg2 database connection.
        status: Run status ('success', 'api_error', 'rate_limited', 'validation_error', 'db_error').
        rows_written: Number of snapshots written.
        error_message: Optional error message string.
    """
    query = """
        INSERT INTO pipeline_log (run_at, status, rows_written, error_message)
        VALUES (NOW(), %s, %s, %s);
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (status, rows_written, error_message))
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Failed to write pipeline_log record: {e}")


# ----------------------------------------------------------------------
# Dashboard Analytics Queries
# ----------------------------------------------------------------------

def get_latest_prices(conn) -> pd.DataFrame:
    """Retrieve the most recent price snapshot for each cryptocurrency."""
    query = """
        SELECT DISTINCT ON (coin_id)
            coin_id,
            symbol,
            price_usd,
            market_cap_usd,
            volume_24h_usd,
            change_24h_pct,
            pulled_at,
            data_source
        FROM price_snapshots
        ORDER BY coin_id, pulled_at DESC;
    """
    return pd.read_sql(query, conn)


def get_price_history(
    conn,
    selected_coins: Optional[List[str]] = None,
    hours: Optional[int] = None
) -> pd.DataFrame:
    """Retrieve historical price time-series filtered by coin and time window.

    Args:
        conn: psycopg2 database connection.
        selected_coins: List of coin IDs to include.
        hours: Restrict to last N hours (e.g. 24, 72, 168, 720). None for all data.
    """
    conditions = []
    params = []

    if selected_coins:
        conditions.append("coin_id = ANY(%s)")
        params.append(selected_coins)

    if hours is not None:
        conditions.append("pulled_at >= NOW() - (INTERVAL '1 hour' * %s)")
        params.append(hours)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT coin_id, symbol, price_usd, market_cap_usd, volume_24h_usd, change_24h_pct, pulled_at, data_source
        FROM price_snapshots
        {where_clause}
        ORDER BY coin_id, pulled_at ASC;
    """
    return pd.read_sql(query, conn, params=params if params else None)


def get_pipeline_logs(conn, limit: int = 15) -> pd.DataFrame:
    """Retrieve recent pipeline execution logs."""
    query = """
        SELECT id, run_at, status, rows_written, error_message
        FROM pipeline_log
        ORDER BY run_at DESC
        LIMIT %s;
    """
    return pd.read_sql(query, conn, params=[limit])


def get_pipeline_statistics(conn) -> Dict[str, Any]:
    """Calculate aggregate pipeline health metrics."""
    query = """
        SELECT
            COUNT(*) as total_runs,
            COUNT(*) FILTER (WHERE status = 'success') as successful_runs,
            COUNT(*) FILTER (WHERE status != 'success') as failed_runs,
            COALESCE(SUM(rows_written), 0) as total_rows_written,
            MAX(run_at) FILTER (WHERE status = 'success') as last_success_at
        FROM pipeline_log;
    """
    cursor = conn.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    cursor.close()

    total_runs = row[0] or 0
    successful_runs = row[1] or 0
    failed_runs = row[2] or 0
    total_rows = row[3] or 0
    last_success_at = row[4]

    success_rate = (successful_runs / total_runs * 100.0) if total_runs > 0 else 0.0

    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "success_rate_pct": round(success_rate, 1),
        "total_rows_written": total_rows,
        "last_success_at": last_success_at
    }


def get_last_successful_pull(conn):
    """Get timestamp of the most recent successful pipeline execution."""
    query = """
        SELECT MAX(run_at)
        FROM pipeline_log
        WHERE status = 'success';
    """
    cursor = conn.cursor()
    cursor.execute(query)
    res = cursor.fetchone()
    cursor.close()
    return res[0] if res else None
