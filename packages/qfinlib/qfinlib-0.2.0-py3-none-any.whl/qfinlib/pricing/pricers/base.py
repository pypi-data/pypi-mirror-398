"""Base pricer class."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import date
from qfinlib.instruments.base import Instrument
from qfinlib.market.container import MarketContainer


class Pricer(ABC):
    """Base class for all pricers."""

    @abstractmethod
    def price(
        self, instrument: Instrument, market: MarketContainer, as_of: Optional[date] = None
    ) -> Any:
        """Price an instrument."""
        pass
