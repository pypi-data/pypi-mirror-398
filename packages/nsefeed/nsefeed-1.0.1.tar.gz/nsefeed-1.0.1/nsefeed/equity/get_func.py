"""
High-level wrapper functions for equity data (nselib-style).

These functions provide a convenient interface to fetch NSE equity data
with support for periods, date ranges, and automatic chunking.
"""

from __future__ import annotations

from datetime import date as date_type, datetime
from typing import TYPE_CHECKING

import pandas as pd

from .. import logger
from ..constants import (
    PRICE_VOLUME_DELIVERABLE_COLUMNS,
    PRICE_VOLUME_COLUMNS,
    DELIVERABLE_COLUMNS,
    DATE_FORMATS,
)
from ..exceptions import NSEDataNotFoundError
from ..utils import (
    validate_date_param,
    derive_dates,
    chunk_date_range,
    convert_numeric_columns,
)
from .equity_data import (
    fetch_price_volume_deliverable_chunk,
    fetch_price_volume_chunk,
    fetch_deliverable_chunk,
    fetch_bulk_deals,
    fetch_block_deals,
    fetch_short_selling,
)

if TYPE_CHECKING:
    from datetime import date


def get_price_volume_and_deliverable_position_data(
    symbol: str,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get security-wise price, volume, and deliverable position data.

    This function fetches comprehensive equity data including OHLC, volume, turnover,
    and delivery data. It automatically chunks large date ranges (max 365 days per request).

    Parameters
    ----------
    symbol : str
        NSE symbol (e.g., 'SBIN', 'RELIANCE')
    from_date : str | date, optional
        Start date in DD-MM-YYYY format or date object
    to_date : str | date, optional
        End date in DD-MM-YYYY format or date object
    period : str, optional
        Period string ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y')
        Either (from_date, to_date) OR period must be provided

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: Symbol, Series, Date, PrevClose, OpenPrice, HighPrice,
        LowPrice, LastPrice, ClosePrice, AveragePrice, TotalTradedQuantity,
        TurnoverInRs, No.ofTrades, DeliverableQty, %DlyQttoTradedQty

    Raises
    ------
    ValueError
        If date parameters are invalid
    NSEDataNotFoundError
        If data is not available

    Examples
    --------
    >>> import nsefeed as nf
    >>> # Using period
    >>> df = nf.equity.get_price_volume_and_deliverable_position_data('SBIN', period='1mo')

    >>> # Using date range
    >>> df = nf.equity.get_price_volume_and_deliverable_position_data(
    ...     'RELIANCE', '01-11-2024', '30-11-2024'
    ... )
    """
    # Validate and derive dates (returns date objects)
    validate_date_param(from_date, to_date, period)
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    # Clean symbol (uppercase, remove spaces)
    symbol = symbol.strip().upper()


    logger.info(
        f"Fetching price/volume/deliverable data for {symbol} "
        f"from {from_dt} to {to_dt}"
    )

    # Chunk date range (max 365 days per request)
    chunks = chunk_date_range(from_dt, to_dt, chunk_days=365)

    # Fetch data for each chunk
    all_dataframes = []

    for chunk_start, chunk_end in chunks:
        chunk_from = chunk_start.strftime(DATE_FORMATS["api"])
        chunk_to = chunk_end.strftime(DATE_FORMATS["api"])

        logger.debug(f"Fetching chunk: {chunk_from} to {chunk_to}")

        try:
            chunk_df = fetch_price_volume_deliverable_chunk(
                symbol, chunk_from, chunk_to
            )

            if not chunk_df.empty:
                all_dataframes.append(chunk_df)

        except NSEDataNotFoundError:
            logger.warning(
                f"No data found for {symbol} in chunk {chunk_from} to {chunk_to}"
            )
            continue

    # Combine all chunks
    if not all_dataframes:
        logger.warning(
            f"No data available for {symbol} in the specified date range"
        )
        return pd.DataFrame(columns=PRICE_VOLUME_DELIVERABLE_COLUMNS)

    # Concatenate all data
    result_df = pd.concat(all_dataframes, ignore_index=True)

    # Remove duplicates (if any)
    result_df = result_df.drop_duplicates(
        subset=['Date', 'Symbol', 'Series'], keep='last'
    )

    # Convert numeric columns
    numeric_cols = [
        'TotalTradedQuantity', 'TurnoverInRs', 'No.ofTrades', 'DeliverableQty'
    ]
    result_df = convert_numeric_columns(result_df, numeric_cols)

    logger.info(f"Successfully fetched {len(result_df)} rows for {symbol}")

    return result_df


def get_price_volume_data(
    symbol: str,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get security-wise price and volume data (without delivery).

    Parameters
    ----------
    symbol : str
        NSE symbol
    from_date : str | date, optional
        Start date in DD-MM-YYYY format
    to_date : str | date, optional
        End date in DD-MM-YYYY format
    period : str, optional
        Period string

    Returns
    -------
    pd.DataFrame
        DataFrame with price and volume data

    Examples
    --------
    >>> df = nf.equity.get_price_volume_data('TCS', period='1mo')
    """
    validate_date_param(from_date, to_date, period)
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    symbol = symbol.strip().upper()

    # Chunk and fetch
    chunks = chunk_date_range(from_dt, to_dt, chunk_days=365)
    all_dataframes = []

    for chunk_start, chunk_end in chunks:
        chunk_from = chunk_start.strftime(DATE_FORMATS["api"])
        chunk_to = chunk_end.strftime(DATE_FORMATS["api"])

        try:
            chunk_df = fetch_price_volume_chunk(symbol, chunk_from, chunk_to)
            if not chunk_df.empty:
                all_dataframes.append(chunk_df)
        except NSEDataNotFoundError:
            continue

    if not all_dataframes:
        return pd.DataFrame(columns=PRICE_VOLUME_COLUMNS)

    result_df = pd.concat(all_dataframes, ignore_index=True)
    result_df = result_df.drop_duplicates(
        subset=['Date', 'Symbol', 'Series'], keep='last'
    )

    return result_df


def get_deliverable_position_data(
    symbol: str,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get deliverable position data only.

    Parameters
    ----------
    symbol : str
        NSE symbol
    from_date : str | date, optional
        Start date in DD-MM-YYYY format
    to_date : str | date, optional
        End date in DD-MM-YYYY format
    period : str, optional
        Period string

    Returns
    -------
    pd.DataFrame
        DataFrame with deliverable position data

    Examples
    --------
    >>> df = nf.equity.get_deliverable_position_data('INFY', period='1mo')
    """
    validate_date_param(from_date, to_date, period)
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    symbol = symbol.strip().upper()

    # Chunk and fetch
    chunks = chunk_date_range(from_dt, to_dt, chunk_days=365)
    all_dataframes = []

    for chunk_start, chunk_end in chunks:
        chunk_from = chunk_start.strftime(DATE_FORMATS["api"])
        chunk_to = chunk_end.strftime(DATE_FORMATS["api"])

        try:
            chunk_df = fetch_deliverable_chunk(symbol, chunk_from, chunk_to)
            if not chunk_df.empty:
                all_dataframes.append(chunk_df)
        except NSEDataNotFoundError:
            continue

    if not all_dataframes:
        return pd.DataFrame(columns=DELIVERABLE_COLUMNS)

    result_df = pd.concat(all_dataframes, ignore_index=True)
    result_df = result_df.drop_duplicates(
        subset=['Date', 'Symbol', 'Series'], keep='last'
    )

    return result_df


def get_bulk_deal_data(
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get bulk deal data.

    Bulk deals are trades where total quantity exceeds 0.5% of equity shares.

    Parameters
    ----------
    from_date : str | date, optional
        Start date in DD-MM-YYYY format
    to_date : str | date, optional
        End date in DD-MM-YYYY format
    period : str, optional
        Period string

    Returns
    -------
    pd.DataFrame
        DataFrame with bulk deal transactions

    Examples
    --------
    >>> df = nf.equity.get_bulk_deal_data(period='1mo')
    >>> print(df[['Symbol', 'ClientName', 'Buy/Sell', 'QuantityTraded']])
    """
    validate_date_param(from_date, to_date, period)
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    from_date_str = from_dt.strftime(DATE_FORMATS["api"])
    to_date_str = to_dt.strftime(DATE_FORMATS["api"])

    logger.info(f"Fetching bulk deals from {from_date_str} to {to_date_str}")

    return fetch_bulk_deals(from_date_str, to_date_str)


def get_block_deals_data(
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get block deal data.

    Block deals are large single transactions negotiated outside normal market.

    Parameters
    ----------
    from_date : str | date, optional
        Start date in DD-MM-YYYY format
    to_date : str | date, optional
        End date in DD-MM-YYYY format
    period : str, optional
        Period string

    Returns
    -------
    pd.DataFrame
        DataFrame with block deal transactions

    Examples
    --------
    >>> df = nf.equity.get_block_deals_data(period='1mo')
    >>> print(df[['Symbol', 'ClientName', 'QuantityTraded']])
    """
    validate_date_param(from_date, to_date, period)
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    from_date_str = from_dt.strftime(DATE_FORMATS["api"])
    to_date_str = to_dt.strftime(DATE_FORMATS["api"])

    logger.info(f"Fetching block deals from {from_date_str} to {to_date_str}")

    return fetch_block_deals(from_date_str, to_date_str)


def get_short_selling_data(
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get short selling data.

    Parameters
    ----------
    from_date : str | date, optional
        Start date in DD-MM-YYYY format
    to_date : str | date, optional
        End date in DD-MM-YYYY format
    period : str, optional
        Period string

    Returns
    -------
    pd.DataFrame
        DataFrame with short selling positions

    Examples
    --------
    >>> df = nf.equity.get_short_selling_data(period='1mo')
    >>> print(df[['Symbol', 'SecurityName', 'Quantity']])
    """
    validate_date_param(from_date, to_date, period)
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    from_date_str = from_dt.strftime(DATE_FORMATS["api"])
    to_date_str = to_dt.strftime(DATE_FORMATS["api"])

    logger.info(f"Fetching short selling data from {from_date_str} to {to_date_str}")

    return fetch_short_selling(from_date_str, to_date_str)
