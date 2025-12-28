"""Financial instruments module."""

try:
    from qfinlib.instruments.base import Instrument, TradeData, TradeResolver
except ImportError:
    # Fallback to old location
    from qfinlib.trade.base import Instrument, TradeData, TradeResolver

from qfinlib.instruments import rates, bond, credit, fx

__all__ = ["Instrument", "TradeData", "TradeResolver", "rates", "bond", "credit", "fx"]
