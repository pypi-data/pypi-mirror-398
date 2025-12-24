# mcard/model/schema.py
"""
DEPRECATED: This module is a backward-compatibility shim.

All schemas are now loaded from the singleton:
    from mcard.schema import MCardSchema
    schema = MCardSchema.get_instance()

The single source of truth is: schema/mcard_schema.sql

WHY THIS FILE EXISTS:
---------------------
This file exists only for backward compatibility with legacy imports like:
    from mcard.model.schema import CARD_TABLE_SCHEMA

New code should import directly from mcard.schema:
    from mcard.schema import MCardSchema, get_schema

This file will be removed in a future version.
"""

import warnings

# Issue deprecation warning on import
warnings.warn(
    "mcard.model.schema is deprecated. Use mcard.schema instead. "
    "See schema/mcard_schema.sql for the single source of truth.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the unified schema singleton
from mcard.schema import (
    CARD_TABLE_SCHEMA,
    HANDLE_REGISTRY_SCHEMA,
    HANDLE_HISTORY_SCHEMA,
    HANDLE_INDEX_SCHEMA,
    MCardSchema,
    get_schema,
    init_all_tables,
    init_core_tables,
    init_handle_tables,
)

__all__ = [
    'CARD_TABLE_SCHEMA',
    'HANDLE_REGISTRY_SCHEMA',
    'HANDLE_HISTORY_SCHEMA',
    'HANDLE_INDEX_SCHEMA',
    'MCardSchema',
    'get_schema',
    'init_all_tables',
    'init_core_tables',
    'init_handle_tables',
]
