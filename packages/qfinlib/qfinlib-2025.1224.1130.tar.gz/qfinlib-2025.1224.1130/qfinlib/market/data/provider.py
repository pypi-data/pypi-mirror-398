"""Market data provider abstract base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import date


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_rates(self, currency: str, as_of: Optional[date] = None) -> Dict[str, Any]:
        """Get rates data for a currency."""
        pass

    @abstractmethod
    def get_bond_prices(self, bond_id: str, as_of: Optional[date] = None) -> Dict[str, Any]:
        """Get bond price data."""
        pass

    @abstractmethod
    def get_volatility(self, asset_class: str, as_of: Optional[date] = None) -> Dict[str, Any]:
        """Get volatility data."""
        pass

    @abstractmethod
    def get_fx_rates(self, currency_pair: str, as_of: Optional[date] = None) -> Dict[str, Any]:
        """Get FX rate data."""
        pass
