"""MarketContainer."""

from typing import Dict, Any, Optional
from datetime import date


class MarketContainer:
    """Container for market data (curves, surfaces, etc.)."""

    def __init__(self, as_of: Optional[date] = None):
        """Initialize market container."""
        self.as_of = as_of
        self.curves: Dict[str, Any] = {}
        self.surfaces: Dict[str, Any] = {}
        self.data: Dict[str, Any] = {}

    def add_curve(self, name: str, curve: Any):
        """Add a curve to the container."""
        self.curves[name] = curve

    def get_curve(self, name: str) -> Optional[Any]:
        """Get a curve by name."""
        return self.curves.get(name)

    def add_surface(self, name: str, surface: Any):
        """Add a volatility surface to the container."""
        self.surfaces[name] = surface

    def get_surface(self, name: str) -> Optional[Any]:
        """Get a volatility surface by name."""
        return self.surfaces.get(name)

    def __repr__(self) -> str:
        return f"MarketContainer(as_of={self.as_of}, {len(self.curves)} curves, {len(self.surfaces)} surfaces)"
