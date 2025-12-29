"""
Receipt Store

Abstract base class and implementations for storing compliance receipts.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
import structlog

from tork.compliance.receipts import PolicyReceipt

logger = structlog.get_logger(__name__)


class ReceiptStore(ABC):
    """
    Abstract base class for receipt storage.
    
    Defines the interface for saving and retrieving compliance receipts.
    """
    
    @abstractmethod
    def save(self, receipt: PolicyReceipt) -> None:
        """
        Save a receipt to the store.
        
        Args:
            receipt: The receipt to save.
        """
        pass
    
    @abstractmethod
    def get(self, receipt_id: str) -> Optional[PolicyReceipt]:
        """
        Retrieve a receipt by ID.
        
        Args:
            receipt_id: The receipt ID to look up.
            
        Returns:
            The receipt if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def list_by_agent(self, agent_id: str, limit: int = 100) -> list[PolicyReceipt]:
        """
        List receipts for a specific agent.
        
        Args:
            agent_id: The agent ID to filter by.
            limit: Maximum number of receipts to return.
            
        Returns:
            List of receipts for the agent.
        """
        pass
    
    @abstractmethod
    def list_by_date_range(self, start: datetime, end: datetime) -> list[PolicyReceipt]:
        """
        List receipts within a date range.
        
        Args:
            start: Start of date range (inclusive).
            end: End of date range (inclusive).
            
        Returns:
            List of receipts within the range.
        """
        pass


class MemoryReceiptStore(ReceiptStore):
    """
    In-memory receipt store for testing and development.
    
    Stores receipts in a dictionary keyed by receipt_id.
    """
    
    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._receipts: dict[str, PolicyReceipt] = {}
        logger.info("MemoryReceiptStore initialized")
    
    def save(self, receipt: PolicyReceipt) -> None:
        """Save a receipt to memory."""
        self._receipts[receipt.receipt_id] = receipt
        logger.debug("Receipt saved to memory", receipt_id=receipt.receipt_id)
    
    def get(self, receipt_id: str) -> Optional[PolicyReceipt]:
        """Retrieve a receipt by ID."""
        return self._receipts.get(receipt_id)
    
    def list_by_agent(self, agent_id: str, limit: int = 100) -> list[PolicyReceipt]:
        """List receipts for a specific agent."""
        receipts = [
            r for r in self._receipts.values()
            if r.agent_id == agent_id
        ]
        receipts.sort(key=lambda r: r.timestamp, reverse=True)
        return receipts[:limit]
    
    def list_by_date_range(self, start: datetime, end: datetime) -> list[PolicyReceipt]:
        """List receipts within a date range."""
        receipts = [
            r for r in self._receipts.values()
            if start <= r.timestamp <= end
        ]
        receipts.sort(key=lambda r: r.timestamp)
        return receipts
    
    def clear(self) -> None:
        """Clear all receipts from memory."""
        self._receipts.clear()
        logger.debug("Memory store cleared")
    
    @property
    def count(self) -> int:
        """Return number of stored receipts."""
        return len(self._receipts)


class FileReceiptStore(ReceiptStore):
    """
    File-based receipt store using JSON files.
    
    Stores each receipt as a separate JSON file named {receipt_id}.json
    in the specified storage directory.
    """
    
    def __init__(self, storage_dir: str) -> None:
        """
        Initialize the file-based store.
        
        Args:
            storage_dir: Directory path for storing receipt files.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info("FileReceiptStore initialized", storage_dir=str(self.storage_dir))
    
    def _receipt_path(self, receipt_id: str) -> Path:
        """Get the file path for a receipt."""
        return self.storage_dir / f"{receipt_id}.json"
    
    def save(self, receipt: PolicyReceipt) -> None:
        """Save a receipt to a JSON file."""
        path = self._receipt_path(receipt.receipt_id)
        with open(path, 'w') as f:
            json.dump(receipt.model_dump(mode='json'), f, indent=2, default=str)
        logger.debug("Receipt saved to file", receipt_id=receipt.receipt_id, path=str(path))
    
    def get(self, receipt_id: str) -> Optional[PolicyReceipt]:
        """Retrieve a receipt by ID from file."""
        path = self._receipt_path(receipt_id)
        if not path.exists():
            return None
        
        with open(path) as f:
            data = json.load(f)
        
        return PolicyReceipt(**data)
    
    def list_by_agent(self, agent_id: str, limit: int = 100) -> list[PolicyReceipt]:
        """List receipts for a specific agent."""
        receipts = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("agent_id") == agent_id:
                    receipts.append(PolicyReceipt(**data))
            except (json.JSONDecodeError, KeyError):
                logger.warning("Invalid receipt file", path=str(path))
                continue
        
        receipts.sort(key=lambda r: r.timestamp, reverse=True)
        return receipts[:limit]
    
    def list_by_date_range(self, start: datetime, end: datetime) -> list[PolicyReceipt]:
        """List receipts within a date range."""
        receipts = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                receipt = PolicyReceipt(**data)
                if start <= receipt.timestamp <= end:
                    receipts.append(receipt)
            except (json.JSONDecodeError, KeyError):
                logger.warning("Invalid receipt file", path=str(path))
                continue
        
        receipts.sort(key=lambda r: r.timestamp)
        return receipts
    
    def delete(self, receipt_id: str) -> bool:
        """
        Delete a receipt file.
        
        Args:
            receipt_id: The receipt ID to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        path = self._receipt_path(receipt_id)
        if path.exists():
            os.remove(path)
            logger.debug("Receipt deleted", receipt_id=receipt_id)
            return True
        return False
    
    @property
    def count(self) -> int:
        """Return number of stored receipts."""
        return len(list(self.storage_dir.glob("*.json")))
