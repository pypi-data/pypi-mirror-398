"""Portfolio risk aggregation."""

from typing import Dict, Any
from qfinlib.portfolio.portfolio import Portfolio
from qfinlib.market.container import MarketContainer
from qfinlib.risk.calculator import RiskCalculator


def aggregate_risk(
    portfolio: Portfolio, market: MarketContainer, calculator: RiskCalculator
) -> Dict[str, Any]:
    """Aggregate risk metrics across portfolio."""
    # Placeholder - actual implementation would sum risks
    return {}
