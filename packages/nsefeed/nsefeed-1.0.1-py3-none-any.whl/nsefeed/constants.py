"""
Constants and configuration for nsefeed library.

This module contains all static configuration values including:
- NSE API endpoints and archive URLs
- HTTP headers for session management
- Rate limiting configuration
- Index definitions (NIFTY 50, NIFTY BANK)
- Cache configuration
"""

from __future__ import annotations

from typing import Final

# =============================================================================
# NSE Website URLs
# =============================================================================

NSE_BASE_URL: Final[str] = "https://www.nseindia.com"
NSE_ARCHIVES_URL: Final[str] = "https://archives.nseindia.com"
NSE_NEW_ARCHIVES_URL: Final[str] = "https://nsearchives.nseindia.com"

# =============================================================================
# NSE API Endpoints (For CSV downloads - Reliable)
# =============================================================================

NSE_ENDPOINTS: Final[dict[str, str]] = {
    # Homepage - for session initialization
    "home": f"{NSE_BASE_URL}/",

    # Index data
    "stock_indices": f"{NSE_BASE_URL}/api/equity-stockIndices",
    "nifty50": f"{NSE_BASE_URL}/api/equity-stockIndices?index=NIFTY%2050",

    # Corporate actions
    "corporate_actions": f"{NSE_BASE_URL}/api/corporates-corporateActions",
    
    # Stock quote
    "quote_equity": f"{NSE_BASE_URL}/api/quote-equity",
}

# =============================================================================
# CSV Download Endpoints (More reliable than JSON APIs)
# =============================================================================

CSV_ENDPOINTS: Final[dict[str, dict[str, str]]] = {
    # Equity price, volume, and deliverable data
    "equity_deliverable": {
        "url": f"{NSE_BASE_URL}/api/historicalOR/generateSecurityWiseHistoricalData",
        "origin": f"{NSE_BASE_URL}/report-detail/eq_security",
    },
    # Bulk deals
    "bulk_deals": {
        "url": f"{NSE_BASE_URL}/api/historicalOR/bulk-block-short-deals",
        "origin": f"{NSE_BASE_URL}",
    },
    # Block deals
    "block_deals": {
        "url": f"{NSE_BASE_URL}/api/historicalOR/bulk-block-short-deals",
        "origin": f"{NSE_BASE_URL}",
    },
    # Short selling
    "short_selling": {
        "url": f"{NSE_BASE_URL}/api/historicalOR/bulk-block-short-deals",
        "origin": f"{NSE_BASE_URL}",
    },
    # Historical index data
    "index_history": {
        "url": f"{NSE_BASE_URL}/api/historical/indicesHistory",
        "origin": f"{NSE_BASE_URL}/reports-indices-historical-index-data",
    },
    # VIX historical data
    "vix_history": {
        "url": "https://nsewebsite-staging.nseindia.com/api/historical/vixhistory",
        "origin": f"{NSE_BASE_URL}/report-detail/eq_security",
    },
    # Futures and Options historical
    "fo_cpv": {
        "url": f"{NSE_BASE_URL}/api/historical/foCPV",
        "origin": f"{NSE_BASE_URL}/report-detail/fo_eq_security",
    },
}

# =============================================================================
# Bhav Copy URL Templates
# =============================================================================

# Old format (works for historical data)
# Example: https://archives.nseindia.com/content/historical/EQUITIES/2024/JAN/cm02JAN2024bhav.csv.zip
BHAV_COPY_OLD_URL: Final[str] = (
    f"{NSE_ARCHIVES_URL}/content/historical/EQUITIES/"
    "{{year}}/{{month}}/cm{{date}}bhav.csv.zip"
)

# New format (UDiFF format, recent data)
# Example: https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20241129_F_0000.csv.zip
BHAV_COPY_NEW_URL: Final[str] = (
    f"{NSE_NEW_ARCHIVES_URL}/content/cm/"
    "BhavCopy_NSE_CM_0_0_0_{{date}}_F_0000.csv.zip"
)

# Delivery data URL
DELIVERY_DATA_URL: Final[str] = (
    f"{NSE_ARCHIVES_URL}/products/content/sec_bhavdata_full_"
    "{{date}}.csv"
)

# Index historical data URL
INDEX_HISTORICAL_URL: Final[str] = (
    f"{NSE_ARCHIVES_URL}/content/indices/ind_close_all_{{date}}.csv"
)

# =============================================================================
# HTTP Headers (Required for NSE requests)
# =============================================================================

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://www.nseindia.com/",
    "Origin": "https://www.nseindia.com",
    "Connection": "keep-alive",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Headers for archive downloads
ARCHIVE_HEADERS: Final[dict[str, str]] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Rotating User-Agents for better resilience
USER_AGENTS: Final[list[str]] = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) "
        "Gecko/20100101 Firefox/132.0"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/18.1 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
]

# =============================================================================
# Rate Limiting Configuration
# =============================================================================

# Maximum requests per second (NSE unofficial limit)
MAX_REQUESTS_PER_SECOND: Final[float] = 3.0

# Minimum delay between requests (in seconds)
MIN_REQUEST_DELAY: Final[float] = 0.35  # Slightly more than 1/3 second

# Retry configuration
MAX_RETRIES: Final[int] = 3
RETRY_BACKOFF_FACTOR: Final[float] = 1.5  # Exponential backoff multiplier
INITIAL_RETRY_DELAY: Final[float] = 1.0  # Initial retry delay in seconds

# Request timeout (in seconds)
REQUEST_TIMEOUT: Final[int] = 30

# Session refresh interval (in seconds) - refresh session every 5 minutes
SESSION_REFRESH_INTERVAL: Final[int] = 300

# =============================================================================
# Cache Configuration
# =============================================================================

# Default cache directory (relative to user home)
DEFAULT_CACHE_DIR: Final[str] = ".nsefeed"

# Cache database filename
CACHE_DB_NAME: Final[str] = "cache.db"

# Cache TTL (Time To Live) in seconds
CACHE_TTL: Final[dict[str, int]] = {
    "historical_data": 7 * 24 * 3600,  # 7 days for historical OHLC
    "live_data": 5 * 60,  # 5 minutes for live data
    "company_info": 24 * 3600,  # 24 hours for company info
    "index_constituents": 7 * 24 * 3600,  # 7 days for index lists
    "market_status": 60,  # 1 minute for market status
}

# =============================================================================
# Date Formats
# =============================================================================

# NSE uses various date formats
DATE_FORMATS: Final[dict[str, str]] = {
    "bhav_copy_old": "%d%b%Y",  # 02JAN2024
    "bhav_copy_new": "%Y%m%d",  # 20240102
    "api": "%d-%m-%Y",  # 02-01-2024
    "display": "%Y-%m-%d",  # 2024-01-02
    "index_file": "%d%m%Y",  # 02012024
}

# =============================================================================
# Valid Series Types
# =============================================================================

EQUITY_SERIES: Final[list[str]] = [
    "EQ",  # Equity
    "BE",  # Book Entry
    "BZ",  # Trade to Trade (Z group)
    "SM",  # SME
    "ST",  # SME Trade to Trade
    "N1",  # NIFTY 50 ETF
    "N2",  # Other ETFs
    "N3",  # Gold ETFs
    "N4",  # Other ETFs
    "N5",  # Infrastructure ETFs
    "N6",  # PSU ETFs
    "N7",  # Shariah ETFs
    "N8",  # Dividend ETFs
]

# Primary series for regular stocks
PRIMARY_SERIES: Final[list[str]] = ["EQ", "BE", "BZ"]

# =============================================================================
# Period Mappings (yfinance-compatible)
# =============================================================================

PERIOD_DAYS: Final[dict[str, int]] = {
    # Lowercase (yfinance-style, for Ticker API compatibility)
    "1d": 1,
    "5d": 5,
    "1w": 7,
    "1mo": 30,
    "1m": 30,  # Alias for 1mo
    "3mo": 90,
    "3m": 90,  # Alias for 3mo
    "6mo": 180,
    "6m": 180,  # Alias for 6mo
    "1y": 365,
    "2y": 730,
    "5y": 1825,
    "10y": 3650,
    "ytd": -1,  # Special handling for year-to-date
    "max": -2,  # Special handling for maximum available

    # Uppercase aliases (for equity/derivatives modules)
    "1D": 1,
    "1W": 7,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
    "2Y": 730,
    "5Y": 1825,
    "10Y": 3650,
    "YTD": -1,
    "MAX": -2,
}

# =============================================================================
# Interval Mappings
# =============================================================================

VALID_INTERVALS: Final[list[str]] = [
    "1d",  # Daily (primary, from bhav copy)
    "1wk",  # Weekly (aggregated from daily)
    "1mo",  # Monthly (aggregated from daily)
]

# =============================================================================
# Market Hours (IST)
# =============================================================================

MARKET_OPEN_HOUR: Final[int] = 9
MARKET_OPEN_MINUTE: Final[int] = 15
MARKET_CLOSE_HOUR: Final[int] = 15
MARKET_CLOSE_MINUTE: Final[int] = 30

# Pre-market session
PRE_MARKET_OPEN_HOUR: Final[int] = 9
PRE_MARKET_OPEN_MINUTE: Final[int] = 0
PRE_MARKET_CLOSE_HOUR: Final[int] = 9
PRE_MARKET_CLOSE_MINUTE: Final[int] = 8

# =============================================================================
# Bhav Copy Column Mappings
# =============================================================================

# Old bhav copy format columns
BHAV_COPY_OLD_COLUMNS: Final[dict[str, str]] = {
    "SYMBOL": "symbol",
    "SERIES": "series",
    "OPEN": "open",
    "HIGH": "high",
    "LOW": "low",
    "CLOSE": "close",
    "LAST": "last",
    "PREVCLOSE": "prev_close",
    "TOTTRDQTY": "volume",
    "TOTTRDVAL": "value",
    "TIMESTAMP": "date",
    "TOTALTRADES": "trades",
    "ISIN": "isin",
}

# New bhav copy format columns (UDiFF format)
BHAV_COPY_NEW_COLUMNS: Final[dict[str, str]] = {
    "TckrSymb": "symbol",
    "SctySrs": "series",
    "OpnPric": "open",
    "HghPric": "high",
    "LwPric": "low",
    "ClsPric": "close",
    "LastPric": "last",
    "PrvsClsgPric": "prev_close",
    "TtlTradgVol": "volume",
    "TtlTrfVal": "value",
    "TradDt": "date",
    "TtlNbOfTxsExctd": "trades",
    "ISIN": "isin",
}

# Output DataFrame columns (standardized)
OUTPUT_COLUMNS: Final[list[str]] = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "value",
    "trades",
]

# =============================================================================
# Data Column Definitions (nselib-style)
# =============================================================================

# Price, volume, and deliverable position data columns
PRICE_VOLUME_DELIVERABLE_COLUMNS: Final[list[str]] = [
    'Symbol', 'Series', 'Date', 'PrevClose', 'OpenPrice', 'HighPrice',
    'LowPrice', 'LastPrice', 'ClosePrice', 'AveragePrice', 'TotalTradedQuantity',
    'TurnoverInRs', 'No.ofTrades', 'DeliverableQty', '%DlyQttoTradedQty'
]

# Price and volume data columns (no delivery)
PRICE_VOLUME_COLUMNS: Final[list[str]] = [
    'Symbol', 'Series', 'Date', 'PrevClose', 'OpenPrice', 'HighPrice',
    'LowPrice', 'LastPrice', 'ClosePrice', 'AveragePrice',
    'TotalTradedQuantity', 'Turnover', 'No.ofTrades'
]

# Deliverable data columns only
DELIVERABLE_COLUMNS: Final[list[str]] = [
    'Symbol', 'Series', 'Date', 'TradedQty', 'DeliverableQty', '%DlyQttoTradedQty'
]

# Bulk deal data columns
BULK_DEAL_COLUMNS: Final[list[str]] = [
    'Date', 'Symbol', 'SecurityName', 'ClientName', 'Buy/Sell', 'QuantityTraded',
    'TradePrice/Wght.Avg.Price', 'Remarks'
]

# Block deals data columns
BLOCK_DEAL_COLUMNS: Final[list[str]] = [
    'Date', 'Symbol', 'SecurityName', 'ClientName', 'Buy/Sell', 'QuantityTraded',
    'TradePrice/Wght.Avg.Price', 'Remarks'
]

# Short selling data columns
SHORT_SELLING_COLUMNS: Final[list[str]] = [
    'Date', 'Symbol', 'SecurityName', 'Quantity'
]

# Future price volume data columns
FUTURE_PRICE_VOLUME_COLUMNS: Final[list[str]] = [
    'TIMESTAMP', 'INSTRUMENT', 'SYMBOL', 'EXPIRY_DT', 'STRIKE_PRICE', 'OPTION_TYPE', 'MARKET_TYPE',
    'OPENING_PRICE', 'TRADE_HIGH_PRICE', 'TRADE_LOW_PRICE', 'CLOSING_PRICE',
    'LAST_TRADED_PRICE', 'PREV_CLS', 'SETTLE_PRICE', 'TOT_TRADED_QTY', 'TOT_TRADED_VAL',
    'OPEN_INT', 'CHANGE_IN_OI', 'MARKET_LOT', 'UNDERLYING_VALUE'
]

# India VIX data columns
INDIA_VIX_COLUMNS: Final[list[str]] = [
    'TIMESTAMP', 'INDEX_NAME', 'OPEN_INDEX_VAL', 'CLOSE_INDEX_VAL', 'HIGH_INDEX_VAL',
    'LOW_INDEX_VAL', 'PREV_CLOSE', 'VIX_PTS_CHG', 'VIX_PERC_CHG'
]

# Index data columns
INDEX_DATA_COLUMNS: Final[list[str]] = [
    'TIMESTAMP', 'INDEX_NAME', 'OPEN_INDEX_VAL', 'HIGH_INDEX_VAL', 'CLOSE_INDEX_VAL',
    'LOW_INDEX_VAL', 'TRADED_QTY', 'TURN_OVER'
]

# =============================================================================
# NSE Index Names
# =============================================================================

INDICES_LIST: Final[list[str]] = [
    'NIFTY', 'FINNIFTY', 'BANKNIFTY', 'MIDCPNIFTY'
]
