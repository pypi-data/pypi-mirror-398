"""Market data loader."""

from typing import Optional
from datetime import date
from qfinlib.market.container import MarketContainer
from qfinlib.market.data.provider import DataProvider


class DataLoader:
    """Loads market data from providers into MarketContainer."""

    def __init__(self, provider: DataProvider):
        """Initialize with a data provider."""
        self.provider = provider

    def load(self, as_of: Optional[date] = None) -> MarketContainer:
        """Load all market data into a MarketContainer."""
        # This is a placeholder - actual implementation would load from provider
        return MarketContainer()
