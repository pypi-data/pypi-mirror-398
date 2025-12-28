"""Base screen class."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from qfinlib.market.container import MarketContainer


class Screen(ABC):
    """Base class for strategy screens."""

    @abstractmethod
    def screen(self, market: MarketContainer, **kwargs) -> List[Dict[str, Any]]:
        """Screen market for opportunities."""
        pass
