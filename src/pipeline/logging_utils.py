"""Pipeline logging utilities."""

import logging
import sys


def setup_logging(level=logging.INFO):
    """Configure standard logging for terminal and execution logs."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
