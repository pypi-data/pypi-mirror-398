"""
Semantic Versioning API for MCards

High-level API functions for managing MCard versions linked to handles
with semantic similarity detection.

This module provides a simplified interface for:
- Linking MCards to handles
- Retrieving version history with semantic info
- Comparing versions by semantic similarity
- Searching within a handle's version history

See: docs/architecture/Handle_Vector_Similarity_Design.md
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from mcard import MCard
from mcard.rag.vector import (
    HandleVectorStore,
    HandleVersion,
    VersionSimilarityResult,
)
from mcard.rag.config import RAGConfig, DEFAULT_RAG_CONFIG

logger = logging.getLogger(__name__)

# Default store instance (lazy-initialized)
_default_store: Optional[HandleVectorStore] = None


def get_store(
    db_path: str = None,
    config: RAGConfig = None,
    reinitialize: bool = False
) -> HandleVectorStore:
    """
    Get the default HandleVectorStore instance.
    
    Args:
        db_path: Path to SQLite database (None = in-memory)
        config: RAG configuration
        reinitialize: Force re-initialization of the store
        
    Returns:
        HandleVectorStore instance
    """
    global _default_store
    
    if _default_store is None or reinitialize:
        _default_store = HandleVectorStore(
            db_path=db_path,
            config=config or DEFAULT_RAG_CONFIG
        )
    
    return _default_store


# ─────────────────────────────────────────────────────────────────────────────
# Core API Functions
# ─────────────────────────────────────────────────────────────────────────────

def link_mcard_to_handle(
    mcard: MCard, 
    handle: str, 
    is_current: bool = True,
    store: HandleVectorStore = None
) -> bool:
    """
    Link an MCard to a handle with semantic embedding.
    
    This function:
    1. Indexes the MCard content with vector embeddings
    2. Associates the MCard with the specified handle
    3. Computes semantic delta from previous version (if exists)
    4. Classifies the upgrade type based on similarity
    
    Args:
        mcard: MCard to link
        handle: Handle name (stable identifier)
        is_current: Whether this becomes the current version
        store: Optional custom HandleVectorStore instance
        
    Returns:
        True if successful, False if indexing failed
        
    Example:
        >>> from mcard import MCard
        >>> doc = MCard(content="Introduction to Machine Learning...")
        >>> link_mcard_to_handle(doc, "ml_intro")
        True
    """
    store = store or get_store()
    indexed = store.index_with_handle(mcard, handle, is_current=is_current)
    return indexed > 0


def get_handle_version_history(
    handle: str,
    store: HandleVectorStore = None
) -> List[Dict]:
    """
    Get version history for a handle with semantic info.
    
    Args:
        handle: Handle name to query
        store: Optional custom HandleVectorStore instance
        
    Returns:
        List of version dicts with hash, order, timestamps, 
        embedding status, and upgrade type
        
    Example:
        >>> history = get_handle_version_history("ml_intro")
        >>> for v in history:
        ...     print(f"v{v['version_order']}: {v['hash'][:8]} ({v['upgrade_type']})")
    """
    store = store or get_store()
    versions = store.get_handle_versions(handle)
    
    return [
        {
            'hash': v.hash,
            'version_order': v.version_order,
            'is_current': v.is_current,
            'created_at': v.created_at,
            'has_embedding': v.has_embedding,
            'parent_hash': v.parent_hash,
            'semantic_delta': v.semantic_delta,
            'upgrade_type': v.upgrade_type,
        }
        for v in versions
    ]


def compare_versions_by_similarity(
    handle: str,
    reference_hash: str = None,
    metric: str = 'cosine',
    store: HandleVectorStore = None
) -> List[VersionSimilarityResult]:
    """
    Compare all versions of a handle by semantic similarity.
    
    This is useful for:
    - Understanding how content has evolved
    - Finding which version is most similar to current
    - Identifying major semantic drift points
    
    Args:
        handle: Handle name
        reference_hash: Compare to this hash (default: current version)
        metric: 'cosine' (higher = more similar) or 'euclidean' (lower = closer)
        store: Optional custom HandleVectorStore instance
        
    Returns:
        Versions sorted by similarity to reference
        
    Example:
        >>> results = compare_versions_by_similarity("ml_intro")
        >>> for r in results:
        ...     print(f"v{r.version_order}: sim={r.similarity_to_current:.4f}")
    """
    store = store or get_store()
    return store.get_versions_by_similarity(
        handle=handle,
        reference_hash=reference_hash,
        metric=metric
    )


def search_within_handle(
    handle: str, 
    query: str, 
    k: int = 10,
    store: HandleVectorStore = None
) -> List[VersionSimilarityResult]:
    """
    Search semantically within a handle's version history.
    
    Useful for finding which version of a document best matches
    a specific concept, topic, or query.
    
    Args:
        handle: Handle name to filter by
        query: Search query text
        k: Number of results to return
        store: Optional custom HandleVectorStore instance
        
    Returns:
        Matching versions sorted by query similarity
        
    Example:
        >>> results = search_within_handle("ml_intro", "neural networks")
        >>> for r in results:
        ...     print(f"v{r.version_order}: query_sim={r.similarity_to_query:.4f}")
    """
    store = store or get_store()
    return store.search_handle_versions(handle=handle, query=query, k=k)


def get_version_distances(
    handle: str,
    cache: bool = True,
    store: HandleVectorStore = None
) -> Dict[tuple, float]:
    """
    Compute pairwise semantic distances between all versions.
    
    Returns a dictionary mapping (hash_a, hash_b) tuples to 
    their cosine similarity scores.
    
    Args:
        handle: Handle name
        cache: Whether to cache computed similarities
        store: Optional custom HandleVectorStore instance
        
    Returns:
        Dict mapping (hash_a, hash_b) to cosine similarity [-1, 1]
        
    Example:
        >>> distances = get_version_distances("ml_intro")
        >>> for (h1, h2), sim in distances.items():
        ...     print(f"{h1[:8]} <-> {h2[:8]}: {sim:.4f}")
    """
    store = store or get_store()
    return store.compute_version_distances(handle=handle, cache=cache)


def find_most_similar_version(
    handle: str,
    query: str,
    store: HandleVectorStore = None
) -> Optional[VersionSimilarityResult]:
    """
    Find the version most similar to a query.
    
    Args:
        handle: Handle name
        query: Search query text
        store: Optional custom HandleVectorStore instance
        
    Returns:
        Most similar version, or None if no versions exist
    """
    results = search_within_handle(handle, query, k=1, store=store)
    return results[0] if results else None


def get_semantic_evolution(
    handle: str,
    store: HandleVectorStore = None
) -> List[Dict]:
    """
    Get the semantic evolution of a handle's versions.
    
    Returns version history annotated with semantic deltas,
    showing how content has evolved over time.
    
    Args:
        handle: Handle name
        store: Optional custom HandleVectorStore instance
        
    Returns:
        List of version dicts with evolution info
    """
    store = store or get_store()
    versions = store.get_handle_versions(handle)
    
    evolution = []
    for v in versions:
        entry = {
            'hash': v.hash,
            'version': v.version_order,
            'is_current': v.is_current,
            'created_at': v.created_at,
        }
        
        if v.parent_hash:
            entry['parent_hash'] = v.parent_hash
            entry['semantic_delta'] = v.semantic_delta
            entry['upgrade_type'] = v.upgrade_type
            
            # Interpret the delta
            if v.semantic_delta:
                if v.semantic_delta >= 0.95:
                    entry['interpretation'] = 'Nearly identical to parent'
                elif v.semantic_delta >= 0.85:
                    entry['interpretation'] = 'Minor changes from parent'
                elif v.semantic_delta >= 0.70:
                    entry['interpretation'] = 'Significant changes from parent'
                else:
                    entry['interpretation'] = 'Major semantic shift from parent'
        else:
            entry['interpretation'] = 'Initial version (no parent)'
        
        evolution.append(entry)
    
    return evolution


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def list_handles(store: HandleVectorStore = None) -> List[str]:
    """
    List all handles with indexed versions.
    
    Args:
        store: Optional custom HandleVectorStore instance
        
    Returns:
        List of handle names
    """
    store = store or get_store()
    return store.list_handles()


def get_store_info(store: HandleVectorStore = None) -> Dict:
    """
    Get information about the vector store.
    
    Args:
        store: Optional custom HandleVectorStore instance
        
    Returns:
        Dict with store statistics
    """
    store = store or get_store()
    return store.get_info()
