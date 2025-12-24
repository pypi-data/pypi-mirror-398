"""
Operations Module for Python Runtime
=====================================

This module provides a modular, pluggable architecture for PythonRuntime operations.
Each operation is a callable that takes (impl, target, ctx) and returns a result.

Operations are organized by category:
- base: Protocol definitions and utilities
- builtins: Core operations (identity, arithmetic, string, etc.)
- handle: Handle versioning and pruning
- loader: File ingestion operations
"""

from .base import Operation, OperationRegistry, ExampleRunnerMixin
from .builtins import (
    op_identity,
    op_transform,
    op_arithmetic,
    op_string,
    op_fetch_url,
    op_session_record,
)
from .handle import (
    op_handle_version,
    op_handle_prune,
)
from .loader import op_loader

# Default operation registry with all built-in operations
DEFAULT_OPERATIONS = {
    'identity': op_identity,
    'transform': op_transform,
    'arithmetic': op_arithmetic,
    'string_op': op_string,
    'fetch_url': op_fetch_url,
    'loader': op_loader,
    'ingest_files': op_loader,
    'load_files': op_loader,
    'session_record': op_session_record,
    'handle_version': op_handle_version,
    'handle_prune': op_handle_prune,
}

__all__ = [
    'Operation',
    'OperationRegistry',
    'ExampleRunnerMixin',
    'DEFAULT_OPERATIONS',
    'op_identity',
    'op_transform',
    'op_arithmetic',
    'op_string',
    'op_fetch_url',
    'op_session_record',
    'op_loader',
    'op_handle_version',
    'op_handle_prune',
]
