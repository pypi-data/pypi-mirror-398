"""
MCard RAG (Retrieval-Augmented Generation) Package

Provides vector search, semantic retrieval, and knowledge graph capabilities
for MCard content using SQLite with sqlite-vec extension and Ollama embeddings.
"""

from .config import RAGConfig, DEFAULT_RAG_CONFIG
from .engine import MCardRAGEngine, RAGResponse
from .indexer import (
    PersistentIndexer, 
    get_indexer, 
    semantic_search, 
    index_mcard
)
from .graph import (
    GraphRAGEngine,
    GraphRAGResponse,
    GraphExtractor,
    GraphStore,
    Entity,
    Relationship,
)
from .semantic_versioning import (
    link_mcard_to_handle,
    get_handle_version_history,
    compare_versions_by_similarity,
    search_within_handle,
    get_version_distances,
    find_most_similar_version,
    get_semantic_evolution,
    list_handles,
    get_store_info,
    get_store,
)
from .vector import (
    HandleVectorStore,
    HandleVersion,
    VersionSimilarityResult,
)

__all__ = [
    # Config
    'RAGConfig',
    'DEFAULT_RAG_CONFIG',
    # Vector RAG
    'MCardRAGEngine',
    'RAGResponse',
    # Persistent Indexer
    'PersistentIndexer',
    'get_indexer',
    'semantic_search',
    'index_mcard',
    # GraphRAG
    'GraphRAGEngine',
    'GraphRAGResponse',
    'GraphExtractor',
    'GraphStore',
    'Entity',
    'Relationship',
    # Semantic Versioning
    'link_mcard_to_handle',
    'get_handle_version_history',
    'compare_versions_by_similarity',
    'search_within_handle',
    'get_version_distances',
    'find_most_similar_version',
    'get_semantic_evolution',
    'list_handles',
    'get_store_info',
    'get_store',
    'HandleVectorStore',
    'HandleVersion',
    'VersionSimilarityResult',
]
