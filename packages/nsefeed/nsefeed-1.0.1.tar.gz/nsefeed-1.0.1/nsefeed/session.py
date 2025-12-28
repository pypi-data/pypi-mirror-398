"""
NSE Session management with proper cookie and header handling.

This module provides a singleton NSESession class that manages:
- Session initialization with NSE website
- Cookie acquisition and management
- Rate limiting (max 3 requests/second)
- Automatic retry with exponential backoff
- Session refresh on authentication errors
- User-Agent rotation for resilience
"""

from __future__ import annotations

import threading
import time
from io import BytesIO
from typing import Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config as cfg
from . import logger
from .constants import (
    DEFAULT_HEADERS,
    ARCHIVE_HEADERS,
    USER_AGENTS,
    NSE_BASE_URL,
    NSE_ENDPOINTS,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    INITIAL_RETRY_DELAY,
)
from .exceptions import (
    NSEConnectionError,
    NSERateLimitError,
    NSESessionError,
)


class NSESession:
    """
    Singleton class for managing NSE HTTP sessions.

    This class handles all communication with NSE servers, including:
    - Initial session establishment (cookie acquisition)
    - Rate limiting to avoid being blocked
    - Automatic retry with exponential backoff
    - Session refresh on authentication failures

    Usage:
        session = NSESession.get_instance()
        data = session.get("/api/quote-equity", params={"symbol": "RELIANCE"})

    Thread-Safety:
        This class is thread-safe and can be used from multiple threads.
    """

    _instance: Optional["NSESession"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "NSESession":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the session (only runs once due to singleton)."""
        if self._initialized:
            return

        self._session: Optional[requests.Session] = None
        self._cookies: dict[str, str] = {}
        self._last_request_time: float = 0.0
        self._session_created_time: float = 0.0
        self._request_lock: threading.Lock = threading.Lock()
        self._ua_index: int = 0

        self._initialized = True
        self._init_session()

    @classmethod
    def get_instance(cls) -> "NSESession":
        """Get the singleton instance of NSESession."""
        return cls()

    def _init_session(self) -> None:
        """Initialize a new requests session with proper configuration."""
        logger.debug("Initializing new NSE session")

        # Create new session
        self._session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        # Set default headers
        self._session.headers.update(self._get_headers())

        # Establish session with NSE
        self._establish_session()

    def _get_headers(self, for_archive: bool = False) -> dict[str, str]:
        """
        Get headers for requests, rotating User-Agent.

        Args:
            for_archive: If True, return archive-specific headers

        Returns:
            Dictionary of HTTP headers
        """
        headers = ARCHIVE_HEADERS.copy() if for_archive else DEFAULT_HEADERS.copy()

        # Rotate User-Agent (use config default if USER_AGENTS is empty)
        if USER_AGENTS:
            self._ua_index = (self._ua_index + 1) % len(USER_AGENTS)
            headers["User-Agent"] = USER_AGENTS[self._ua_index]
        else:
            headers["User-Agent"] = cfg.USER_AGENT_DEFAULT

        # Enforce gzip/deflate to avoid brotli issues if library missing
        headers["Accept-Encoding"] = "gzip, deflate"

        return headers

    def _establish_session(self) -> None:
        """
        Establish session by visiting NSE homepage to get cookies.

        NSE requires cookies from visiting the homepage before accessing
        any API endpoints. This method handles that initial handshake.
        """
        if not self._session:
            raise NSESessionError("Session not initialized")

        try:
            logger.debug("Establishing session with NSE homepage")

            # Simple headers for initial homepage visit (inspired by nselib)
            simple_headers = {
                "User-Agent": cfg.USER_AGENT_DEFAULT
            }

            # Visit homepage to get cookies
            response = self._session.get(
                "https://www.nseindia.com",
                headers=simple_headers,
                timeout=cfg.REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            # Store cookies
            self._cookies = dict(response.cookies)
            self._session_created_time = time.time()

            logger.info(f"NSE session established successfully, cookies: {len(self._cookies)}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to establish NSE session: {e}")
            raise NSESessionError(
                "Failed to establish session with NSE",
                details=str(e),
            )

    def _should_refresh_session(self) -> bool:
        """Check if session needs to be refreshed."""
        if self._session_created_time == 0:
            return True
        elapsed = time.time() - self._session_created_time
        return elapsed > cfg.SESSION_REFRESH_INTERVAL

    def _rate_limit(self) -> None:
        """
        Implement rate limiting to avoid being blocked.

        Ensures minimum delay between requests (approximately 3 req/sec).
        """
        with self._request_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < cfg.MIN_REQUEST_DELAY:
                sleep_time = cfg.MIN_REQUEST_DELAY - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f}s")
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    def _handle_response_error(
        self, response: requests.Response, url: str
    ) -> None:
        """
        Handle HTTP error responses.

        Args:
            response: The HTTP response object
            url: The requested URL

        Raises:
            NSERateLimitError: If rate limited (429)
            NSEConnectionError: For other HTTP errors
        """
        status_code = response.status_code

        if status_code == 401 or status_code == 403:
            logger.warning(f"Authentication error ({status_code}), refreshing session")
            self._establish_session()
            raise NSESessionError(
                f"Authentication failed (HTTP {status_code})",
                details="Session has been refreshed, please retry",
            )

        if status_code == 429:
            retry_after = float(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited, retry after {retry_after}s")
            raise NSERateLimitError(retry_after=retry_after)

        if status_code == 404:
            raise NSEConnectionError(
                "Resource not found",
                details=f"URL: {url}",
                status_code=status_code,
            )

        raise NSEConnectionError(
            f"HTTP error {status_code}",
            details=response.text[:200] if response.text else None,
            status_code=status_code,
        )

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        for_archive: bool = False,
        timeout: int | None = None,
    ) -> requests.Response:
        """
        Make a GET request to NSE with proper session handling.

        Args:
            url: URL or endpoint path (if starts with /, prepends NSE_BASE_URL)
            params: Query parameters
            headers: Custom headers to update/override defaults
            for_archive: If True, use archive-specific headers
            timeout: Request timeout in seconds

        Returns:
            requests.Response object

        Raises:
            NSEConnectionError: On connection failures
            NSERateLimitError: If rate limited
            NSESessionError: On session issues
        """
        if not self._session:
            raise NSESessionError("Session not initialized")

        # Build full URL if needed
        if url.startswith("/"):
            url = f"{NSE_BASE_URL}{url}"

        # Use config default if timeout not specified
        if timeout is None:
            timeout = cfg.REQUEST_TIMEOUT

        # Refresh session if needed
        if self._should_refresh_session():
            logger.debug("Session expired, refreshing")
            self._establish_session()

        # Apply rate limiting
        self._rate_limit()

        # Make request with retry logic
        retry_count = 0
        last_exception: Exception | None = None

        while retry_count <= MAX_RETRIES:
            try:
                logger.debug(f"GET {url} (attempt {retry_count + 1})")

                # Use proper headers based on request type
                req_headers = self._get_headers(for_archive=for_archive)
                # Always add referer and origin for API calls
                if "/api/" in url:
                    req_headers.update({
                        "Referer": "https://www.nseindia.com/",
                        "Origin": "https://www.nseindia.com",
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json, text/javascript, */*; q=0.01"
                    })
                    logger.debug(f"API call with headers: Referer, Origin, X-Requested-With")

                # Update with custom headers if provided
                if headers:
                    req_headers.update(headers)

                response = self._session.get(
                    url,
                    params=params,
                    headers=req_headers,
                    cookies=self._cookies,
                    timeout=timeout,
                )

                # Handle non-success status codes
                if not response.ok:
                    self._handle_response_error(response, url)

                return response

            except NSESessionError:
                # Session was refreshed, retry immediately
                retry_count += 1
                continue

            except NSERateLimitError as e:
                # Rate limited, wait and retry
                if e.retry_after:
                    time.sleep(e.retry_after)
                retry_count += 1
                last_exception = e
                continue

            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout: {url}")
                retry_count += 1
                last_exception = e
                time.sleep(INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count))
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                retry_count += 1
                last_exception = e
                time.sleep(INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count))
                continue

        # All retries exhausted
        raise NSEConnectionError(
            "Failed to connect to NSE after multiple retries",
            details=str(last_exception) if last_exception else None,
        )

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        Make a GET request and parse JSON response.

        Args:
            url: URL or endpoint path
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON as dictionary

        Raises:
            NSEConnectionError: On connection or parsing failures
        """
        response = self.get(url, params=params, timeout=timeout)

        try:
            # Check if response is empty
            if not response.content:
                raise NSEConnectionError(
                    "Empty response from NSE",
                    details=f"URL: {url}",
                )

            # Parse JSON - requests automatically handles gzip decoding
            json_data = response.json()
            return json_data

        except ValueError as e:
            # Log the actual response for debugging
            try:
                response_preview = response.text[:500] if response.text else "<empty>"
            except:
                response_preview = f"<binary data, length: {len(response.content)}>"

            logger.error(f"JSON parse error for {url}")
            logger.error(f"Response preview: {response_preview}")
            logger.error(f"Response headers: {dict(response.headers)}")

            raise NSEConnectionError(
                "Failed to parse JSON response",
                details=f"{str(e)} | Check if endpoint is valid",
            )

    def get_csv(
        self,
        url: str,
        origin_url: str | None = None,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> pd.DataFrame:
        """
        Make a GET request and parse CSV response into DataFrame.

        This method is designed for NSE's CSV download endpoints which are
        more reliable than JSON APIs. Handles gzip compression and various encodings.

        Args:
            url: URL or endpoint path
            origin_url: Origin/referer URL to visit first for cookies
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            Parsed CSV as pandas DataFrame

        Raises:
            NSEConnectionError: On connection or parsing failures
        """
        import gzip
        import io

        # If origin URL provided, visit it first to get cookies
        if origin_url:
            try:
                logger.debug(f"Visiting origin URL: {origin_url}")
                self.get(origin_url, timeout=timeout)
            except Exception as e:
                logger.warning(f"Failed to visit origin URL: {e}")

        # Make the actual request
        response = self.get(url, params=params, timeout=timeout)

        try:
            # Check if response is empty
            if not response.content:
                raise NSEConnectionError(
                    "Empty CSV response from NSE",
                    details=f"URL: {url}",
                )

            content = response.content

            # Check Content-Type to see if it's actually HTML (error page)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                # NSE returned an error page instead of CSV
                logger.error(f"NSE returned HTML instead of CSV. Status: {response.status_code}")
                raise NSEConnectionError(
                    "NSE returned HTML error page instead of CSV data",
                    details=f"This usually means the endpoint is not accessible or requires different parameters",
                    status_code=response.status_code
                )

            # Try to decompress if compressed (requests should auto-decompress, but sometimes it doesn't)
            # Try gzip first
            if len(content) >= 2 and content[:2] == b'\x1f\x8b':
                try:
                    logger.debug("Detected gzip-compressed response, decompressing")
                    content = gzip.decompress(content)
                    logger.debug(f"Successfully decompressed gzip data: {len(content)} bytes")
                except Exception as e:
                    logger.debug(f"Gzip decompression failed: {e}")
            # Try raw deflate if first byte looks compressed
            elif len(content) > 0 and content[0:1] in [b'\x78', b'\x58', b'\x08', b'\x18', b'\x28', b'\x38', b'\x48', b'\x68']:
                try:
                    import zlib
                    logger.debug("Attempting deflate decompression")
                    content = zlib.decompress(content)
                    logger.debug(f"Successfully decompressed deflate data: {len(content)} bytes")
                except Exception as e:
                    logger.debug(f"Deflate decompression failed: {e}")
                    # Try with -zlib.MAX_WBITS for raw deflate
                    try:
                        content = zlib.decompress(content, -zlib.MAX_WBITS)
                        logger.debug(f"Successfully decompressed raw deflate data: {len(content)} bytes")
                    except Exception as e2:
                        logger.debug(f"Raw deflate decompression also failed: {e2}")

            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            last_error = None

            for encoding in encodings:
                try:
                    logger.debug(f"Trying encoding: {encoding}")
                    # Decode bytes to string with the current encoding
                    text_content = content.decode(encoding)
                    # Parse CSV from string
                    df = pd.read_csv(io.StringIO(text_content))
                    logger.debug(f"Successfully parsed with {encoding} encoding")
                    break
                except Exception as e:
                    last_error = e
                    logger.debug(f"Failed with {encoding}: {str(e)[:100]}")
                    continue

            # If all encodings failed, raise error
            if df is None:
                raise last_error if last_error else Exception("Failed to parse CSV")

            # Clean column names (remove spaces)
            df.columns = [col.replace(' ', '') for col in df.columns]

            logger.debug(f"Successfully parsed CSV: {len(df)} rows, {len(df.columns)} columns")
            return df

        except Exception as e:
            # Log the actual response for debugging
            try:
                # Try to decode for preview
                preview = None
                for enc in ['utf-8', 'latin-1', 'iso-8859-1']:
                    try:
                        preview = content[:500].decode(enc)
                        break
                    except:
                        continue
                response_preview = preview if preview else f"<binary data, length: {len(content)}>"
            except:
                response_preview = f"<binary data, length: {len(content)}>"

            logger.error(f"CSV parse error for {url}")
            logger.error(f"Response preview: {response_preview}")
            logger.error(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            logger.error(f"Content-Encoding: {response.headers.get('Content-Encoding', 'none')}")
            logger.error(f"Error: {str(e)}")

            raise NSEConnectionError(
                "Failed to parse CSV response",
                details=f"{str(e)} | Check if endpoint returns valid CSV",
            )

    def get_with_origin(
        self,
        url: str,
        origin_url: str,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """
        Make a GET request after visiting an origin URL for cookies.

        This pattern is used by NSE for certain endpoints that require
        visiting a specific page first.

        Args:
            url: URL or endpoint path
            origin_url: Origin/referer URL to visit first
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            requests.Response object

        Raises:
            NSEConnectionError: On connection failures
        """
        # Visit origin page first
        try:
            logger.debug(f"Visiting origin URL: {origin_url}")
            self.get(origin_url, timeout=timeout)
        except Exception as e:
            logger.warning(f"Failed to visit origin URL: {e}")

        # Make the actual request with referer header
        return self.get(url, params=params, timeout=timeout)

    def download_file(
        self,
        url: str,
        timeout: int | None = None,
    ) -> bytes:
        """
        Download a file (e.g., bhav copy ZIP) from NSE archives.

        Args:
            url: URL of the file to download
            timeout: Request timeout in seconds

        Returns:
            File content as bytes

        Raises:
            NSEConnectionError: On download failures
        """
        if timeout is None:
            timeout = cfg.REQUEST_TIMEOUT * 2
        response = self.get(url, for_archive=True, timeout=timeout)
        return response.content

    def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """
        Make an HTTP POST request to NSE servers.

        Args:
            url: URL or endpoint path
            json: JSON payload for the request
            data: Form data for the request
            headers: Custom headers to update/override defaults
            timeout: Request timeout in seconds

        Returns:
            requests.Response object

        Raises:
            NSEConnectionError: On connection failures
            NSERateLimitError: If rate limited
            NSESessionError: On session issues
        """
        if not self._session:
            raise NSESessionError("Session not initialized")

        # Build full URL if needed
        if url.startswith("/"):
            url = f"{NSE_BASE_URL}{url}"

        # Use config default if timeout not specified
        if timeout is None:
            timeout = cfg.REQUEST_TIMEOUT

        # Refresh session if needed
        if self._should_refresh_session():
            logger.debug("Session expired, refreshing")
            self._establish_session()

        # Apply rate limiting
        self._rate_limit()

        # Make request with retry logic
        retry_count = 0
        last_exception: Exception | None = None

        while retry_count <= MAX_RETRIES:
            try:
                logger.debug(f"POST {url} (attempt {retry_count + 1})")

                # Use proper headers
                req_headers = self._get_headers(for_archive=False)
                # Always add referer and origin for API calls
                if "/api/" in url or "Backpage.aspx" in url:
                    req_headers.update({
                        "Referer": "https://www.niftyindices.com/reports/historical-data",
                        "Origin": headers.get("Origin", "https://www.niftyindices.com") if headers else "https://www.niftyindices.com",
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json, text/javascript, */*; q=0.01"
                    })

                # Update with custom headers if provided
                if headers:
                    req_headers.update(headers)

                response = self._session.post(
                    url,
                    json=json,
                    data=data,
                    headers=req_headers,
                    cookies=self._cookies,
                    timeout=timeout,
                )

                # Handle non-success status codes
                if not response.ok:
                    self._handle_response_error(response, url)

                return response

            except NSESessionError:
                # Session was refreshed, retry immediately
                retry_count += 1
                continue

            except NSERateLimitError as e:
                # Rate limited, wait and retry
                if e.retry_after:
                    time.sleep(e.retry_after)
                retry_count += 1
                last_exception = e
                continue

            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout: {url}")
                retry_count += 1
                last_exception = e
                time.sleep(INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count))
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                retry_count += 1
                last_exception = e
                time.sleep(INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count))
                continue

        # All retries exhausted
        raise NSEConnectionError(
            "Failed to connect to NSE after multiple retries",
            details=str(last_exception) if last_exception else None,
        )

    def close(self) -> None:
        """Close the session and clean up resources."""
        if self._session:
            self._session.close()
            self._session = None
            self._cookies = {}
            self._session_created_time = 0
            logger.debug("NSE session closed")

    def __enter__(self) -> "NSESession":
        """Context manager entry."""
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Context manager exit - close session."""
        self.close()

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.

        Useful for testing or when a fresh session is needed.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None
