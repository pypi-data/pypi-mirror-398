"""
Core equity data fetching functions for NSE India.

All functions are CSV-based and fetch historical data from NSE archives.
This module provides low-level data fetching, while get_func.py provides
convenient wrapper functions following nselib pattern.
"""

from __future__ import annotations

from datetime import date as date_type, datetime
from io import BytesIO
from typing import TYPE_CHECKING

import pandas as pd

from .. import logger
from ..constants import (
    CSV_ENDPOINTS,
    PRICE_VOLUME_DELIVERABLE_COLUMNS,
    PRICE_VOLUME_COLUMNS,
    DELIVERABLE_COLUMNS,
    BULK_DEAL_COLUMNS,
    BLOCK_DEAL_COLUMNS,
    SHORT_SELLING_COLUMNS,
    DATE_FORMATS,
)
from ..exceptions import NSEDataNotFoundError, NSEConnectionError
from ..session import NSESession
from ..utils import (
    cleaning_column_name,
    validate_date_param,
    derive_from_and_to_date,
    chunk_date_range,
)

if TYPE_CHECKING:
    from datetime import date


def fetch_price_volume_deliverable_chunk(
    symbol: str,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    """
    Fetch price, volume, and deliverable data for a single date range chunk.

    This is an internal function used by get_price_volume_and_deliverable_position_data()
    to handle chunked requests (NSE has a 365-day limit per request).

    Parameters
    ----------
    symbol : str
        NSE symbol (should be already cleaned/validated)
    from_date : str
        Start date in DD-MM-YYYY format
    to_date : str
        End date in DD-MM-YYYY format

    Returns
    -------
    pd.DataFrame
        DataFrame with price, volume, and delivery data

    Raises
    ------
    NSEDataNotFoundError
        If data is not available for the date range
    """
    session = NSESession()

    try:
        endpoint = CSV_ENDPOINTS["equity_deliverable"]

        params = {
            "from": from_date,
            "to": to_date,
            "symbol": symbol,
            "type": "priceVolumeDeliverable",
            "series": "ALL",
            "csv": "true"
        }

        response = session.get(
            url=endpoint["url"],
            headers={"Referer": endpoint["origin"]},
            params=params
        )

        if response.status_code != 200:
            raise NSEDataNotFoundError(
                f"Failed to fetch data for {symbol}. Status: {response.status_code}"
            )

        # Parse CSV
        df = pd.read_csv(BytesIO(response.content))

        if df.empty:
            raise NSEDataNotFoundError(
                f"No data available for {symbol} from {from_date} to {to_date}"
            )

        # Clean column names (remove spaces)
        df.columns = [name.replace(' ', '') for name in df.columns]

        return df

    except NSEConnectionError as e:
        raise NSEDataNotFoundError(
            f"Price/volume/deliverable data not available for {symbol}",
            details=f"Date range: {from_date} to {to_date} | Error: {str(e)}"
        ) from e


def fetch_price_volume_chunk(
    symbol: str,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    """
    Fetch price and volume data (without delivery) for a single date range chunk.

    Parameters
    ----------
    symbol : str
        NSE symbol
    from_date : str
        Start date in DD-MM-YYYY format
    to_date : str
        End date in DD-MM-YYYY format

    Returns
    -------
    pd.DataFrame
        DataFrame with price and volume data

    Raises
    ------
    NSEDataNotFoundError
        If data is not available
    """
    session = NSESession()

    try:
        endpoint = CSV_ENDPOINTS["equity_deliverable"]

        params = {
            "from": from_date,
            "to": to_date,
            "symbol": symbol,
            "type": "priceVolume",
            "series": "ALL",
            "csv": "true"
        }

        response = session.get(
            url=endpoint["url"],
            headers={"Referer": endpoint["origin"]},
            params=params
        )

        if response.status_code != 200:
            raise NSEDataNotFoundError(
                f"Failed to fetch price/volume data for {symbol}"
            )

        df = pd.read_csv(BytesIO(response.content))

        if df.empty:
            raise NSEDataNotFoundError(
                f"No price/volume data for {symbol} from {from_date} to {to_date}"
            )

        df.columns = [name.replace(' ', '') for name in df.columns]

        return df

    except NSEConnectionError as e:
        raise NSEDataNotFoundError(
            f"Price/volume data not available for {symbol}: {e}"
        ) from e


def fetch_deliverable_chunk(
    symbol: str,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    """
    Fetch deliverable position data only for a single date range chunk.

    Parameters
    ----------
    symbol : str
        NSE symbol
    from_date : str
        Start date in DD-MM-YYYY format
    to_date : str
        End date in DD-MM-YYYY format

    Returns
    -------
    pd.DataFrame
        DataFrame with deliverable position data

    Raises
    ------
    NSEDataNotFoundError
        If data is not available
    """
    session = NSESession()

    try:
        endpoint = CSV_ENDPOINTS["equity_deliverable"]

        params = {
            "from": from_date,
            "to": to_date,
            "symbol": symbol,
            "type": "deliverable",
            "series": "ALL",
            "csv": "true"
        }

        response = session.get(
            url=endpoint["url"],
            headers={"Referer": endpoint["origin"]},
            params=params
        )

        if response.status_code != 200:
            raise NSEDataNotFoundError(
                f"Failed to fetch deliverable data for {symbol}"
            )

        df = pd.read_csv(BytesIO(response.content))

        if df.empty:
            raise NSEDataNotFoundError(
                f"No deliverable data for {symbol} from {from_date} to {to_date}"
            )

        df.columns = [name.replace(' ', '') for name in df.columns]

        return df

    except NSEConnectionError as e:
        raise NSEDataNotFoundError(
            f"Deliverable data not available for {symbol}: {e}"
        ) from e


def fetch_bulk_deals(from_date: str, to_date: str) -> pd.DataFrame:
    """
    Fetch bulk deal data for a date range.

    Bulk deals are trades where total quantity exceeds 0.5% of equity shares.

    Parameters
    ----------
    from_date : str
        Start date in DD-MM-YYYY format
    to_date : str
        End date in DD-MM-YYYY format

    Returns
    -------
    pd.DataFrame
        DataFrame with bulk deal transactions

    Raises
    ------
    NSEDataNotFoundError
        If data is not available
    """
    session = NSESession()

    try:
        endpoint = CSV_ENDPOINTS["bulk_deals"]

        params = {
            "from": from_date,
            "to": to_date,
            "optionType": "bulk_deals",
            "csv": "true"
        }

        response = session.get(
            url=endpoint["url"],
            headers={"Referer": endpoint["origin"]},
            params=params
        )

        if response.status_code != 200:
            raise NSEDataNotFoundError(
                f"Failed to fetch bulk deals. Status: {response.status_code}"
            )

        df = pd.read_csv(BytesIO(response.content))
        df.columns = [name.replace(' ', '') for name in df.columns]

        return df

    except NSEConnectionError as e:
        raise NSEDataNotFoundError(
            f"Bulk deals data not available: {e}"
        ) from e


def fetch_block_deals(from_date: str, to_date: str) -> pd.DataFrame:
    """
    Fetch block deal data for a date range.

    Block deals are large single transactions negotiated outside normal market.

    Parameters
    ----------
    from_date : str
        Start date in DD-MM-YYYY format
    to_date : str
        End date in DD-MM-YYYY format

    Returns
    -------
    pd.DataFrame
        DataFrame with block deal transactions

    Raises
    ------
    NSEDataNotFoundError
        If data is not available
    """
    session = NSESession()

    try:
        endpoint = CSV_ENDPOINTS["block_deals"]

        params = {
            "from": from_date,
            "to": to_date,
            "optionType": "block_deals",
            "csv": "true"
        }

        response = session.get(
            url=endpoint["url"],
            headers={"Referer": endpoint["origin"]},
            params=params
        )

        if response.status_code != 200:
            raise NSEDataNotFoundError(
                f"Failed to fetch block deals. Status: {response.status_code}"
            )

        df = pd.read_csv(BytesIO(response.content))
        df.columns = [name.replace(' ', '') for name in df.columns]

        return df

    except NSEConnectionError as e:
        raise NSEDataNotFoundError(
            f"Block deals data not available: {e}"
        ) from e


def fetch_short_selling(from_date: str, to_date: str) -> pd.DataFrame:
    """
    Fetch short selling data for a date range.

    Parameters
    ----------
    from_date : str
        Start date in DD-MM-YYYY format
    to_date : str
        End date in DD-MM-YYYY format

    Returns
    -------
    pd.DataFrame
        DataFrame with short selling positions

    Raises
    ------
    NSEDataNotFoundError
        If data is not available
    """
    session = NSESession()

    try:
        endpoint = CSV_ENDPOINTS["short_selling"]

        params = {
            "from": from_date,
            "to": to_date,
            "optionType": "short_selling",
            "csv": "true"
        }

        response = session.get(
            url=endpoint["url"],
            headers={"Referer": endpoint["origin"]},
            params=params
        )

        if response.status_code != 200:
            raise NSEDataNotFoundError(
                f"Failed to fetch short selling data. Status: {response.status_code}"
            )

        df = pd.read_csv(BytesIO(response.content))
        df.columns = [name.replace(' ', '') for name in df.columns]

        return df

    except NSEConnectionError as e:
        raise NSEDataNotFoundError(
            f"Short selling data not available: {e}"
        ) from e
