"""
Bhav Copy scraper for NSE historical data.

This module handles downloading and parsing of NSE bhav copy files
which contain daily OHLC data for all equities.

Bhav copy formats:
1. Old format (historical data):
   URL: https://archives.nseindia.com/content/historical/EQUITIES/{year}/{month}/cm{DDMmmYYYY}bhav.csv.zip

2. New format (UDiFF, recent data):
   URL: https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{YYYYMMDD}_F_0000.csv.zip
"""

from __future__ import annotations

import io
import zipfile
from datetime import date, datetime, timedelta
from typing import Generator

import pandas as pd

from .. import logger
from ..constants import (
    BHAV_COPY_OLD_URL,
    BHAV_COPY_NEW_URL,
    BHAV_COPY_OLD_COLUMNS,
    BHAV_COPY_NEW_COLUMNS,
    PRIMARY_SERIES,
)
from ..exceptions import NSEDataNotFoundError, NSEConnectionError, NSEParseError
from ..session import NSESession
from ..utils import (
    parse_date,
    format_date,
    validate_date_range,
    is_trading_day,
    get_previous_trading_day,
    standardize_dataframe,
    filter_by_series,
)
from ..cache import NSECache


class BhavCopyScraper:
    """
    Scraper for NSE Bhav Copy files.

    Bhav copy files contain daily End-of-Day (EOD) data for all NSE equities
    including OHLC, volume, value, and number of trades.

    Usage:
        scraper = BhavCopyScraper()
        df = scraper.fetch_for_date(date(2024, 1, 15))
        df = scraper.fetch_for_symbol("RELIANCE", date(2024, 1, 1), date(2024, 1, 31))
    """

    def __init__(self, use_cache: bool = True) -> None:
        """
        Initialize the bhav copy scraper.

        Args:
            use_cache: Whether to use local cache
        """
        self._session = NSESession.get_instance()
        self._cache = NSECache() if use_cache else None
        self._use_cache = use_cache

    def _build_old_url(self, d: date) -> str:
        """
        Build URL for old bhav copy format.

        Example: https://archives.nseindia.com/content/historical/EQUITIES/2024/JAN/cm02JAN2024bhav.csv.zip

        Args:
            d: Date for bhav copy

        Returns:
            URL string
        """
        year = str(d.year)
        month = d.strftime("%b").upper()  # JAN, FEB, etc.
        date_str = d.strftime("%d%b%Y").upper()  # 02JAN2024

        return BHAV_COPY_OLD_URL.replace("{{year}}", year).replace(
            "{{month}}", month
        ).replace("{{date}}", date_str)

    def _build_new_url(self, d: date) -> str:
        """
        Build URL for new bhav copy format (UDiFF).

        Example: https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20240102_F_0000.csv.zip

        Args:
            d: Date for bhav copy

        Returns:
            URL string
        """
        date_str = d.strftime("%Y%m%d")  # 20240102
        return BHAV_COPY_NEW_URL.replace("{{date}}", date_str)

    def _download_and_parse(self, url: str, is_new_format: bool) -> pd.DataFrame:
        """
        Download and parse a bhav copy ZIP file.

        Args:
            url: URL of the ZIP file
            is_new_format: Whether this is the new UDiFF format

        Returns:
            DataFrame with parsed data

        Raises:
            NSEConnectionError: On download failures
            NSEParseError: On parsing failures
        """
        try:
            logger.debug(f"Downloading bhav copy: {url}")
            content = self._session.download_file(url)

            # Extract CSV from ZIP
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # Get the first CSV file
                csv_files = [f for f in zf.namelist() if f.endswith(".csv")]
                if not csv_files:
                    raise NSEParseError(
                        "No CSV file found in bhav copy ZIP",
                        details=f"ZIP contents: {zf.namelist()}",
                    )

                csv_filename = csv_files[0]
                with zf.open(csv_filename) as csv_file:
                    df = pd.read_csv(csv_file)

            return self._parse_bhav_copy(df, is_new_format)

        except zipfile.BadZipFile:
            raise NSEParseError(
                "Invalid ZIP file received",
                details=f"URL: {url}",
            )
        except pd.errors.ParserError as e:
            raise NSEParseError(
                "Failed to parse bhav copy CSV",
                details=str(e),
            )

    def _parse_bhav_copy(self, df: pd.DataFrame, is_new_format: bool) -> pd.DataFrame:
        """
        Parse and standardize bhav copy DataFrame.

        Args:
            df: Raw DataFrame from CSV
            is_new_format: Whether this is the new UDiFF format

        Returns:
            Standardized DataFrame
        """
        # Choose column mapping based on format
        column_map = BHAV_COPY_NEW_COLUMNS if is_new_format else BHAV_COPY_OLD_COLUMNS

        # Rename columns that exist
        rename_map = {}
        for old_col, new_col in column_map.items():
            # Handle case-insensitive matching
            matching_cols = [c for c in df.columns if c.upper() == old_col.upper()]
            if matching_cols:
                rename_map[matching_cols[0]] = new_col

        df = df.rename(columns=rename_map)

        # Keep only standard columns that exist
        standard_cols = ["symbol", "series", "open", "high", "low", "close",
                        "volume", "value", "trades", "date", "prev_close", "last", "isin"]
        existing_cols = [c for c in standard_cols if c in df.columns]
        df = df[existing_cols].copy()

        # Ensure numeric types
        numeric_cols = ["open", "high", "low", "close", "volume", "value", "trades", "prev_close", "last"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Parse date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Clean symbol
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].str.strip().str.upper()

        # Clean series
        if "series" in df.columns:
            df["series"] = df["series"].str.strip().str.upper()

        return df

    def fetch_for_date(
        self,
        trade_date: date | str,
        series: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Fetch bhav copy for a specific date.

        Tries new format first, falls back to old format.

        Args:
            trade_date: Date for bhav copy
            series: List of series to include (default: EQ, BE, BZ)

        Returns:
            DataFrame with OHLC data for all equities on that date

        Raises:
            NSEDataNotFoundError: If no data available for the date
        """
        # Parse date
        if isinstance(trade_date, str):
            parsed = parse_date(trade_date)
            if parsed is None:
                raise NSEDataNotFoundError(f"Invalid date format: {trade_date}")
            trade_date = parsed

        # Check if it's a trading day
        if not is_trading_day(trade_date):
            raise NSEDataNotFoundError(
                f"No trading on {trade_date}",
                details="NSE is closed on weekends",
            )

        # Future date check
        if trade_date > date.today():
            raise NSEDataNotFoundError(
                f"Cannot fetch future data for {trade_date}",
            )

        # Try new format first (for recent data)
        try:
            url = self._build_new_url(trade_date)
            df = self._download_and_parse(url, is_new_format=True)
            if not df.empty:
                logger.debug(f"Fetched bhav copy (new format) for {trade_date}")
                return filter_by_series(df, series)
        except (NSEConnectionError, NSEParseError) as e:
            logger.debug(f"New format failed for {trade_date}: {e}")

        # Fall back to old format
        try:
            url = self._build_old_url(trade_date)
            df = self._download_and_parse(url, is_new_format=False)
            if not df.empty:
                logger.debug(f"Fetched bhav copy (old format) for {trade_date}")
                return filter_by_series(df, series)
        except (NSEConnectionError, NSEParseError) as e:
            logger.debug(f"Old format failed for {trade_date}: {e}")

        raise NSEDataNotFoundError(
            f"No bhav copy available for {trade_date}",
            details="This might be a trading holiday or data not yet available",
        )

    def fetch_for_symbol(
        self,
        symbol: str,
        start_date: date | str,
        end_date: date | str,
        series: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Fetch historical data for a specific symbol.

        This method downloads bhav copies for each trading day in the range
        and filters for the requested symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            series: Series to include (default: EQ, BE, BZ)

        Returns:
            DataFrame with OHLC data for the symbol

        Raises:
            NSEDataNotFoundError: If no data found for the symbol
        """
        symbol = symbol.strip().upper()

        # Parse dates
        if isinstance(start_date, str):
            parsed = parse_date(start_date)
            if parsed is None:
                raise NSEDataNotFoundError(f"Invalid start date format: {start_date}")
            start_date = parsed
        if isinstance(end_date, str):
            parsed = parse_date(end_date)
            if parsed is None:
                raise NSEDataNotFoundError(f"Invalid end date format: {end_date}")
            end_date = parsed

        # Validate date range
        start_date, end_date = validate_date_range(start_date, end_date)

        logger.info(f"Fetching {symbol} history from {start_date} to {end_date}")

        # Check cache first
        if self._use_cache and self._cache:
            cached_df = self._cache.get_ohlc(symbol, start_date, end_date)
            if cached_df is not None and not cached_df.empty:
                # Check if we have complete data
                cached_range = self._cache.get_cached_date_range(symbol)
                if cached_range:
                    cache_start, cache_end = cached_range
                    if cache_start <= start_date and cache_end >= end_date:
                        logger.debug(f"Cache hit for {symbol}")
                        return cached_df

        # Fetch data day by day
        all_data = []
        current_date = start_date
        errors = []

        while current_date <= end_date:
            if is_trading_day(current_date):
                try:
                    daily_df = self.fetch_for_date(current_date, series=series)

                    # Filter for symbol
                    symbol_data = daily_df[daily_df["symbol"] == symbol]

                    if not symbol_data.empty:
                        # Add date if not present
                        if "date" not in symbol_data.columns:
                            symbol_data = symbol_data.copy()
                            symbol_data["date"] = current_date
                        all_data.append(symbol_data)

                except NSEDataNotFoundError:
                    # Skip holidays/unavailable dates
                    errors.append(current_date)
                except NSEConnectionError as e:
                    logger.warning(f"Failed to fetch {current_date}: {e}")
                    errors.append(current_date)

            current_date += timedelta(days=1)

        if not all_data:
            raise NSEDataNotFoundError(
                f"No data found for {symbol}",
                symbol=symbol,
                date_range=(str(start_date), str(end_date)),
            )

        # Combine all data
        result_df = pd.concat(all_data, ignore_index=True)

        # Standardize
        result_df = standardize_dataframe(result_df, symbol=symbol)

        # Cache the data
        if self._use_cache and self._cache and not result_df.empty:
            self._cache.set_ohlc(symbol, result_df)

        if errors:
            logger.debug(f"Skipped {len(errors)} dates due to errors/holidays")

        return result_df

    def fetch_bulk(
        self,
        symbols: list[str],
        start_date: date | str,
        end_date: date | str,
        series: list[str] | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols efficiently.

        This method downloads bhav copies once per day and filters for
        all requested symbols, which is more efficient than fetching
        each symbol separately.

        Args:
            symbols: List of stock symbols
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            series: Series to include (default: EQ, BE, BZ)

        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        symbols = [s.strip().upper() for s in symbols]

        # Parse dates
        if isinstance(start_date, str):
            parsed = parse_date(start_date)
            if parsed is None:
                raise NSEDataNotFoundError(f"Invalid start date format: {start_date}")
            start_date = parsed
        if isinstance(end_date, str):
            parsed = parse_date(end_date)
            if parsed is None:
                raise NSEDataNotFoundError(f"Invalid end date format: {end_date}")
            end_date = parsed

        # Validate date range
        start_date, end_date = validate_date_range(start_date, end_date)

        logger.info(f"Bulk fetching {len(symbols)} symbols from {start_date} to {end_date}")

        # Initialize result containers
        symbol_data: dict[str, list[pd.DataFrame]] = {s: [] for s in symbols}

        # Fetch data day by day
        current_date = start_date

        while current_date <= end_date:
            if is_trading_day(current_date):
                try:
                    daily_df = self.fetch_for_date(current_date, series=series)

                    # Filter for each symbol
                    for symbol in symbols:
                        symbol_rows = daily_df[daily_df["symbol"] == symbol]
                        if not symbol_rows.empty:
                            symbol_rows = symbol_rows.copy()
                            if "date" not in symbol_rows.columns:
                                symbol_rows["date"] = current_date
                            symbol_data[symbol].append(symbol_rows)

                except (NSEDataNotFoundError, NSEConnectionError) as e:
                    logger.debug(f"Skipping {current_date}: {e}")

            current_date += timedelta(days=1)

        # Combine and standardize each symbol's data
        results: dict[str, pd.DataFrame] = {}

        for symbol, data_list in symbol_data.items():
            if data_list:
                combined = pd.concat(data_list, ignore_index=True)
                results[symbol] = standardize_dataframe(combined, symbol=symbol)

                # Cache the data
                if self._use_cache and self._cache:
                    self._cache.set_ohlc(symbol, results[symbol])
            else:
                results[symbol] = pd.DataFrame()

        return results

    def get_available_dates(
        self,
        start_date: date | str,
        end_date: date | str,
    ) -> list[date]:
        """
        Get list of dates for which bhav copy is available.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of dates with available data
        """
        # Parse dates
        if isinstance(start_date, str):
            parsed = parse_date(start_date)
            if parsed is None:
                raise NSEDataNotFoundError(f"Invalid start date format: {start_date}")
            start_date = parsed
        if isinstance(end_date, str):
            parsed = parse_date(end_date)
            if parsed is None:
                raise NSEDataNotFoundError(f"Invalid end date format: {end_date}")
            end_date = parsed

        available = []
        current = start_date

        while current <= end_date:
            if is_trading_day(current):
                try:
                    # Try to fetch - if successful, date is available
                    self.fetch_for_date(current)
                    available.append(current)
                except NSEDataNotFoundError:
                    pass
            current += timedelta(days=1)

        return available
