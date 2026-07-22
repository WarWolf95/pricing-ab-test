"""Shared Utilities and Logging Configuration for Pricing A/B Test.

Provides logging setup, statistical formatting, and data validation helpers.
"""

import logging
import sys
from typing import Union


def setup_logger(name: str = "pricing_ab_test") -> logging.Logger:
    """Configures and returns a standardised stream logger for UK Data Analyst pipelines.

    Args:
        name: Logger name identifier.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def format_gbp(amount: Union[int, float]) -> str:
    """Formats a numeric value as GBP currency string according to UK formatting rules.

    Args:
        amount: Numeric amount to format.

    Returns:
        str: Formatted currency string (e.g. '£587.00').
    """
    return f"£{amount:,.2f}"


def format_pct(val: float, decimals: int = 2) -> str:
    """Formats a decimal proportion as a percentage string.

    Args:
        val: Proportion between 0.0 and 1.0.
        decimals: Number of decimal places.

    Returns:
        str: Formatted percentage string (e.g. '8.50%').
    """
    return f"{val * 100:.{decimals}f}%"
