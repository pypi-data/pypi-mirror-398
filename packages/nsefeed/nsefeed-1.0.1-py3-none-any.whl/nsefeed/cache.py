"""
SQLite-based caching layer for nsefeed.

This module provides a caching mechanism to:
- Reduce redundant network requests to NSE
- Store historical OHLC data locally
- Cache metadata and company info
- Support TTL (Time To Live) for cache entries

Cache location: ~/.nsefeed/cache.db (configurable)
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, date
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator, TypeVar, ParamSpec

import pandas as pd

from . import logger
from .constants import (
    DEFAULT_CACHE_DIR,
    CACHE_DB_NAME,
    CACHE_TTL,
)
from .exceptions import NSECacheError

P = ParamSpec("P")
R = TypeVar("R")


class NSECache:
    """
    SQLite-based cache for NSE data.

    This class manages a local SQLite database for caching NSE data.
    It supports different TTLs for different data types and handles
    cache invalidation automatically.

    Usage:
        cache = NSECache()
        cache.set_ohlc("RELIANCE", df, start_date, end_date)
        df = cache.get_ohlc("RELIANCE", start_date, end_date)
        cache.close()

    Thread-Safety:
        This class is thread-safe and can be used from multiple threads.
    """

    _instance: NSECache | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, cache_dir: str | Path | None = None) -> "NSECache":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """
        Initialize the cache.

        Args:
            cache_dir: Directory for cache database. Defaults to ~/.nsefeed/
        """
        if self._initialized:
            return

        if cache_dir is None:
            cache_dir = Path.home() / DEFAULT_CACHE_DIR
        else:
            cache_dir = Path(cache_dir)

        # Create cache directory if it doesn't exist
        cache_dir.mkdir(parents=True, exist_ok=True)

        self._db_path = cache_dir / CACHE_DB_NAME
        self._local = threading.local()
        self._initialized = True

        # Initialize database schema
        self._init_db()

        logger.debug(f"Cache initialized at {self._db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
                timeout=30.0,
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
        return self._local.connection

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for database cursor with automatic commit."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise NSECacheError(
                "Database operation failed",
                details=str(e),
            )
        finally:
            cursor.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._cursor() as cursor:
            # OHLC data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ohlc_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    trade_date DATE NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    value REAL,
                    trades INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, trade_date)
                )
            """)

            # Index data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS index_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL,
                    trade_date DATE NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(index_name, trade_date)
                )
            """)

            # Metadata cache table (for company info, index constituents, etc.)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata_cache (
                    cache_key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    expiry TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indices for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_date
                ON ohlc_data(symbol, trade_date)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_index_name_date
                ON index_data(index_name, trade_date)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metadata_expiry
                ON metadata_cache(expiry)
            """)

    def set_ohlc(
        self,
        symbol: str,
        df: pd.DataFrame,
    ) -> None:
        """
        Cache OHLC data for a symbol.

        Args:
            symbol: Stock symbol
            df: DataFrame with OHLC data (must have 'date' column as index or column)
        """
        if df.empty:
            return

        symbol = symbol.upper()

        # Ensure date is in the right format
        if "date" in df.columns:
            df = df.set_index("date") if df.index.name != "date" else df
        elif df.index.name != "date":
            logger.warning(f"DataFrame has no 'date' column for {symbol}")
            return

        with self._cursor() as cursor:
            for trade_date, row in df.iterrows():
                if isinstance(trade_date, str):
                    trade_date_str = trade_date
                elif isinstance(trade_date, (datetime, date)):
                    trade_date_str = trade_date.strftime("%Y-%m-%d")
                else:
                    trade_date_str = str(trade_date)

                cursor.execute("""
                    INSERT OR REPLACE INTO ohlc_data
                    (symbol, trade_date, open, high, low, close, volume, value, trades)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    trade_date_str,
                    row.get("open"),
                    row.get("high"),
                    row.get("low"),
                    row.get("close"),
                    row.get("volume"),
                    row.get("value"),
                    row.get("trades"),
                ))

        logger.debug(f"Cached {len(df)} rows for {symbol}")

    def get_ohlc(
        self,
        symbol: str,
        start_date: date | str,
        end_date: date | str,
    ) -> pd.DataFrame | None:
        """
        Get cached OHLC data for a symbol and date range.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLC data, or None if not in cache
        """
        symbol = symbol.upper()

        # Normalize dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()

        with self._cursor() as cursor:
            cursor.execute("""
                SELECT trade_date, open, high, low, close, volume, value, trades
                FROM ohlc_data
                WHERE symbol = ?
                AND trade_date >= ?
                AND trade_date <= ?
                ORDER BY trade_date ASC
            """, (symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            rows = cursor.fetchall()

        if not rows:
            return None

        df = pd.DataFrame(
            [dict(row) for row in rows],
            columns=["date", "open", "high", "low", "close", "volume", "value", "trades"],
        )

        # Rename trade_date to date
        df.rename(columns={"trade_date": "date"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        logger.debug(f"Cache hit for {symbol}: {len(df)} rows")
        return df

    def get_cached_date_range(self, symbol: str) -> tuple[date, date] | None:
        """
        Get the date range of cached data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (start_date, end_date) or None if no data cached
        """
        symbol = symbol.upper()

        with self._cursor() as cursor:
            cursor.execute("""
                SELECT MIN(trade_date), MAX(trade_date)
                FROM ohlc_data
                WHERE symbol = ?
            """, (symbol,))

            row = cursor.fetchone()

        if row and row[0] and row[1]:
            return (
                datetime.strptime(row[0], "%Y-%m-%d").date(),
                datetime.strptime(row[1], "%Y-%m-%d").date(),
            )
        return None

    def set_index_data(
        self,
        index_name: str,
        df: pd.DataFrame,
    ) -> None:
        """
        Cache index OHLC data.

        Args:
            index_name: Index name (e.g., "NIFTY 50")
            df: DataFrame with OHLC data
        """
        if df.empty:
            return

        index_name = index_name.upper()

        # Ensure date is in the right format
        if "date" in df.columns:
            df = df.set_index("date") if df.index.name != "date" else df
        elif df.index.name != "date":
            return

        with self._cursor() as cursor:
            for trade_date, row in df.iterrows():
                if isinstance(trade_date, str):
                    trade_date_str = trade_date
                elif isinstance(trade_date, (datetime, date)):
                    trade_date_str = trade_date.strftime("%Y-%m-%d")
                else:
                    trade_date_str = str(trade_date)

                cursor.execute("""
                    INSERT OR REPLACE INTO index_data
                    (index_name, trade_date, open, high, low, close)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    index_name,
                    trade_date_str,
                    row.get("open"),
                    row.get("high"),
                    row.get("low"),
                    row.get("close"),
                ))

        logger.debug(f"Cached {len(df)} index rows for {index_name}")

    def get_index_data(
        self,
        index_name: str,
        start_date: date | str,
        end_date: date | str,
    ) -> pd.DataFrame | None:
        """
        Get cached index data.

        Args:
            index_name: Index name
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with index OHLC data, or None if not cached
        """
        index_name = index_name.upper()

        # Normalize dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()

        with self._cursor() as cursor:
            cursor.execute("""
                SELECT trade_date, open, high, low, close
                FROM index_data
                WHERE index_name = ?
                AND trade_date >= ?
                AND trade_date <= ?
                ORDER BY trade_date ASC
            """, (index_name, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            rows = cursor.fetchall()

        if not rows:
            return None

        df = pd.DataFrame(
            [dict(row) for row in rows],
            columns=["date", "open", "high", "low", "close"],
        )

        df.rename(columns={"trade_date": "date"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        return df

    def set_metadata(
        self,
        key: str,
        data: Any,
        ttl: int | None = None,
    ) -> None:
        """
        Cache metadata with TTL.

        Args:
            key: Cache key
            data: Data to cache (must be JSON serializable)
            ttl: Time to live in seconds (default: 24 hours)
        """
        if ttl is None:
            ttl = CACHE_TTL["company_info"]

        expiry = datetime.now().timestamp() + ttl
        json_data = json.dumps(data)

        with self._cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO metadata_cache
                (cache_key, data, expiry)
                VALUES (?, ?, ?)
            """, (key, json_data, expiry))

        logger.debug(f"Cached metadata: {key}")

    def get_metadata(self, key: str) -> Any | None:
        """
        Get cached metadata.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found or expired
        """
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT data, expiry
                FROM metadata_cache
                WHERE cache_key = ?
            """, (key,))

            row = cursor.fetchone()

        if not row:
            return None

        # Check expiry
        if row["expiry"] < datetime.now().timestamp():
            # Expired, delete and return None
            self.delete_metadata(key)
            return None

        try:
            return json.loads(row["data"])
        except json.JSONDecodeError:
            return None

    def delete_metadata(self, key: str) -> None:
        """Delete a metadata cache entry."""
        with self._cursor() as cursor:
            cursor.execute("DELETE FROM metadata_cache WHERE cache_key = ?", (key,))

    def clear_expired(self) -> int:
        """
        Clear all expired metadata entries.

        Returns:
            Number of entries deleted
        """
        now = datetime.now().timestamp()
        with self._cursor() as cursor:
            cursor.execute("DELETE FROM metadata_cache WHERE expiry < ?", (now,))
            deleted = cursor.rowcount
        logger.debug(f"Cleared {deleted} expired cache entries")
        return deleted

    def clear_symbol(self, symbol: str) -> None:
        """Clear all cached data for a symbol."""
        symbol = symbol.upper()
        with self._cursor() as cursor:
            cursor.execute("DELETE FROM ohlc_data WHERE symbol = ?", (symbol,))
        logger.debug(f"Cleared cache for {symbol}")

    def clear_all(self) -> None:
        """Clear all cached data."""
        with self._cursor() as cursor:
            cursor.execute("DELETE FROM ohlc_data")
            cursor.execute("DELETE FROM index_data")
            cursor.execute("DELETE FROM metadata_cache")
        logger.info("Cache cleared completely")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._cursor() as cursor:
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ohlc_data")
            num_symbols = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ohlc_data")
            num_ohlc_rows = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT index_name) FROM index_data")
            num_indices = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM metadata_cache")
            num_metadata = cursor.fetchone()[0]

        return {
            "symbols_cached": num_symbols,
            "ohlc_rows": num_ohlc_rows,
            "indices_cached": num_indices,
            "metadata_entries": num_metadata,
            "db_path": str(self._db_path),
        }

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
        logger.debug("Cache connection closed")

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None


def cached(
    ttl: int | None = None,
    key_prefix: str = "",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key

    Usage:
        @cached(ttl=3600, key_prefix="company_info")
        def get_company_info(symbol: str) -> dict:
            ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cache = NSECache()
            cached_result = cache.get_metadata(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache.set_metadata(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


# Convenience function for clearing cache
def clear_cache() -> None:
    """Clear all nsefeed cache data."""
    cache = NSECache()
    cache.clear_all()
