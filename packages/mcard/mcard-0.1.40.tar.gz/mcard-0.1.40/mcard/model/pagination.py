"""Pagination support for MCard collections."""
from dataclasses import dataclass
from typing import List, TypeVar, Generic, Optional

T = TypeVar('T')

@dataclass
class Page(Generic[T]):
    """A page of search results."""
    items: List[T]
    page_number: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @property
    def next_page_number(self) -> Optional[int]:
        """Get the next page number, or None if this is the last page."""
        return self.page_number + 1 if self.has_next else None

    @property
    def previous_page_number(self) -> Optional[int]:
        """Get the previous page number, or None if this is the first page."""
        return self.page_number - 1 if self.has_previous else None
