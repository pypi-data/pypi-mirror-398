"""qfinlib - A comprehensive quantitative finance library for hedge fund portfolio management."""

__version__ = "0.2.0"

# Core modules
from qfinlib import date, math, utils

# Market data
from qfinlib import market
from qfinlib.market.container import MarketContainer

# Calibration
from qfinlib import calibration
from qfinlib.calibration.curve.builder import CurveBuilder

# Instruments
from qfinlib import instruments

# Pricing
from qfinlib import pricing
from qfinlib.pricing.engine import PricingEngine

# Risk
from qfinlib import risk
from qfinlib.risk.calculator import RiskCalculator

# Monitoring
from qfinlib import monitoring
from qfinlib.monitoring.scanner import Scanner

# Portfolio
from qfinlib import portfolio
from qfinlib.portfolio.portfolio import Portfolio
from qfinlib.portfolio.position import Position

# Strategy
from qfinlib import strategy
from qfinlib.strategy.generator import StrategyGenerator

__all__ = [
    "__version__",
    "date",
    "math",
    "utils",
    # Market
    "market",
    "MarketContainer",
    # Calibration
    "calibration",
    "CurveBuilder",
    # Instruments
    "instruments",
    # Pricing
    "pricing",
    "PricingEngine",
    # Risk
    "risk",
    "RiskCalculator",
    # Monitoring
    "monitoring",
    "Scanner",
    # Portfolio
    "portfolio",
    "Portfolio",
    "Position",
    # Strategy
    "strategy",
    "StrategyGenerator",
]
