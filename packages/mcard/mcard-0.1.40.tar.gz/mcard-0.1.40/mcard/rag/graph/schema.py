"""
Graph Database Schema

This module provides graph-specific schemas from the unified schema singleton.

IMPORTANT: All schemas are loaded from schema/mcard_schema.sql
This module provides convenient access to graph-related schemas only.

Usage:
    from mcard.rag.graph.schema import GRAPH_SCHEMAS
    
Or better, use the singleton directly:
    from mcard.schema import MCardSchema
    schema = MCardSchema.get_instance()
    schema.init_graph_tables(conn)
"""

from mcard.schema import MCardSchema


def _get_schema_instance() -> MCardSchema:
    return MCardSchema.get_instance()


def _build_graph_schemas() -> dict:
    """Build GRAPH_SCHEMAS from the unified schema."""
    schema = _get_schema_instance()
    return {
        'entities': schema.get_table('graph_entities'),
        'entity_idx_name': schema.get_index('idx_entity_name'),
        'entity_idx_type': schema.get_index('idx_entity_type'),
        'entity_idx_source': schema.get_index('idx_entity_source'),
        'relationships': schema.get_table('graph_relationships'),
        'rel_idx_source': schema.get_index('idx_rel_source'),
        'rel_idx_target': schema.get_index('idx_rel_target'),
        'communities': schema.get_table('graph_communities'),
        'community_idx_level': schema.get_index('idx_community_level'),
        'extractions': schema.get_table('graph_extractions'),
    }


# Lazy-loaded schema dictionary
_GRAPH_SCHEMAS = None


def __getattr__(name: str):
    """Lazy loading of schema dictionaries."""
    global _GRAPH_SCHEMAS
    
    if name == 'GRAPH_SCHEMAS':
        if _GRAPH_SCHEMAS is None:
            _GRAPH_SCHEMAS = _build_graph_schemas()
        return _GRAPH_SCHEMAS
    
    elif name == 'ENTITY_SCHEMA':
        return _get_schema_instance().get_table('graph_entities')
    
    elif name == 'ENTITY_INDEX_NAME':
        return _get_schema_instance().get_index('idx_entity_name')
    
    elif name == 'ENTITY_INDEX_TYPE':
        return _get_schema_instance().get_index('idx_entity_type')
    
    elif name == 'ENTITY_INDEX_SOURCE':
        return _get_schema_instance().get_index('idx_entity_source')
    
    elif name == 'RELATIONSHIP_SCHEMA':
        return _get_schema_instance().get_table('graph_relationships')
    
    elif name == 'RELATIONSHIP_INDEX_SOURCE':
        return _get_schema_instance().get_index('idx_rel_source')
    
    elif name == 'RELATIONSHIP_INDEX_TARGET':
        return _get_schema_instance().get_index('idx_rel_target')
    
    elif name == 'COMMUNITY_SCHEMA':
        return _get_schema_instance().get_table('graph_communities')
    
    elif name == 'COMMUNITY_INDEX_LEVEL':
        return _get_schema_instance().get_index('idx_community_level')
    
    elif name == 'EXTRACTION_TRACKING_SCHEMA':
        return _get_schema_instance().get_table('graph_extractions')
    
    raise AttributeError(f"module 'mcard.rag.graph.schema' has no attribute '{name}'")


__all__ = [
    'GRAPH_SCHEMAS',
    'ENTITY_SCHEMA',
    'ENTITY_INDEX_NAME',
    'ENTITY_INDEX_TYPE',
    'ENTITY_INDEX_SOURCE',
    'RELATIONSHIP_SCHEMA',
    'RELATIONSHIP_INDEX_SOURCE',
    'RELATIONSHIP_INDEX_TARGET',
    'COMMUNITY_SCHEMA',
    'COMMUNITY_INDEX_LEVEL',
    'EXTRACTION_TRACKING_SCHEMA',
]
