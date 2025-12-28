"""Curve slope indicator."""

from typing import Optional
from datetime import date
from qfinlib.market.curve.forward import ForwardCurve


def calculate_slope(
    curve: ForwardCurve,
    short_tenor: str = "2Y",
    long_tenor: str = "10Y",
    as_of: Optional[date] = None,
) -> float:
    """Calculate curve slope (long - short rate)."""
    # Placeholder - actual implementation would extract rates from curve
    return 0.0
