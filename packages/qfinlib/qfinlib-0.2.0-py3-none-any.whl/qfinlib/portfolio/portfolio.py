"""Portfolio class."""

from typing import List, Dict, Any
from qfinlib.portfolio.position import Position


class Portfolio:
    """Represents a portfolio of positions."""

    def __init__(self, name: str = "default"):
        """Initialize portfolio."""
        self.name = name
        self.positions: List[Position] = []

    def add_position(self, instrument, quantity: float = 1.0, entry_price: float = None):
        """Add a position to the portfolio."""
        position = Position(instrument, quantity, entry_price)
        self.positions.append(position)

    def get_positions(self) -> List[Position]:
        """Get all positions."""
        return self.positions

    def __len__(self) -> int:
        return len(self.positions)

    def __repr__(self) -> str:
        return f"Portfolio({self.name}, {len(self.positions)} positions)"
