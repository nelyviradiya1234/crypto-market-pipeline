"""Database initialization script to set up PostgreSQL schema and indexes."""

import os
import sys
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_connection, get_database_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("init_db")


def init_database():
    """Execute the SQL schema to initialize tables and indexes."""
    try:
        db_url = get_database_url()
        logger.info("Connecting to PostgreSQL database...")
    except ValueError as err:
        logger.error(str(err))
        sys.exit(1)

    schema_file = os.path.join(os.path.dirname(__file__), "sql", "schema.sql")
    if not os.path.exists(schema_file):
        logger.error(f"Schema file not found at {schema_file}")
        sys.exit(1)

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        logger.info("Executing schema initialization (tables & indexes)...")
        cursor.execute(schema_sql)
        conn.commit()
        cursor.close()
        logger.info("[SUCCESS] Database initialized successfully. All tables and indexes are ready.")
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"[ERROR] Database initialization failed: {type(e).__name__} - {str(e)}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    init_database()
