from __future__ import annotations

import os
from pathlib import Path
from typing import Final

# Logging
LOG_LEVEL: Final[str] = os.getenv("NSEFEED_LOG_LEVEL", "INFO").upper()
LOG_FILE: Final[str | None] = os.getenv("NSEFEED_LOG_FILE") or None
LOG_COLOR_RAW: Final[str] = os.getenv("NSEFEED_LOG_COLOR", "auto")

# Networking / session
USER_AGENT_DEFAULT: Final[str] = (
    os.getenv(
        "NSEFEED_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
)
# Allow overriding rate limits and timeouts via env
RATE_LIMIT_RPS: Final[float] = float(os.getenv("NSEFEED_RATE_LIMIT", os.getenv("NSEFEED_RPS", "3.0")))
MIN_REQUEST_DELAY: Final[float] = float(os.getenv("NSEFEED_MIN_REQUEST_DELAY", "0.35"))
REQUEST_TIMEOUT: Final[int] = int(os.getenv("NSEFEED_REQUEST_TIMEOUT", "30"))
SESSION_REFRESH_INTERVAL: Final[int] = int(os.getenv("NSEFEED_SESSION_REFRESH_INTERVAL", "300"))

# Cache directory override (optional, useful for tests)
CACHE_DIR: Final[str] = os.getenv("NSEFEED_CACHE_DIR", str(Path.home() / ".nsefeed"))

# Helper boolean parser
def parse_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")
# Derived value
LOG_COLOR: Final[bool | str] = (
    "auto" if LOG_COLOR_RAW.lower() == "auto" else parse_bool(LOG_COLOR_RAW, default=False)
)
