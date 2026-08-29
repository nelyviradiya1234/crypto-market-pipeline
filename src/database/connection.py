"""PostgreSQL connection management module."""

import os
import logging
from contextlib import contextmanager
import psycopg2
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Retrieve the database URL from environment variables or Streamlit secrets."""
    # Check environment variable first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # Fallback to Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    raise ValueError(
        "DATABASE_URL is not set. Please configure it in environment variables or .env file."
    )


def get_connection():
    """Create and return a new PostgreSQL database connection."""
    db_url = get_database_url()
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error("Failed to connect to PostgreSQL database.")
        raise e


@contextmanager
def get_db_cursor():
    """Context manager for database connections and cursors with automatic commit/rollback."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error during transaction: {type(e).__name__}")
        raise e
    finally:
        cursor.close()
        conn.close()
