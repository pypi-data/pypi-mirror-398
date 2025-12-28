"""Valuation module (alias to pricing)."""

from qfinlib import pricing

calculator = pricing.calculator
cashflow = pricing.cashflow
priceable = pricing.priceable
pricers = pricing.pricers
results = pricing.results

__all__ = [
    "pricing",
    "calculator",
    "cashflow",
    "priceable",
    "pricers",
    "results",
]
