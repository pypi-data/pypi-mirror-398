"""Base alert class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class Alert(ABC):
    """Base class for market alerts."""

    def __init__(self, message: str, severity: str = "info", timestamp: Optional[datetime] = None):
        """Initialize alert."""
        self.message = message
        self.severity = severity  # info, warning, error
        self.timestamp = timestamp or datetime.now()
        self.data: Dict[str, Any] = {}

    @abstractmethod
    def check(self, market_data: Any) -> bool:
        """Check if alert condition is met."""
        pass

    def __repr__(self) -> str:
        return f"Alert({self.severity}: {self.message})"
