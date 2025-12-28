"""Trade, TradeData, TradeResolver base classes."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import date


class Instrument(ABC):
    """Base class for all financial instruments."""

    def __init__(self, trade_date: Optional[date] = None):
        """Initialize instrument."""
        self.trade_date = trade_date

    @abstractmethod
    def notional(self) -> float:
        """Get notional amount."""
        pass

    @abstractmethod
    def currency(self) -> str:
        """Get currency."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(currency={self.currency()}, notional={self.notional()})"


class TradeData:
    """Data associated with a trade."""

    def __init__(self, **kwargs):
        """Initialize trade data."""
        self.data = kwargs

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any):
        self.data[key] = value


class TradeResolver:
    """Resolves trade data."""

    @staticmethod
    def resolve(instrument: Instrument, market: Any) -> TradeData:
        """Resolve trade data from market."""
        return TradeData()
