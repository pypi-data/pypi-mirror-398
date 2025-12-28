"""
NSE Indices Module.

This module provides functions to fetch NSE index data:
- Index constituent lists
- Historical index OHLCV data
- Historical India VIX data

All functions are CSV-based and fetch reliable historical data.
"""

from __future__ import annotations

from .index_data import (
    index_list,
    constituent_stock_list,
    index_data,
    india_vix_data,
)

__all__ = [
    "index_list",
    "constituent_stock_list",
    "index_data",
    "india_vix_data",
]
