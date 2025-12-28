"""
Utility functions for nsefeed library.

This module provides helper functions for:
- Date parsing and validation
- Symbol validation
- DataFrame operations
- Period to date range conversion
"""

from __future__ import annotations

import re
from datetime import datetime, date, timedelta
from typing import Any, Tuple

import pandas as pd
from dateutil.parser import parse as dateutil_parse
from dateutil.relativedelta import relativedelta

from .constants import PERIOD_DAYS, DATE_FORMATS, PRIMARY_SERIES
from .exceptions import NSEInvalidDateError, NSEInvalidSymbolError


def parse_date(
    date_input: str | datetime | date | None,
    default: date | None = None,
) -> date | None:
    """
    Parse a date from various input formats.

    Supports:
    - ISO format: "2024-01-15"
    - Indian format: "15-01-2024", "15/01/2024"
    - NSE format: "15JAN2024", "15-Jan-2024"
    - datetime objects
    - date objects

    Args:
        date_input: Date in various formats
        default: Default value if input is None

    Returns:
        Parsed date object

    Raises:
        NSEInvalidDateError: If date cannot be parsed
    """
    if date_input is None:
        return default

    if isinstance(date_input, datetime):
        return date_input.date()

    if isinstance(date_input, date):
        return date_input

    if isinstance(date_input, str):
        date_str = date_input.strip()

        # Try common formats
        formats_to_try = [
            "%Y-%m-%d",      # ISO format
            "%d-%m-%Y",      # Indian format
            "%d/%m/%Y",      # Slash format
            "%d%b%Y",        # NSE bhav copy format
            "%d-%b-%Y",      # NSE format with dash
            "%Y%m%d",        # Compact ISO
        ]

        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Fall back to dateutil parser
        try:
            return dateutil_parse(date_str, dayfirst=True).date()
        except (ValueError, TypeError):
            pass

    raise NSEInvalidDateError(
        f"Cannot parse date: '{date_input}'",
        details="Use formats like '2024-01-15', '15-01-2024', or '15JAN2024'",
    )


def format_date(d: date | datetime, format_name: str = "display") -> str:
    """
    Format a date according to NSE conventions.

    Args:
        d: Date to format
        format_name: Format type from DATE_FORMATS

    Returns:
        Formatted date string
    """
    if isinstance(d, datetime):
        d = d.date()

    fmt = DATE_FORMATS.get(format_name, DATE_FORMATS["display"])
    return d.strftime(fmt).upper()


def period_to_dates(period: str) -> tuple[date, date]:
    """
    Convert a period string to start and end dates.

    Args:
        period: Period string like "1mo", "3mo", "1y", "ytd", "max"

    Returns:
        Tuple of (start_date, end_date)

    Raises:
        NSEInvalidDateError: If period is invalid
    """
    period = period.lower()
    end_date = date.today()

    if period not in PERIOD_DAYS:
        raise NSEInvalidDateError(
            f"Invalid period: '{period}'",
            details=f"Valid periods: {', '.join(PERIOD_DAYS.keys())}",
        )

    days = PERIOD_DAYS[period]

    if days == -1:  # ytd
        start_date = date(end_date.year, 1, 1)
    elif days == -2:  # max
        start_date = date(2000, 1, 1)  # NSE data generally available from 2000
    else:
        start_date = end_date - timedelta(days=days)

    return start_date, end_date


def validate_date_range(
    start_date: date,
    end_date: date,
    allow_future: bool = False,
) -> tuple[date, date]:
    """
    Validate a date range.

    Args:
        start_date: Start date
        end_date: End date
        allow_future: Whether to allow future dates

    Returns:
        Validated (start_date, end_date) tuple

    Raises:
        NSEInvalidDateError: If date range is invalid
    """
    today = date.today()

    # Ensure start is before end
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Check for future dates
    if not allow_future:
        if start_date > today:
            raise NSEInvalidDateError(
                "Start date cannot be in the future",
                details=f"Today is {today}, start_date is {start_date}",
            )
        if end_date > today:
            end_date = today

    # Check for dates too far in the past
    min_date = date(1995, 1, 1)  # NSE was established in 1992, data from ~1995
    if start_date < min_date:
        start_date = min_date

    return start_date, end_date


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize an NSE symbol.

    NSE symbols:
    - Are uppercase
    - Can contain letters, numbers, hyphens, and ampersands
    - Cannot be empty
    - Cannot contain spaces (except special cases)

    Args:
        symbol: Stock symbol to validate

    Returns:
        Normalized symbol (uppercase, trimmed)

    Raises:
        NSEInvalidSymbolError: If symbol is invalid
    """
    if not symbol:
        raise NSEInvalidSymbolError(symbol, "Symbol cannot be empty")

    # Normalize
    symbol = symbol.strip().upper()

    # Basic validation
    if len(symbol) > 20:
        raise NSEInvalidSymbolError(symbol, "Symbol too long")

    # Check for valid characters
    if not re.match(r"^[A-Z0-9&\-]+$", symbol):
        raise NSEInvalidSymbolError(
            symbol,
            "Symbol contains invalid characters",
        )

    return symbol


def is_trading_day(d: date) -> bool:
    """
    Check if a date is likely a trading day.

    This is a basic check that excludes weekends.
    For accurate holiday checking, use the NSE holiday calendar.

    Args:
        d: Date to check

    Returns:
        True if likely a trading day
    """
    # Saturday = 5, Sunday = 6
    return d.weekday() < 5


def get_previous_trading_day(d: date) -> date:
    """
    Get the previous likely trading day.

    Skips weekends. For accurate holiday handling, use NSE calendar.

    Args:
        d: Reference date

    Returns:
        Previous trading day
    """
    d = d - timedelta(days=1)
    while not is_trading_day(d):
        d = d - timedelta(days=1)
    return d


def get_trading_days_between(start: date, end: date) -> list[date]:
    """
    Get list of likely trading days between two dates.

    Excludes weekends. Does not account for holidays.

    Args:
        start: Start date (inclusive)
        end: End date (inclusive)

    Returns:
        List of trading days
    """
    days = []
    current = start
    while current <= end:
        if is_trading_day(current):
            days.append(current)
        current += timedelta(days=1)
    return days


def standardize_dataframe(
    df: pd.DataFrame,
    symbol: str | None = None,
) -> pd.DataFrame:
    """
    Standardize a DataFrame to nsefeed format.

    Ensures:
    - Columns are lowercase
    - Date column exists and is datetime
    - OHLCV columns are numeric
    - Index is set to date

    Args:
        df: Input DataFrame
        symbol: Optional symbol to add as column

    Returns:
        Standardized DataFrame
    """
    if df.empty:
        return df

    # Make a copy
    df = df.copy()

    # Lowercase columns
    df.columns = [c.lower() for c in df.columns]

    # Ensure date column
    date_cols = ["date", "timestamp", "trade_date", "traddt"]
    date_col = None
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break

    if date_col:
        df["date"] = pd.to_datetime(df[date_col])
        if date_col != "date":
            df = df.drop(columns=[date_col])
    elif df.index.name in date_cols or isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        df = df.rename(columns={df.columns[0]: "date"})
        df["date"] = pd.to_datetime(df["date"])

    # Ensure numeric columns
    numeric_cols = ["open", "high", "low", "close", "volume", "value", "trades"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add symbol if provided
    if symbol:
        df["symbol"] = symbol.upper()

    # Set index
    if "date" in df.columns:
        df = df.set_index("date")
        df = df.sort_index()

    return df


def filter_by_series(df: pd.DataFrame, series: list[str] | None = None) -> pd.DataFrame:
    """
    Filter DataFrame by series type.

    Args:
        df: DataFrame with 'series' column
        series: List of series to include (default: PRIMARY_SERIES)

    Returns:
        Filtered DataFrame
    """
    if series is None:
        series = PRIMARY_SERIES

    if "series" not in df.columns:
        return df

    series = [s.upper() for s in series]
    return df[df["series"].str.upper().isin(series)]


def aggregate_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily OHLC data to weekly.

    Args:
        df: Daily OHLC DataFrame

    Returns:
        Weekly OHLC DataFrame
    """
    if df.empty:
        return df

    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        if "date" in df.columns:
            df = df.set_index("date")
            df.index = pd.to_datetime(df.index, errors='coerce')

    # Drop rows with NaT (invalid dates) in index
    df = df[df.index.notna()]

    if df.empty:
        return df

    # Resample to weekly (week ending Friday)
    weekly = df.resample("W-FRI").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    # Add value and trades if present
    if "value" in df.columns:
        weekly["value"] = df["value"].resample("W-FRI").sum()
    if "trades" in df.columns:
        weekly["trades"] = df["trades"].resample("W-FRI").sum()

    return weekly


def aggregate_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily OHLC data to monthly.

    Args:
        df: Daily OHLC DataFrame

    Returns:
        Monthly OHLC DataFrame
    """
    if df.empty:
        return df

    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        if "date" in df.columns:
            df = df.set_index("date")
            df.index = pd.to_datetime(df.index, errors='coerce')

    # Drop rows with NaT (invalid dates) in index
    df = df[df.index.notna()]

    if df.empty:
        return df

    # Resample to monthly
    monthly = df.resample("ME").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    # Add value and trades if present
    if "value" in df.columns:
        monthly["value"] = df["value"].resample("ME").sum()
    if "trades" in df.columns:
        monthly["trades"] = df["trades"].resample("ME").sum()

    return monthly


def parse_nse_response_to_dataframe(data: Any) -> pd.DataFrame:
    """
    Parse NSE API response to DataFrame.

    Handles multiple response formats from NSE APIs:
    - Direct list: [{"col1": "val1"}, {"col2": "val2"}]
    - Dict with data key: {"data": [...], "metadata": {...}}
    - Dict with other structure

    Args:
        data: Response data from NSE API

    Returns:
        DataFrame with parsed data, or empty DataFrame if parsing fails
    """
    if data is None:
        return pd.DataFrame()

    # Handle direct list
    if isinstance(data, list):
        if len(data) == 0:
            return pd.DataFrame()
        return pd.DataFrame(data)

    # Handle dict with 'data' key
    if isinstance(data, dict):
        if 'data' in data:
            if isinstance(data['data'], list):
                return pd.DataFrame(data['data'])
        # Try direct dict conversion
        try:
            return pd.DataFrame([data])
        except (ValueError, TypeError):
            return pd.DataFrame()

    return pd.DataFrame()


def parse_nse_response_to_list(data: Any, key: str = 'symbol') -> list[str]:
    """
    Parse NSE API response to list of values.

    Extracts a specific key (default: 'symbol') from NSE API response.

    Args:
        data: Response data from NSE API
        key: Key to extract from each item (default: 'symbol')

    Returns:
        List of values, or empty list if parsing fails
    """
    if data is None:
        return []

    result = []

    # Handle direct list
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and key in item:
                result.append(item[key])
        return result

    # Handle dict with 'data' key
    if isinstance(data, dict) and 'data' in data:
        if isinstance(data['data'], list):
            for item in data['data']:
                if isinstance(item, dict) and key in item:
                    result.append(item[key])
            return result

    return []


# =============================================================================
# nselib-style Utility Functions
# =============================================================================

def cleaning_nse_symbol(symbol: str) -> str:
    """
    Clean and normalize NSE symbol (nselib-style).

    Args:
        symbol: Raw symbol string

    Returns:
        Cleaned and uppercase symbol

    Example:
        >>> cleaning_nse_symbol('  reliance  ')
        'RELIANCE'
        >>> cleaning_nse_symbol('m&m')
        'M&M'
    """
    if not symbol:
        raise NSEInvalidSymbolError(symbol, "Symbol cannot be empty")

    # Strip whitespace and convert to uppercase
    symbol = symbol.strip().upper()

    # Replace common variations
    symbol = symbol.replace(' ', '')  # Remove internal spaces

    return validate_symbol(symbol)


def cleaning_column_name(columns: Any) -> list[str]:
    """
    Clean column names from NSE data (nselib-style).

    Removes special characters and standardizes column names.

    Args:
        columns: Column names (list, Index, or Series)

    Returns:
        List of cleaned column names

    Example:
        >>> cleaning_column_name(['Symbol ', ' Date', 'OPEN PRICE'])
        ['Symbol', 'Date', 'OPENPRICE']
    """
    if isinstance(columns, (list, pd.Index, pd.Series)):
        cleaned = []
        for col in columns:
            # Convert to string and clean
            col_str = str(col).strip()
            # Remove special chars except dot and underscore
            col_str = col_str.replace(' ', '')
            cleaned.append(col_str)
        return cleaned
    return [str(columns)]


def validate_date_param(
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> None:
    """
    Validate date parameters (nselib-style).

    Ensures that either (from_date + to_date) OR period is provided, not both.

    Args:
        from_date: Start date
        to_date: End date
        period: Period string ('1D', '1W', '1M', '3M', '6M', '1Y')

    Raises:
        NSEInvalidDateError: If parameters are invalid

    Example:
        >>> validate_date_param(from_date='01-01-2024', to_date='31-01-2024')  # OK
        >>> validate_date_param(period='1M')  # OK
        >>> validate_date_param(from_date='01-01-2024', period='1M')  # ERROR
    """
    has_dates = from_date is not None or to_date is not None
    has_period = period is not None

    if not has_dates and not has_period:
        raise NSEInvalidDateError(
            "Either provide (from_date, to_date) or period",
            details="Example: from_date='01-01-2024', to_date='31-01-2024' OR period='1M'"
        )

    if has_dates and has_period:
        raise NSEInvalidDateError(
            "Cannot provide both (from_date, to_date) and period",
            details="Choose either date range or period, not both"
        )

    # If dates provided, both must be provided
    if has_dates and (from_date is None or to_date is None):
        raise NSEInvalidDateError(
            "Both from_date and to_date must be provided",
            details="If using dates, provide both from_date and to_date"
        )

    # Validate period format (case-insensitive)
    if has_period:
        valid_periods = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y', '5Y', '10Y']
        # Normalize to uppercase for comparison
        period_upper = period.upper() if isinstance(period, str) else period
        if period_upper not in valid_periods:
            raise NSEInvalidDateError(
                f"Invalid period: '{period}'",
                details=f"Valid periods: {', '.join(valid_periods)} (case-insensitive)"
            )


def derive_from_and_to_date(
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> tuple[str, str]:
    """
    Derive from_date and to_date from period or date range (nselib-style).

    Args:
        from_date: Start date (DD-MM-YYYY or date object)
        to_date: End date (DD-MM-YYYY or date object)
        period: Period string ('1D', '1W', '1M', '3M', '6M', '1Y')

    Returns:
        Tuple of (from_date_str, to_date_str) in DD-MM-YYYY format

    Example:
        >>> derive_from_and_to_date(period='1M')
        ('01-11-2024', '01-12-2024')  # Approximate
        >>> derive_from_and_to_date(from_date='01-01-2024', to_date='31-01-2024')
        ('01-01-2024', '31-01-2024')
    """
    # If period provided, calculate dates
    if period:
        # Normalize period to uppercase for consistency
        period = period.upper() if isinstance(period, str) else period

        end_date = date.today()

        # Map periods to days/months
        period_map = {
            '1D': timedelta(days=1),
            '1W': timedelta(weeks=1),
            '1M': relativedelta(months=1),
            '3M': relativedelta(months=3),
            '6M': relativedelta(months=6),
            '1Y': relativedelta(years=1),
            '2Y': relativedelta(years=2),
            '5Y': relativedelta(years=5),
            '10Y': relativedelta(years=10),
        }

        delta = period_map.get(period)
        if delta is None:
            raise NSEInvalidDateError(f"Unsupported period: {period}")

        if isinstance(delta, relativedelta):
            start_date = end_date - delta
        else:
            start_date = end_date - delta

        # Format as DD-MM-YYYY
        from_date_str = start_date.strftime('%d-%m-%Y')
        to_date_str = end_date.strftime('%d-%m-%Y')

        return from_date_str, to_date_str

    # If dates provided, normalize them
    if from_date and to_date:
        # Parse dates if string
        if isinstance(from_date, str):
            # Try DD-MM-YYYY format first
            try:
                from_dt = datetime.strptime(from_date, '%d-%m-%Y').date()
            except ValueError:
                from_dt = parse_date(from_date)
        else:
            from_dt = from_date if isinstance(from_date, date) else from_date.date()

        if isinstance(to_date, str):
            try:
                to_dt = datetime.strptime(to_date, '%d-%m-%Y').date()
            except ValueError:
                to_dt = parse_date(to_date)
        else:
            to_dt = to_date if isinstance(to_date, date) else to_date.date()

        # Validate and return in DD-MM-YYYY format
        from_dt, to_dt = validate_date_range(from_dt, to_dt, allow_future=False)

        return from_dt.strftime('%d-%m-%Y'), to_dt.strftime('%d-%m-%Y')

    raise NSEInvalidDateError("Must provide either period or from_date/to_date")


def convert_numeric_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Convert string columns with commas to numeric (nselib-style).

    NSE data often has numbers formatted with commas (e.g., "1,234,567").
    This function cleans and converts them to proper numeric types.

    Args:
        df: DataFrame to convert
        columns: List of column names to convert

    Returns:
        DataFrame with numeric columns

    Example:
        >>> df = pd.DataFrame({'Volume': ['1,234,567', '2,345,678']})
        >>> df = convert_numeric_columns(df, ['Volume'])
        >>> df['Volume'].dtype
        dtype('int64')
    """
    if df.empty:
        return df

    df = df.copy()

    for col in columns:
        if col in df.columns:
            # Remove commas and convert to numeric
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', ''),
                errors='coerce'
            )

    return df


def chunk_date_range(
    start_date: date,
    end_date: date,
    chunk_days: int = 365,
) -> list[tuple[date, date]]:
    """
    Split a date range into chunks (nselib-style).

    NSE APIs often have limits on date range (e.g., max 365 days).
    This function splits large ranges into manageable chunks.

    Args:
        start_date: Start date
        end_date: End date
        chunk_days: Maximum days per chunk (default: 365)

    Returns:
        List of (chunk_start, chunk_end) tuples

    Example:
        >>> start = date(2023, 1, 1)
        >>> end = date(2024, 6, 1)
        >>> chunks = chunk_date_range(start, end, chunk_days=365)
        >>> len(chunks)
        2
    """
    chunks = []
    current_start = start_date

    while current_start <= end_date:
        # Calculate chunk end (min of chunk_days ahead or end_date)
        chunk_end = min(
            current_start + timedelta(days=chunk_days - 1),
            end_date
        )

        chunks.append((current_start, chunk_end))

        # Move to next chunk
        current_start = chunk_end + timedelta(days=1)

    return chunks


def derive_dates(
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> tuple[date, date]:
    """
    Derive from_date and to_date as date objects (nselib-style).
    
    Similar to derive_from_and_to_date but returns date objects instead of strings.
    Handles '1M', '1Y' style periods.
    """
    if period:
        end_date = date.today()

        # Map periods to days/months (same as derive_from_and_to_date)
        period_map = {
            '1D': timedelta(days=1),
            '1W': timedelta(weeks=1),
            '1M': relativedelta(months=1),
            '3M': relativedelta(months=3),
            '6M': relativedelta(months=6),
            '1Y': relativedelta(years=1),
            '2Y': relativedelta(years=2),
            '5Y': relativedelta(years=5),
            '10Y': relativedelta(years=10),
        }

        delta = period_map.get(period)
        if delta is None:
            # Try lowercase lookup if uppercase failed (fallback)
            delta = period_map.get(period.upper())
            
        if delta is None:
             # Try PERIOD_DAYS for compatibility
            try:
                # period_to_dates returns (start, end)
                return period_to_dates(period)
            except NSEInvalidDateError:
                raise NSEInvalidDateError(f"Unsupported period: {period}")

        start_date = end_date - delta
        return start_date, end_date

    if from_date and to_date:
        # Parse if strings
        if isinstance(from_date, str):
            from_dt = parse_date(from_date)
        else:
            from_dt = from_date.date() if isinstance(from_date, datetime) else from_date

        if isinstance(to_date, str):
            to_dt = parse_date(to_date)
        else:
            to_dt = to_date.date() if isinstance(to_date, datetime) else to_date

        # Validate
        return validate_date_range(from_dt, to_dt, allow_future=False)

    raise NSEInvalidDateError("Must provide either period or from_date/to_date")
