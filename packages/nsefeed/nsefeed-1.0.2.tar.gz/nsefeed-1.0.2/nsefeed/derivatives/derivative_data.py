"""
Core derivatives data fetching functions for NSE India.

All functions fetch historical F&O data from NSE archives.
This module provides low-level data fetching, while get_func.py provides
convenient wrapper functions following nselib pattern.
"""

from __future__ import annotations

from datetime import date as date_type
from io import BytesIO
from typing import TYPE_CHECKING
import zipfile

import pandas as pd

from .. import logger
from ..constants import (
    CSV_ENDPOINTS,
    FUTURE_PRICE_VOLUME_COLUMNS,
    DATE_FORMATS,
)
from ..exceptions import NSEDataNotFoundError, NSEConnectionError
from ..session import NSESession
from ..utils import cleaning_column_name

if TYPE_CHECKING:
    from datetime import date


def fetch_fo_price_volume_chunk(
    symbol: str,
    instrument: str,
    from_date: str,
    to_date: str,
    option_type: str | None = None,
) -> pd.DataFrame:
    """
    Fetch F&O price and volume data for a single date range chunk.

    This internal function fetches futures or options historical data
    from NSE's foCPV API endpoint.

    Parameters
    ----------
    symbol : str
        NSE symbol (e.g., 'RELIANCE', 'NIFTY', 'BANKNIFTY')
    instrument : str
        Instrument type: 'FUTIDX', 'FUTSTK', 'OPTIDX', 'OPTSTK'
    from_date : str
        Start date in DD-MM-YYYY format
    to_date : str
        End date in DD-MM-YYYY format
    option_type : str, optional
        Option type: 'CE' or 'PE' (required for OPTIDX/OPTSTK)

    Returns
    -------
    pd.DataFrame
        DataFrame with F&O price, volume, and OI data

    Raises
    ------
    NSEDataNotFoundError
        If data is not available
    ValueError
        If parameters are invalid
    """
    # Validate instrument
    valid_instruments = ['FUTIDX', 'FUTSTK', 'OPTIDX', 'OPTSTK']
    if instrument.upper() not in valid_instruments:
        raise ValueError(
            f"Invalid instrument: {instrument}. "
            f"Valid instruments: {valid_instruments}"
        )

    # Validate option_type for options
    if instrument.upper() in ['OPTIDX', 'OPTSTK']:
        if not option_type:
            raise ValueError(
                f"option_type (CE/PE) is required for {instrument}"
            )
        if option_type.upper() not in ['CE', 'PE']:
            raise ValueError(
                f"Invalid option_type: {option_type}. Must be CE or PE"
            )

    session = NSESession()

    try:
        endpoint = CSV_ENDPOINTS["fo_cpv"]

        params = {
            "from": from_date,
            "to": to_date,
            "instrumentType": instrument.upper(),
            "symbol": symbol.upper(),
            "csv": "true"
        }

        # Add option type for options
        if option_type:
            params["optionType"] = option_type.upper()

        response = session.get(
            url=endpoint["url"],
            headers={"Referer": endpoint["origin"]},
            params=params
        )

        # Parse JSON response (foCPV returns JSON, not CSV)
        data_json = response.json()

        if not data_json or 'data' not in data_json:
            raise NSEDataNotFoundError(
                f"No F&O data available for {symbol} ({instrument})"
            )

        df = pd.DataFrame(data_json['data'])

        if df.empty:
            raise NSEDataNotFoundError(
                f"No F&O data for {symbol} from {from_date} to {to_date}"
            )

        # Drop TIMESTAMP column if it exists
        df = df.drop(columns=['TIMESTAMP'], errors='ignore')

        # Clean column names
        df.columns = cleaning_column_name(df.columns)

        return df[FUTURE_PRICE_VOLUME_COLUMNS]

    except NSEConnectionError as e:
        raise NSEDataNotFoundError(
            f"F&O data not available for {symbol}: {e}"
        ) from e


def fetch_fno_bhav_copy(trade_date: date) -> pd.DataFrame:
    """
    Fetch F&O bhav copy for a specific trading date.

    The bhav copy contains end-of-day snapshot of all F&O contracts.

    Parameters
    ----------
    trade_date : date
        Trading date

    Returns
    -------
    pd.DataFrame
        DataFrame with complete F&O bhav copy data

    Raises
    ------
    NSEDataNotFoundError
        If bhav copy is not available for the date
    """
    session = NSESession()

    # Format date for URL
    date_str = trade_date.strftime('%Y%m%d')

    # Try new archives first
    url = (
        f"https://nsearchives.nseindia.com/content/fo/"
        f"BhavCopy_NSE_FO_0_0_0_{date_str}_F_0000.csv.zip"
    )

    try:
        response = session.get(url)

        if response.status_code == 200:
            # Extract CSV from zip
            zip_file = zipfile.ZipFile(BytesIO(response.content), 'r')

            for file_name in zip_file.filelist:
                if file_name.filename.endswith('.csv'):
                    df = pd.read_csv(zip_file.open(file_name))
                    return df

            raise NSEDataNotFoundError(
                f"No CSV file found in bhav copy zip for {trade_date}"
            )

        # Try alternative API endpoint if archive fails
        elif response.status_code == 403:
            date_alt = trade_date.strftime('%d-%b-%Y')
            url_alt = (
                f"https://www.nseindia.com/api/reports?archives="
                "%5B%7B%22name%22%3A%22F%26O%20-%20Bhavcopy(csv)%22%2C%22type%22%3A%22archives%22%2C%22category%22"
                f"%3A%22derivatives%22%2C%22section%22%3A%22equity%22%7D%5D&date={date_alt}"
                "&type=equity&mode=single"
            )

            response_alt = session.get(url_alt)

            if response_alt.status_code == 200:
                zip_file = zipfile.ZipFile(BytesIO(response_alt.content), 'r')

                for file_name in zip_file.filelist:
                    if file_name.filename.endswith('.csv'):
                        df = pd.read_csv(zip_file.open(file_name))
                        return df

            raise NSEDataNotFoundError(
                f"F&O bhav copy not available for {trade_date}"
            )

        else:
            raise NSEDataNotFoundError(
                f"F&O bhav copy not found for {trade_date}. "
                f"Status: {response.status_code}"
            )

    except zipfile.BadZipFile as e:
        raise NSEDataNotFoundError(
            f"Invalid bhav copy zip file for {trade_date}"
        ) from e
    except Exception as e:
        raise NSEDataNotFoundError(
            f"Failed to fetch F&O bhav copy for {trade_date}: {e}"
        ) from e
