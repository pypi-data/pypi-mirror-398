"""Unified pricing engine."""

from typing import Any, Optional
from datetime import date
from qfinlib.market.container import MarketContainer
from qfinlib.instruments.base import Instrument
from qfinlib.pricing.pricers.base import Pricer


class PricingEngine:
    """Unified pricing engine for all instruments."""

    def __init__(self, market: MarketContainer):
        """Initialize with market data."""
        self.market = market
        self._pricers: dict[str, Pricer] = {}

    def price(self, instrument: Instrument, as_of: Optional[date] = None) -> Any:
        """Price an instrument."""
        pricer = self._get_pricer(instrument)
        return pricer.price(instrument, self.market, as_of)

    def _get_pricer(self, instrument: Instrument) -> Pricer:
        """Get the appropriate pricer for an instrument."""
        instrument_type = type(instrument).__name__
        if instrument_type not in self._pricers:
            # Lazy load pricer based on instrument type
            self._pricers[instrument_type] = self._create_pricer(instrument)
        return self._pricers[instrument_type]

    def _create_pricer(self, instrument: Instrument) -> Pricer:
        """Create a pricer for an instrument type."""
        # This would map instrument types to pricers
        # Placeholder implementation
        from qfinlib.pricing.pricers.base import Pricer

        return Pricer()
