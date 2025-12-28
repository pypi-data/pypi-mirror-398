"""Strategy idea generator."""

from typing import List, Dict, Any, Optional
from datetime import date
from qfinlib.market.container import MarketContainer
from qfinlib.monitoring.scanner import Scanner


class StrategyGenerator:
    """Generates trading strategy ideas."""

    def __init__(self, market: MarketContainer):
        """Initialize with market data."""
        self.market = market
        self.scanner = Scanner(market)

    def generate_carry_ideas(
        self,
        currencies: Optional[List[str]] = None,
        min_carry: float = 0.3,
        as_of: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Generate carry trade ideas."""
        return self.scanner.scan_carry_trades(currencies, min_carry, as_of)

    def generate_curve_ideas(
        self,
        currencies: Optional[List[str]] = None,
        min_slope: float = 0.2,
        as_of: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Generate curve trade ideas."""
        return self.scanner.scan_curve_trades(currencies, min_slope, as_of)

    def generate_vol_ideas(
        self,
        currencies: Optional[List[str]] = None,
        min_skew: float = 0.15,
        as_of: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Generate volatility trade ideas."""
        return self.scanner.scan_vol_trades(currencies, min_skew, as_of)
