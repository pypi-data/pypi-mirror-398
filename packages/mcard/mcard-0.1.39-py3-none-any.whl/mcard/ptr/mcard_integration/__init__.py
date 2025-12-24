"""
MCard Integration Module

Integration layer for using MCard Collections with PTR for
content-addressable storage and dynamic CLM assembly.
"""

from .collection_manager import CollectionManager
from .storage import MCardStorage

__all__ = ["MCardStorage", "CollectionManager"]
