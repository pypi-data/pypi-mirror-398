"""Unified curve builder interface."""

from typing import Optional, List, Any
from datetime import date
from qfinlib.market.curve import DiscountCurve, ForwardCurve
from qfinlib.market.container import MarketContainer

# Try to import engine, but make it optional
try:
    from qfinlib.calibration.curve.engine import CurveCalibrationEngine
except ImportError:

    class CurveCalibrationEngine:
        """Placeholder calibration engine."""

        pass


class CurveBuilder:
    """Unified interface for building curves."""

    def __init__(self, market: MarketContainer):
        """Initialize with market data."""
        self.market = market
        self.engine = CurveCalibrationEngine()

    def build_discount_curve(
        self, currency: str, instruments: Optional[List] = None, as_of: Optional[date] = None
    ) -> DiscountCurve:
        """Build a discount curve for a currency."""
        # Placeholder - actual implementation would use calibration engine
        return DiscountCurve()

    def build_forward_curve(
        self,
        currency: str,
        index: str,
        instruments: Optional[List] = None,
        as_of: Optional[date] = None,
    ) -> ForwardCurve:
        """Build a forward curve for a currency and index."""
        # Placeholder - actual implementation would use calibration engine
        return ForwardCurve()
