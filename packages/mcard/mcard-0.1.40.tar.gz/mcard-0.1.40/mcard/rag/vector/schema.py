"""
Vector Store Database Schema

This module provides vector-specific schemas from the unified schema singleton.

IMPORTANT: All schemas are loaded from schema/mcard_schema.sql
This module provides convenient access to vector-related schemas only.

Usage:
    from mcard.rag.vector.schema import VECTOR_SCHEMAS, HANDLE_VECTOR_SCHEMAS
    
Or better, use the singleton directly:
    from mcard.schema import MCardSchema
    schema = MCardSchema.get_instance()
    schema.init_vector_tables(conn)
"""

from mcard.schema import MCardSchema, get_schema


# Get singleton instance
def _get_schema_instance() -> MCardSchema:
    return MCardSchema.get_instance()


# ─────────────────────────────────────────────────────────────────────────────
# Vector Schemas (from unified schema file)
# ─────────────────────────────────────────────────────────────────────────────

def _build_vector_schemas() -> dict:
    """Build VECTOR_SCHEMAS from the unified schema."""
    schema = _get_schema_instance()
    return {
        'metadata': schema.get_table('mcard_vector_metadata'),
        'metadata_index': schema.get_index('idx_vector_metadata_hash'),
        'embeddings': schema.get_table('mcard_embeddings'),
        'fts': schema.get_table('mcard_fts'),
    }


def _build_handle_vector_schemas() -> dict:
    """Build HANDLE_VECTOR_SCHEMAS from the unified schema."""
    schema = _get_schema_instance()
    
    # Get indexes for handle_version_vectors
    hvv_indexes = []
    for idx_name in ['idx_hvv_handle', 'idx_hvv_hash', 'idx_hvv_current', 'idx_hvv_parent']:
        idx = schema.get_index(idx_name)
        if idx:
            hvv_indexes.append(idx)
    
    return {
        'handle_version_vectors': schema.get_table('handle_version_vectors'),
        'handle_version_vectors_indexes': '; '.join(hvv_indexes),
        'similarity_cache': schema.get_table('version_similarity_cache'),
        'similarity_cache_index': schema.get_index('idx_vsc_handle'),
    }


# Lazy-loaded schema dictionaries
_VECTOR_SCHEMAS = None
_HANDLE_VECTOR_SCHEMAS = None


def __getattr__(name: str):
    """Lazy loading of schema dictionaries."""
    global _VECTOR_SCHEMAS, _HANDLE_VECTOR_SCHEMAS
    
    if name == 'VECTOR_SCHEMAS':
        if _VECTOR_SCHEMAS is None:
            _VECTOR_SCHEMAS = _build_vector_schemas()
        return _VECTOR_SCHEMAS
    
    elif name == 'HANDLE_VECTOR_SCHEMAS':
        if _HANDLE_VECTOR_SCHEMAS is None:
            _HANDLE_VECTOR_SCHEMAS = _build_handle_vector_schemas()
        return _HANDLE_VECTOR_SCHEMAS
    
    elif name == 'VECTOR_METADATA_SCHEMA':
        return _get_schema_instance().get_table('mcard_vector_metadata')
    
    elif name == 'VECTOR_METADATA_INDEX':
        return _get_schema_instance().get_index('idx_vector_metadata_hash')
    
    elif name == 'VECTOR_EMBEDDINGS_SCHEMA':
        return _get_schema_instance().get_table('mcard_embeddings')
    
    elif name == 'FTS_SCHEMA':
        return _get_schema_instance().get_table('mcard_fts')
    
    elif name == 'HANDLE_VERSION_VECTORS_SCHEMA':
        return _get_schema_instance().get_table('handle_version_vectors')
    
    elif name == 'VERSION_SIMILARITY_CACHE_SCHEMA':
        return _get_schema_instance().get_table('version_similarity_cache')
    
    raise AttributeError(f"module 'mcard.rag.vector.schema' has no attribute '{name}'")


def get_vec0_schema(dimensions: int) -> str:
    """
    Generate sqlite-vec virtual table schema.
    
    Note: This is dynamically generated because dimensions vary.
    
    Args:
        dimensions: Embedding vector dimensions
        
    Returns:
        SQL CREATE VIRTUAL TABLE statement
    """
    return f"""
    CREATE VIRTUAL TABLE IF NOT EXISTS mcard_vec USING vec0(
        metadata_id INTEGER PRIMARY KEY,
        embedding float[{dimensions}]
    )
    """


__all__ = [
    # Schema dictionaries
    'VECTOR_SCHEMAS',
    'HANDLE_VECTOR_SCHEMAS',
    # Individual schemas
    'VECTOR_METADATA_SCHEMA',
    'VECTOR_METADATA_INDEX',
    'VECTOR_EMBEDDINGS_SCHEMA',
    'FTS_SCHEMA',
    'HANDLE_VERSION_VECTORS_SCHEMA',
    'VERSION_SIMILARITY_CACHE_SCHEMA',
    # Functions
    'get_vec0_schema',
]
