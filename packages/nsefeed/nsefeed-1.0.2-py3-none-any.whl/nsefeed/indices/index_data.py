"""
Index data fetching functions for NSE India.

This module provides:
- Index constituent lists (WORKING)
- Historical index OHLCV data (UNDER DEVELOPMENT - NSE API deprecated)
- Historical India VIX data (UNDER DEVELOPMENT - NSE API deprecated)

NOTE: NSE has deprecated their historical index data endpoints.
index_data() and india_vix_data() are currently non-functional.
Use constituent_stock_list() and index_list() which work reliably.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import pandas as pd

from ..exceptions import NSEDataNotFoundError
from ..session import NSESession
from . import config
from ..logger import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from datetime import date


def _get_index_config_class(index_category: str):
    """Get the configuration class for a given index category."""
    category = f"Nifty{index_category}"
    category_class = getattr(config, category, None)

    if category_class is None:
        raise ValueError(
            f"Invalid index category: {index_category}. "
            f"Valid categories: {config.VALID_INDEX_CATEGORIES}"
        )
    return category_class


def _validate_index_category(index_category: str) -> None:
    """Validate that the index category is valid."""
    if index_category not in config.VALID_INDEX_CATEGORIES:
        raise ValueError(
            f"Invalid index category: {index_category}. "
            f"Valid categories: {config.VALID_INDEX_CATEGORIES}"
        )


def _validate_index_name(index_category: str, index_name: str) -> None:
    """Validate that the index name exists in the given category."""
    _validate_index_category(index_category)
    ind_list = index_list(index_category)
    if index_name not in ind_list:
        raise ValueError(
            f"Invalid index name: {index_name}. "
            f"Valid indices in {index_category}: {ind_list}"
        )


def index_list(index_category: str = "BroadMarketIndices") -> list[str]:
    """
    Get list of all available NSE indices for a given category.

    NSE organizes indices into 4 main categories:
    - BroadMarketIndices: NIFTY 50, NIFTY Next 50, etc.
    - SectoralIndices: NIFTY Bank, NIFTY IT, etc.
    - ThematicIndices: NIFTY Commodities, NIFTY Energy, etc.
    - StrategyIndices: NIFTY Dividend Opportunities, etc.

    Parameters
    ----------
    index_category : str, default "BroadMarketIndices"
        Category of indices. Must be one of:
        'BroadMarketIndices', 'SectoralIndices', 'ThematicIndices', 'StrategyIndices'

    Returns
    -------
    list[str]
        List of index names in the specified category

    Raises
    ------
    ValueError
        If index_category is invalid

    Examples
    --------
    >>> import nsefeed as nf
    >>> nf.indices.index_list('BroadMarketIndices')
    ['Nifty 50', 'Nifty Next 50', 'Nifty 100', ...]

    >>> nf.indices.index_list('SectoralIndices')
    ['Nifty Auto', 'Nifty Bank', 'Nifty Financial Services', ...]
    """
    return _get_index_config_class(index_category).indices_list


def constituent_stock_list(
    index_category: str = "BroadMarketIndices",
    index_name: str = "Nifty 50"
) -> pd.DataFrame:
    """
    Get list of all constituent stocks in a given index.

    Fetches the current list of stocks that are part of the specified index.
    Data is sourced from NSE archives CSV files.

    Parameters
    ----------
    index_category : str, default "BroadMarketIndices"
        Category of the index
    index_name : str, default "Nifty 50"
        Name of the index. Get available names using index_list()

    Returns
    -------
    pd.DataFrame
        DataFrame containing constituent stock details including:
        - Symbol: Stock symbol
        - Company Name: Full company name
        - Industry: Sector/Industry classification
        - Series: Trading series (typically EQ)
        - ISIN Code: International Securities Identification Number

    Raises
    ------
    ValueError
        If index_category or index_name is invalid
    NSEDataNotFoundError
        If constituent list data is not available

    Examples
    --------
    >>> import nsefeed as nf
    >>> # Get NIFTY 50 constituent stocks
    >>> df = nf.indices.constituent_stock_list('BroadMarketIndices', 'Nifty 50')
    >>> print(df[['Symbol', 'Company Name']].head())

    >>> # Get NIFTY Bank constituent stocks
    >>> df = nf.indices.constituent_stock_list('SectoralIndices', 'Nifty Bank')
    """
    _validate_index_name(index_category, index_name)

    # Get the CSV URL from config
    config_class = _get_index_config_class(index_category)
    url = config_class.index_constituent_list_urls.get(index_name)

    if not url:
        raise NSEDataNotFoundError(
            f"Constituent list URL not found for index: {index_name}"
        )

    # Fetch data using NSE session
    session = NSESession()
    try:
        response = session.get(url)
        if response.status_code != 200:
            raise NSEDataNotFoundError(
                f"Failed to fetch constituent list for {index_name}. "
                f"Status code: {response.status_code}"
            )

        # Parse CSV
        stocks_df = pd.read_csv(BytesIO(response.content))

    except Exception as e:
        raise NSEDataNotFoundError(
            f"Failed to fetch constituent list for {index_name}: {e}"
        ) from e

    # Get factsheet URL for reference
    factsheet_url = config_class.index_factsheet_urls.get(index_name, "")
    if factsheet_url:
        print(
            f"Note: For detailed information about {index_name}, "
            f"see factsheet: {factsheet_url}"
        )

    return stocks_df


def index_data(
    index: str,
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get historical OHLCV data for NSE indices.

    **CURRENTLY UNAVAILABLE**: NSE has deprecated their historical index data endpoints.
    This function is under development as we work on alternative data sources.

    Parameters
    ----------
    index : str
        Name of the index (case-insensitive). Examples:
        - "NIFTY 50", "NIFTY BANK", "NIFTY IT", etc.
    from_date : str | date, optional
        Start date in format 'DD-MM-YYYY' or datetime.date object
    to_date : str | date, optional
        End date in format 'DD-MM-YYYY' or datetime.date object
    period : str, optional
        Time period. Use instead of from_date/to_date.
        Valid: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'

    Raises
    ------
    NotImplementedError
        This function is currently unavailable due to NSE API deprecation

    Examples
    --------
    >>> import nsefeed as nf
    >>> # This function is currently not working
    >>> # df = nf.indices.index_data("NIFTY 50", period="1mo")
    >>>
    >>> # WORKAROUND: Use constituent stocks instead
    >>> stocks = nf.indices.constituent_stock_list("BroadMarketIndices", "Nifty 50")
    >>> for symbol in stocks['Symbol'][:5]:
    ...     df = nf.Ticker(symbol).history(period="1mo")
    """
    raise NotImplementedError(
        "Historical index data is currently unavailable due to NSE API deprecation. "
        "This feature is under development as we work on alternative data sources. "
        "\n\nWorkaround: Use nf.indices.constituent_stock_list() to get index constituents, "
        "then fetch individual stock data using nf.Ticker(symbol).history()"
    )


def india_vix_data(
    from_date: str | date | None = None,
    to_date: str | date | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """
    Get historical India VIX (Volatility Index) data.

    **CURRENTLY UNAVAILABLE**: NSE has deprecated their VIX data endpoints.
    This function is under development as we work on alternative data sources.

    Parameters
    ----------
    from_date : str | date, optional
        Start date in format 'DD-MM-YYYY' or datetime.date object
    to_date : str | date, optional
        End date in format 'DD-MM-YYYY' or datetime.date object
    period : str, optional
        Time period. Use instead of from_date/to_date.
        Valid: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'

    Raises
    ------
    NotImplementedError
        This function is currently unavailable due to NSE API deprecation

    Examples
    --------
    >>> import nsefeed as nf
    >>> # This function is currently not working
    >>> # vix = nf.indices.india_vix_data(period="1mo")
    """
    raise NotImplementedError(
        "Historical India VIX data is currently unavailable due to NSE API deprecation. "
        "This feature is under development as we work on alternative data sources."
    )
