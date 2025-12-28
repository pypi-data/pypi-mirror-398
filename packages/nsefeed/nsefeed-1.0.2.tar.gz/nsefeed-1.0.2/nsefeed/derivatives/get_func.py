"""
High-level wrapper functions for derivatives data (nselib-style).

These functions provide a convenient interface to fetch NSE F&O data
with support for periods, date ranges, and automatic chunking.
"""

from __future__ import annotations

from datetime import date as date_type, datetime, timedelta
from typing import TYPE_CHECKING

import pandas as pd

from .. import logger
from ..constants import (
    FUTURE_PRICE_VOLUME_COLUMNS,
    DATE_FORMATS,
)
from ..exceptions import NSEDataNotFoundError
from ..utils import (
    validate_date_param,
    derive_dates,
    chunk_date_range,
)
from .derivative_data import (
    fetch_fo_price_volume_chunk,
    fetch_fno_bhav_copy,
)

if TYPE_CHECKING:
    from datetime import date


def get_future_price_volume_data(
    symbol: str,
    instrument: str,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get contract-wise futures price and volume data.

    Fetches historical data for futures contracts with automatic chunking
    for large date ranges (max 90 days per request recommended).

    Parameters
    ----------
    symbol : str
        NSE symbol (e.g., 'RELIANCE', 'NIFTY', 'BANKNIFTY')
    instrument : str
        Instrument type:
        - 'FUTIDX': Index futures (NIFTY, BANKNIFTY, etc.)
        - 'FUTSTK': Stock futures
    from_date : str | date, optional
        Start date in DD-MM-YYYY format or date object
    to_date : str | date, optional
        End date in DD-MM-YYYY format or date object
    period : str, optional
        Period string ('1d', '5d', '1mo', '3mo', '6mo', '1y')
        Either (from_date, to_date) OR period must be provided

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - TIMESTAMP, INSTRUMENT, SYMBOL, EXPIRY_DT, STRIKE_PRICE, OPTION_TYPE
        - MARKET_TYPE, OPENING_PRICE, TRADE_HIGH_PRICE, TRADE_LOW_PRICE
        - CLOSING_PRICE, LAST_TRADED_PRICE, PREV_CLS, SETTLE_PRICE
        - TOT_TRADED_QTY, TOT_TRADED_VAL, OPEN_INT, CHANGE_IN_OI
        - MARKET_LOT, UNDERLYING_VALUE

    Raises
    ------
    ValueError
        If instrument or date parameters are invalid
    NSEDataNotFoundError
        If data is not available

    Examples
    --------
    >>> import nsefeed as nf
    >>> # Get NIFTY futures data for last 1 month
    >>> df = nf.derivatives.get_future_price_volume_data(
    ...     'NIFTY', 'FUTIDX', period='1mo'
    ... )

    >>> # Get stock futures for specific date range
    >>> df = nf.derivatives.get_future_price_volume_data(
    ...     'RELIANCE', 'FUTSTK', '01-11-2024', '30-11-2024'
    ... )
    """
    # Validate parameters
    validate_date_param(from_date, to_date, period)

    # Clean and validate instrument
    symbol = symbol.strip().upper()
    instrument = instrument.strip().upper()

    if instrument not in ['FUTIDX', 'FUTSTK']:
        raise ValueError(
            f"Invalid instrument: {instrument}. Must be FUTIDX or FUTSTK"
        )

    # Derive dates
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    logger.info(
        f"Fetching futures data for {symbol} ({instrument}) "
        f"from {from_dt} to {to_dt}"
    )

    # Format dates for API
    from_date_str = from_dt.strftime(DATE_FORMATS["api"])
    to_date_str = to_dt.strftime(DATE_FORMATS["api"])

    # Chunk date range (max 90 days per request as per nselib)
    chunks = chunk_date_range(from_dt, to_dt, chunk_days=90)

    # Fetch data for each chunk
    all_dataframes = []

    for chunk_start, chunk_end in chunks:
        chunk_from = chunk_start.strftime(DATE_FORMATS["api"])
        chunk_to = chunk_end.strftime(DATE_FORMATS["api"])

        logger.debug(
            f"Fetching futures chunk: {chunk_from} to {chunk_to}"
        )

        try:
            chunk_df = fetch_fo_price_volume_chunk(
                symbol, instrument, chunk_from, chunk_to
            )

            if not chunk_df.empty:
                all_dataframes.append(chunk_df)

        except NSEDataNotFoundError:
            logger.warning(
                f"No futures data for {symbol} in chunk "
                f"{chunk_from} to {chunk_to}"
            )
            continue

    # Combine all chunks
    if not all_dataframes:
        logger.warning(
            f"No futures data available for {symbol} in the specified date range"
        )
        return pd.DataFrame(columns=FUTURE_PRICE_VOLUME_COLUMNS)

    # Concatenate all data
    result_df = pd.concat(all_dataframes, ignore_index=True)

    # Remove duplicates (if any)
    result_df = result_df.drop_duplicates(
        subset=['TIMESTAMP', 'SYMBOL', 'EXPIRY_DT', 'INSTRUMENT'],
        keep='last'
    )

    logger.info(f"Successfully fetched {len(result_df)} futures rows for {symbol}")

    return result_df


def get_option_price_volume_data(
    symbol: str,
    instrument: str,
    option_type: str | None = None,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get contract-wise options price and volume data.

    Fetches historical data for options contracts with automatic chunking.

    Parameters
    ----------
    symbol : str
        NSE symbol (e.g., 'RELIANCE', 'NIFTY', 'BANKNIFTY')
    instrument : str
        Instrument type:
        - 'OPTIDX': Index options (NIFTY, BANKNIFTY, etc.)
        - 'OPTSTK': Stock options
    option_type : str, optional
        Option type: 'CE' (Call) or 'PE' (Put)
        If None, fetches both CE and PE
    from_date : str | date, optional
        Start date in DD-MM-YYYY format
    to_date : str | date, optional
        End date in DD-MM-YYYY format
    period : str, optional
        Period string

    Returns
    -------
    pd.DataFrame
        DataFrame with options data

    Raises
    ------
    ValueError
        If parameters are invalid
    NSEDataNotFoundError
        If data is not available

    Examples
    --------
    >>> # Get NIFTY call options for last month
    >>> df = nf.derivatives.get_option_price_volume_data(
    ...     'NIFTY', 'OPTIDX', 'CE', period='1mo'
    ... )

    >>> # Get both CE and PE for a stock
    >>> df = nf.derivatives.get_option_price_volume_data(
    ...     'RELIANCE', 'OPTSTK', period='1mo'
    ... )
    """
    # Validate parameters
    validate_date_param(from_date, to_date, period)

    # Clean and validate
    symbol = symbol.strip().upper()
    instrument = instrument.strip().upper()

    if instrument not in ['OPTIDX', 'OPTSTK']:
        raise ValueError(
            f"Invalid instrument: {instrument}. Must be OPTIDX or OPTSTK"
        )

    # Handle option_type
    if option_type:
        option_type = option_type.strip().upper()
        if option_type not in ['CE', 'PE']:
            raise ValueError(
                f"Invalid option_type: {option_type}. Must be CE or PE"
            )
        option_types = [option_type]
    else:
        # Fetch both CE and PE
        option_types = ['CE', 'PE']

    # Derive dates
    from_dt, to_dt = derive_dates(from_date, to_date, period)

    logger.info(
        f"Fetching options data for {symbol} ({instrument}) "
        f"types={option_types} from {from_dt} to {to_dt}"
    )

    # Chunk date range
    chunks = chunk_date_range(from_dt, to_dt, chunk_days=90)

    # Fetch data for each chunk and option type
    all_dataframes = []

    for chunk_start, chunk_end in chunks:
        chunk_from = chunk_start.strftime(DATE_FORMATS["api"])
        chunk_to = chunk_end.strftime(DATE_FORMATS["api"])

        for opt_type in option_types:
            logger.debug(
                f"Fetching options chunk: {chunk_from} to {chunk_to} "
                f"type={opt_type}"
            )

            try:
                chunk_df = fetch_fo_price_volume_chunk(
                    symbol, instrument, chunk_from, chunk_to,
                    option_type=opt_type
                )

                if not chunk_df.empty:
                    all_dataframes.append(chunk_df)

            except NSEDataNotFoundError:
                logger.warning(
                    f"No {opt_type} options data for {symbol} in chunk "
                    f"{chunk_from} to {chunk_to}"
                )
                continue

    # Combine all chunks
    if not all_dataframes:
        logger.warning(
            f"No options data available for {symbol} in the specified date range"
        )
        return pd.DataFrame(columns=FUTURE_PRICE_VOLUME_COLUMNS)

    # Concatenate all data
    result_df = pd.concat(all_dataframes, ignore_index=True)

    # Remove duplicates
    result_df = result_df.drop_duplicates(
        subset=[
            'TIMESTAMP', 'SYMBOL', 'EXPIRY_DT', 'STRIKE_PRICE',
            'OPTION_TYPE', 'INSTRUMENT'
        ],
        keep='last'
    )

    logger.info(
        f"Successfully fetched {len(result_df)} options rows for {symbol}"
    )

    return result_df


def get_fno_bhav_copy(trade_date: str | date) -> pd.DataFrame:
    """
    Get F&O bhav copy for a specific trading date.

    The bhav copy contains end-of-day snapshot of all F&O contracts
    traded on that day.

    Parameters
    ----------
    trade_date : str | date
        Trading date in DD-MM-YYYY format or date object

    Returns
    -------
    pd.DataFrame
        DataFrame with complete F&O bhav copy data including:
        - INSTRUMENT, SYMBOL, EXPIRY_DT, STRIKE_PR, OPTION_TYP
        - OPEN, HIGH, LOW, CLOSE, SETTLE_PR
        - CONTRACTS, VAL_INLAKH, OPEN_INT, CHG_IN_OI
        - TIMESTAMP

    Raises
    ------
    NSEDataNotFoundError
        If bhav copy is not available

    Examples
    --------
    >>> # Get F&O bhav copy for a specific date
    >>> df = nf.derivatives.get_fno_bhav_copy('01-12-2024')
    >>> print(df[['SYMBOL', 'EXPIRY_DT', 'CLOSE', 'OPEN_INT']].head())
    """
    # Convert to date object if string
    if isinstance(trade_date, str):
        trade_dt = datetime.strptime(trade_date, '%d-%m-%Y').date()
    else:
        trade_dt = trade_date

    logger.info(f"Fetching F&O bhav copy for {trade_dt}")

    return fetch_fno_bhav_copy(trade_dt)
