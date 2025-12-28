"""Position class."""

from typing import Optional
from qfinlib.instruments.base import Instrument


class Position:
    """Represents a position in an instrument."""

    def __init__(
        self, instrument: Instrument, quantity: float = 1.0, entry_price: Optional[float] = None
    ):
        """Initialize position."""
        self.instrument = instrument
        self.quantity = quantity
        self.entry_price = entry_price

    def __repr__(self) -> str:
        return f"Position({self.instrument}, qty={self.quantity})"
