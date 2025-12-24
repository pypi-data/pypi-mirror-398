"""
Vector Store Package

SQLite-based vector storage using sqlite-vec extension.
Includes handle-aware semantic versioning support.
"""

from .store import MCardVectorStore, VectorSearchResult
from .schema import VECTOR_SCHEMAS, HANDLE_VECTOR_SCHEMAS
from .handle_vector_store import (
    HandleVectorStore,
    HandleVersion,
    VersionSimilarityResult,
    classify_upgrade_type,
)

__all__ = [
    # Core vector store
    'MCardVectorStore',
    'VectorSearchResult',
    'VECTOR_SCHEMAS',
    # Handle-aware semantic versioning
    'HandleVectorStore',
    'HandleVersion',
    'VersionSimilarityResult',
    'HANDLE_VECTOR_SCHEMAS',
    'classify_upgrade_type',
]

