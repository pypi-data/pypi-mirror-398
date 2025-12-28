"""
Ticker class for accessing NSE equity data.

This module provides the main user-facing Ticker class with a
yfinance-inspired API design.

Usage:
    import nsefeed as nf

    # Get historical data
    reliance = nf.Ticker("RELIANCE")
    df = reliance.history(period="1mo")

    # Get company info
    print(reliance.info)

    # Date range query
    df = reliance.history(start="2024-01-01", end="2024-06-30")
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from . import logger
from .cache import NSECache, cached
from .constants import (
    VALID_INTERVALS,
    PERIOD_DAYS,
    NSE_ENDPOINTS,
    PRIMARY_SERIES,
)
from .exceptions import (
    NSEInvalidSymbolError,
    NSEInvalidDateError,
    NSEDataNotFoundError,
)
from .scrapers.bhav_copy import BhavCopyScraper
from .session import NSESession
from .utils import (
    parse_date,
    period_to_dates,
    validate_date_range,
    validate_symbol,
    aggregate_to_weekly,
    aggregate_to_monthly,
)


class Ticker:
    """
    NSE Ticker class for accessing equity data.

    This class provides a clean, yfinance-inspired API for accessing
    NSE equity data including historical OHLC, company information,
    and corporate actions.

    Args:
        symbol: NSE stock symbol (e.g., "RELIANCE", "TCS", "HDFCBANK")

    Usage:
        >>> import nsefeed as nf
        >>> reliance = nf.Ticker("RELIANCE")
        >>> df = reliance.history(period="1mo")
        >>> print(df.head())
                        open     high      low    close    volume
        date
        2024-01-02  2502.00  2515.95  2490.05  2510.35  12345678
        2024-01-03  2515.00  2530.00  2505.00  2525.75   9876543
    """

    def __init__(self, symbol: str) -> None:
        """
        Initialize Ticker with a symbol.

        Args:
            symbol: NSE stock symbol (case-insensitive)

        Raises:
            NSEInvalidSymbolError: If symbol is invalid
        """
        self._symbol = validate_symbol(symbol)
        self._session = NSESession.get_instance()
        self._cache = NSECache()
        self._bhav_scraper = BhavCopyScraper(use_cache=True)
        self._info_cache: dict[str, Any] | None = None

        logger.debug(f"Ticker initialized for {self._symbol}")

    @property
    def symbol(self) -> str:
        """Get the stock symbol."""
        return self._symbol

    def history(
        self,
        period: str = "1mo",
        interval: str = "1d",
        start: str | date | datetime | None = None,
        end: str | date | datetime | None = None,
        auto_adjust: bool = False,
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for the ticker.

        This method fetches historical price data from NSE bhav copies.
        Data is automatically cached locally to reduce server load.

        Args:
            period: Data period. Valid values:
                - "1d", "5d": Days
                - "1mo", "3mo", "6mo": Months
                - "1y", "2y", "5y", "10y": Years
                - "ytd": Year to date
                - "max": Maximum available data
                Ignored if start/end are specified.

            interval: Data interval. Valid values:
                - "1d": Daily (default, from bhav copy)
                - "1wk": Weekly (aggregated from daily)
                - "1mo": Monthly (aggregated from daily)

            start: Start date. Formats: "2024-01-15", "15-01-2024",
                   datetime object, or date object.

            end: End date. Same formats as start.

            auto_adjust: Not yet implemented. Reserved for future
                        corporate action adjustments.

        Returns:
            pandas.DataFrame with columns:
                - date (index): Trading date
                - open: Opening price
                - high: Highest price
                - low: Lowest price
                - close: Closing price
                - volume: Trading volume
                - value: Total traded value (optional)
                - trades: Number of trades (optional)

        Raises:
            NSEInvalidDateError: If dates are invalid
            NSEDataNotFoundError: If no data found for the period

        Examples:
            >>> ticker = Ticker("RELIANCE")

            # Last 1 month
            >>> df = ticker.history(period="1mo")

            # Specific date range
            >>> df = ticker.history(start="2024-01-01", end="2024-06-30")

            # Weekly data
            >>> df = ticker.history(period="3mo", interval="1wk")
        """
        # Validate interval
        interval = interval.lower()
        if interval not in VALID_INTERVALS:
            raise ValueError(
                f"Invalid interval '{interval}'. "
                f"Valid intervals: {', '.join(VALID_INTERVALS)}"
            )

        # Determine date range
        if start is not None or end is not None:
            # Use explicit dates
            start_date = parse_date(start) if start else None
            end_date = parse_date(end) if end else None

            # Ensure end_date has a value
            if end_date is None:
                end_date = date.today()

            if start_date is None:
                # Default to 1 month before end
                start_date = end_date.replace(
                    month=end_date.month - 1 if end_date.month > 1 else 12,
                    year=end_date.year if end_date.month > 1 else end_date.year - 1,
                )
        else:
            # Use period
            start_date, end_date = period_to_dates(period)

        # Validate date range
        start_date, end_date = validate_date_range(start_date, end_date)

        logger.info(
            f"Fetching {self._symbol} history: "
            f"{start_date} to {end_date}, interval={interval}"
        )

        # Fetch data
        df = self._bhav_scraper.fetch_for_symbol(
            self._symbol,
            start_date,
            end_date,
            series=PRIMARY_SERIES,
        )

        if df.empty:
            raise NSEDataNotFoundError(
                f"No data found for {self._symbol}",
                symbol=self._symbol,
                date_range=(str(start_date), str(end_date)),
            )

        # Aggregate if needed
        if interval == "1wk":
            df = aggregate_to_weekly(df)
        elif interval == "1mo":
            df = aggregate_to_monthly(df)

        # Select and order columns for output
        output_cols = ["open", "high", "low", "close", "volume"]
        optional_cols = ["value", "trades"]

        for col in optional_cols:
            if col in df.columns:
                output_cols.append(col)

        return df[[c for c in output_cols if c in df.columns]]

    @property
    def info(self) -> dict[str, Any]:
        """
        Get company information.

        Returns a dictionary containing company metadata including
        symbol, company name, industry, and more.

        Note: This requires accessing the NSE API and may be rate limited.

        Returns:
            Dictionary with company information

        Example:
            >>> ticker = Ticker("RELIANCE")
            >>> print(ticker.info)
            {
                'symbol': 'RELIANCE',
                'companyName': 'Reliance Industries Limited',
                'industry': 'REFINERIES',
                'series': 'EQ',
                ...
            }
        """
        if self._info_cache is not None:
            return self._info_cache

        # Try to get from metadata cache
        cache_key = f"info:{self._symbol}"
        cached_info = self._cache.get_metadata(cache_key)
        if cached_info:
            self._info_cache = cached_info
            return cached_info

        # Fetch from NSE API
        try:
            response = self._session.get_json(
                NSE_ENDPOINTS["quote_equity"],
                params={"symbol": self._symbol},
            )

            # Extract relevant info
            info_data = response.get("info", {})
            price_info = response.get("priceInfo", {})

            self._info_cache = {
                "symbol": self._symbol,
                "companyName": info_data.get("companyName"),
                "industry": info_data.get("industry"),
                "series": info_data.get("activeSeries", []),
                "isin": info_data.get("isin"),
                "faceValue": info_data.get("faceVal"),
                "issuedSize": info_data.get("issuedSize"),
                "listingDate": info_data.get("listingDate"),
                "lastPrice": price_info.get("lastPrice"),
                "change": price_info.get("change"),
                "pChange": price_info.get("pChange"),
                "open": price_info.get("open"),
                "dayHigh": price_info.get("intraDayHighLow", {}).get("max"),
                "dayLow": price_info.get("intraDayHighLow", {}).get("min"),
                "previousClose": price_info.get("previousClose"),
                "weekHigh52": price_info.get("weekHighLow", {}).get("max"),
                "weekLow52": price_info.get("weekHighLow", {}).get("min"),
            }

            # Cache the info
            self._cache.set_metadata(cache_key, self._info_cache, ttl=24 * 3600)

            return self._info_cache

        except Exception as e:
            logger.warning(f"Failed to fetch info for {self._symbol}: {e}")
            return {"symbol": self._symbol, "error": str(e)}

    @property
    def actions(self) -> pd.DataFrame:
        """
        Get corporate actions (dividends, splits, bonuses).

        Returns:
            DataFrame with corporate actions

        Note: This feature is planned for Phase 2.
        """
        logger.warning("Corporate actions not yet implemented (Phase 2 feature)")
        return pd.DataFrame()

    @property
    def major_holders(self) -> pd.DataFrame:
        """
        Get major shareholding pattern.

        Returns:
            DataFrame with shareholding data

        Note: This feature is planned for Phase 2.
        """
        logger.warning("Major holders not yet implemented (Phase 2 feature)")
        return pd.DataFrame()

    def get_ohlc(
        self,
        start: str | date | None = None,
        end: str | date | None = None,
    ) -> pd.DataFrame:
        """
        Convenience method to get OHLC data.

        Equivalent to history() but returns only OHLC columns.

        Args:
            start: Start date
            end: End date (default: today)

        Returns:
            DataFrame with OHLC columns
        """
        df = self.history(start=start, end=end)
        return df[["open", "high", "low", "close"]]

    def __repr__(self) -> str:
        """String representation."""
        return f"Ticker('{self._symbol}')"

    def __str__(self) -> str:
        """String representation."""
        return f"nsefeed.Ticker({self._symbol})"
