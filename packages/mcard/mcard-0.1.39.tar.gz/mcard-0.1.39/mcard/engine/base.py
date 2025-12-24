from abc import ABC, abstractmethod
from typing import Optional, Protocol

from mcard.model.card import MCard
from mcard.model.pagination import Page


class DatabaseConnection(Protocol):
    """Protocol for database connections"""

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class StorageEngine(ABC):
    """Abstract base class for storage engines"""

    @abstractmethod
    def add(self, card: MCard) -> str:
        """Add a card and return its hash"""
        pass

    @abstractmethod
    def get(self, hash_value: str) -> Optional[MCard]:
        """Retrieve a card by its hash"""
        pass

    @abstractmethod
    def delete(self, hash_value: str) -> bool:
        """Delete a card by its hash"""
        pass

    @abstractmethod
    def get_page(self, page_number: int, page_size: int) -> Page:
        """Get a page of cards"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all cards"""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of cards"""
        pass
