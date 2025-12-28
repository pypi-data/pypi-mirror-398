# Quick Start Guide

This guide will get you up and running with nsefeed in 5 minutes.

## Installation

```bash
pip install nsefeed
```

## Your First Script

```python
import nsefeed as nf

# Create a Ticker object
reliance = nf.Ticker("RELIANCE")

# Get last 1 month of data
df = reliance.history(period="1mo")
print(df)
```

## Understanding the Output

The `history()` method returns a pandas DataFrame:

```
                  open     high      low    close      volume
date
2024-11-01     1245.50  1258.30  1240.00  1255.75     2345678
2024-11-04     1256.00  1268.90  1252.10  1265.40     2567890
2024-11-05     1266.00  1275.00  1260.00  1272.50     2123456
```

Columns:
- **date**: Trading date (index)
- **open**: Opening price
- **high**: Highest price of the day
- **low**: Lowest price of the day
- **close**: Closing price
- **volume**: Number of shares traded

## Common Use Cases

### 1. Specific Date Range

```python
df = reliance.history(start="2024-01-01", end="2024-06-30")
```

### 2. Different Time Periods

```python
# Last 5 days
df = reliance.history(period="5d")

# Last 3 months
df = reliance.history(period="3mo")

# Last 1 year
df = reliance.history(period="1y")

# Year to date
df = reliance.history(period="ytd")

# Maximum available
df = reliance.history(period="max")
```

### 3. Different Intervals

```python
# Daily (default)
df = reliance.history(period="3mo", interval="1d")

# Weekly
df = reliance.history(period="3mo", interval="1wk")

# Monthly
df = reliance.history(period="1y", interval="1mo")
```

### 4. Multiple Tickers

```python
# Download multiple stocks at once
data = nf.download(
    tickers=["RELIANCE", "TCS", "INFY"],
    period="1mo"
)

# Access individual DataFrames
print(data["RELIANCE"])
print(data["TCS"])
```

### 5. Company Information

```python
reliance = nf.Ticker("RELIANCE")
info = reliance.info

print(f"Company: {info['companyName']}")
print(f"Industry: {info['industry']}")
print(f"Last Price: ₹{info['lastPrice']}")
```

## Supported Symbols

nsefeed supports all NSE equity symbols. Common examples:

| Symbol | Company |
|--------|---------|
| RELIANCE | Reliance Industries |
| TCS | Tata Consultancy Services |
| HDFCBANK | HDFC Bank |
| INFY | Infosys |
| ICICIBANK | ICICI Bank |
| HINDUNILVR | Hindustan Unilever |
| ITC | ITC Limited |
| SBIN | State Bank of India |
| BHARTIARTL | Bharti Airtel |
| KOTAKBANK | Kotak Mahindra Bank |

## Error Handling

```python
from nsefeed.exceptions import (
    NSEInvalidSymbolError,
    NSEDataNotFoundError
)

try:
    ticker = nf.Ticker("INVALIDSYMBOL")
    df = ticker.history(period="1mo")
except NSEInvalidSymbolError as e:
    print(f"Invalid symbol: {e}")
except NSEDataNotFoundError as e:
    print(f"No data available: {e}")
```

## Debugging

Enable debug logging to see detailed output:

```python
import nsefeed as nf

# Enable debug mode
nf.enable_debug()

# Now all operations will show debug info
ticker = nf.Ticker("RELIANCE")
df = ticker.history(period="1mo")
```

## Cache Management

Data is cached locally to reduce server load:

```python
import nsefeed as nf

# Clear all cached data
nf.clear_cache()

# Get cache statistics
from nsefeed import NSECache
cache = NSECache()
stats = cache.get_cache_stats()
print(f"Symbols cached: {stats['symbols_cached']}")
```

## Next Steps

- Check out the [examples](../examples/) directory
- Read the full [API Reference](api_reference.md)
- Learn about [advanced usage](advanced_usage.md)
