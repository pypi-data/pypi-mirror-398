"""
Base scraper class for NSE data fetching.

This module provides the abstract base class for all NSE scrapers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import pandas as pd

from ..session import NSESession


class BaseScraper(ABC):
    """
    Abstract base class for NSE data scrapers.

    All scrapers (bhav copy, live data, derivatives, etc.) should
    inherit from this class and implement the required methods.
    """

    def __init__(self) -> None:
        """Initialize the scraper with a session."""
        self._session = NSESession.get_instance()

    @property
    def session(self) -> NSESession:
        """Get the NSE session instance."""
        return self._session

    @abstractmethod
    def fetch(self, *args, **kwargs) -> pd.DataFrame:
        """
        Fetch data from NSE.

        This method must be implemented by subclasses.

        Returns:
            DataFrame containing the fetched data
        """
        pass

    @abstractmethod
    def validate_params(self, *args, **kwargs) -> bool:
        """
        Validate input parameters.

        This method must be implemented by subclasses.

        Returns:
            True if parameters are valid
        """
        pass
