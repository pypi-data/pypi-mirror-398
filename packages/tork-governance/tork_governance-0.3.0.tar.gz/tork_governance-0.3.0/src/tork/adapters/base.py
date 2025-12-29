"""
Base Adapter

Abstract base class for all governance adapters.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """
    Abstract base class for governance adapters.
    
    Adapters provide integration points between the governance
    engine and various AI agent frameworks or external systems.
    """
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the target system."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the target system."""
        pass
    
    @abstractmethod
    def send_event(self, event: dict[str, Any]) -> None:
        """
        Send a governance event to the target system.
        
        Args:
            event: The event data to send.
        """
        pass
    
    @abstractmethod
    def receive_event(self) -> dict[str, Any] | None:
        """
        Receive a governance event from the target system.
        
        Returns:
            The received event data, or None if no event available.
        """
        pass
