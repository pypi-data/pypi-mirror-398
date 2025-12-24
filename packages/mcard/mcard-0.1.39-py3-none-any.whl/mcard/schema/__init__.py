"""
MCard Unified Schema Loader (Singleton)

This module provides the ONLY access point to MCard database schemas.
All schemas are loaded from: schema/mcard_schema.sql

This implements a Singleton pattern to ensure:
1. Schema file is read only once
2. All code uses the same schema definitions
3. NO duplicate CREATE TABLE statements exist elsewhere

IMPORTANT: The SQL file MUST exist. There are no fallbacks.
If the file is missing, an explicit error is raised.

Usage:
    from mcard.schema import MCardSchema
    
    # Get the singleton instance
    schema = MCardSchema.get_instance()
    
    # Get a specific table's CREATE statement
    card_schema = schema.get_table('card')
    
    # Initialize all tables on a connection
    schema.init_all_tables(conn)

Single Source of Truth:
    schema/mcard_schema.sql
    
See: docs/architecture/Handle_Vector_Similarity_Design.md
"""

import sqlite3
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Schema File Location
# ─────────────────────────────────────────────────────────────────────────────

def _find_schema_path() -> Path:
    """
    Find the path to the unified core schema file.
    
    Raises FileNotFoundError if the schema file cannot be found.
    There is NO fallback - the SQL file MUST exist.
    """
    module_dir = Path(__file__).parent
    
    # Path patterns to try (in order of preference)
    paths_to_try = [
        module_dir.parent.parent / "schema" / "mcard_schema.sql",  # mcard/schema -> project root
        module_dir.parent / "schema" / "mcard_schema.sql",
        Path.cwd() / "schema" / "mcard_schema.sql",
    ]
    
    for path in paths_to_try:
        if path.exists():
            return path.resolve()
    
    raise FileNotFoundError(
        "CRITICAL: Could not find schema/mcard_schema.sql\n"
        "This file is the SINGLE SOURCE OF TRUTH for all MCard database schemas.\n"
        "There are NO fallbacks - please ensure the file exists.\n\n"
        f"Tried locations:\n" + "\n".join(f"  - {p}" for p in paths_to_try)
    )

def _find_vector_schema_path() -> Optional[Path]:
    """
    Find the path to the vector schema file (mcard_vector_schema.sql).
    Returns None if not found (optional).
    """
    module_dir = Path(__file__).parent
    
    # Path patterns to try (in order of preference)
    paths_to_try = [
        module_dir.parent.parent / "schema" / "mcard_vector_schema.sql",
        module_dir.parent / "schema" / "mcard_vector_schema.sql",
        Path.cwd() / "schema" / "mcard_vector_schema.sql",
    ]
    
    for path in paths_to_try:
        if path.exists():
            return path.resolve()
            
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Singleton Schema Manager
# ─────────────────────────────────────────────────────────────────────────────

class MCardSchema:
    """
    Singleton class for MCard database schema management.
    
    This class ensures that ALL schema definitions come exclusively from:
        schema/mcard_schema.sql
    
    There are NO hardcoded SQL fallbacks in this class.
    
    Thread-safe singleton implementation.
    
    Usage:
        schema = MCardSchema.get_instance()
        schema.get_table('card')  # Get CREATE TABLE statement
        schema.init_core_tables(conn)  # Initialize core tables
    """
    
    _instance: Optional['MCardSchema'] = None
    _lock = threading.Lock()
    
    # Table-to-layer mapping (defines the architecture)
    TABLE_LAYERS = {
        # Layer 1: Core
        'card': 'core',
        'documents': 'core',  # Legacy FTS table for backward compatibility
        # Layer 2: Handle System
        'handle_registry': 'handle',
        'handle_history': 'handle',
        # Layer 3: Vector Storage
        'mcard_vector_metadata': 'vector',
        'mcard_embeddings': 'vector',
        'mcard_fts': 'vector',
        # Layer 4: Semantic Versioning
        'handle_version_vectors': 'semantic',
        'version_similarity_cache': 'semantic',
        # Layer 5: Knowledge Graph
        'graph_entities': 'graph',
        'graph_relationships': 'graph',
        'graph_communities': 'graph',
        'graph_extractions': 'graph',
        # Metadata
        'schema_version': 'metadata',
    }
    
    def __init__(self):
        """Private constructor - use get_instance() instead."""
        self._schema_path: Optional[Path] = None
        self._raw_sql: Optional[str] = None
        self._statements: Optional[List[str]] = None
        self._tables: Optional[Dict[str, str]] = None
        self._indexes: Optional[Dict[str, str]] = None
        self._loaded = False
    
    @classmethod
    def get_instance(cls) -> 'MCardSchema':
        """
        Get the singleton instance of MCardSchema.
        
        Thread-safe lazy initialization.
        
        Returns:
            The single MCardSchema instance
            
        Raises:
            FileNotFoundError: If schema/mcard_schema.sql cannot be found
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = cls()
                    cls._instance._load()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (primarily for testing)."""
        with cls._lock:
            cls._instance = None
    
    def _load(self) -> None:
        """Load and parse the schema file(s)."""
        if self._loaded:
            return
        
        # Find and read the core schema file (raises if not found)
        self._schema_path = _find_schema_path()
        self._raw_sql = self._schema_path.read_text(encoding='utf-8')
        
        # Try to load vector schema
        vector_schema_path = _find_vector_schema_path()
        if vector_schema_path:
            vector_sql = vector_schema_path.read_text(encoding='utf-8')
            self._raw_sql += "\n\n" + vector_sql
            
        self._statements = self._parse_statements(self._raw_sql)
        self._tables = {}
        self._indexes = {}
        
        for stmt in self._statements:
            name = self._extract_name(stmt)
            if name:
                if 'CREATE TABLE' in stmt.upper() or 'CREATE VIRTUAL TABLE' in stmt.upper():
                    self._tables[name.lower()] = stmt
                elif 'CREATE INDEX' in stmt.upper():
                    self._indexes[name.lower()] = stmt
        
        self._loaded = True
    
    def _parse_statements(self, sql: str) -> List[str]:
        """Parse SQL file into individual statements."""
        # Remove block comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        statements = []
        current = []
        
        for line in sql.split('\n'):
            # Skip line comments and empty lines
            line_stripped = line.split('--')[0].strip()
            if not line_stripped:
                continue
            
            current.append(line_stripped)
            
            if line_stripped.endswith(';'):
                statement = ' '.join(current)
                # Skip INSERT statements (version tracking)
                if not statement.strip().upper().startswith('INSERT'):
                    statements.append(statement)
                current = []
        
        return [s.strip() for s in statements if s.strip()]
    
    def _extract_name(self, statement: str) -> Optional[str]:
        """Extract table or index name from a CREATE statement."""
        # Handle CREATE TABLE
        match = re.search(
            r'CREATE\s+(?:VIRTUAL\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
            statement,
            re.IGNORECASE
        )
        if match:
            return match.group(1)
        
        # Handle CREATE INDEX
        match = re.search(
            r'CREATE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
            statement,
            re.IGNORECASE
        )
        if match:
            return match.group(1)
        
        return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Schema Access
    # ─────────────────────────────────────────────────────────────────────────
    
    @property
    def schema_path(self) -> Path:
        """Get the path to the schema file."""
        return self._schema_path
    
    def get_table(self, table_name: str) -> Optional[str]:
        """
        Get CREATE TABLE statement for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            CREATE TABLE SQL statement, or None if not found
        """
        return self._tables.get(table_name.lower())
    
    def get_index(self, index_name: str) -> Optional[str]:
        """
        Get CREATE INDEX statement for an index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            CREATE INDEX SQL statement, or None if not found
        """
        return self._indexes.get(index_name.lower())
    
    def get_all_tables(self) -> Dict[str, str]:
        """Get all table CREATE statements."""
        return dict(self._tables)
    
    def get_all_indexes(self) -> Dict[str, str]:
        """Get all index CREATE statements."""
        return dict(self._indexes)
    
    def get_all_statements(self) -> List[str]:
        """Get all CREATE statements."""
        return list(self._statements)
    
    def get_tables_by_layer(self, layer: str) -> List[str]:
        """Get table names for a specific layer."""
        return [name for name, l in self.TABLE_LAYERS.items() if l == layer]
    
    def get_layer_statements(self, layer: str) -> List[str]:
        """Get all CREATE statements for a layer (tables + indexes)."""
        statements = []
        tables = self.get_tables_by_layer(layer)
        
        # Add tables
        for table in tables:
            stmt = self.get_table(table)
            if stmt:
                statements.append(stmt)
        
        # Add indexes for these tables
        for idx_name, stmt in self._indexes.items():
            match = re.search(r'ON\s+(\w+)', stmt, re.IGNORECASE)
            if match and match.group(1).lower() in [t.lower() for t in tables]:
                statements.append(stmt)
        
        return statements
    
    # ─────────────────────────────────────────────────────────────────────────
    # Database Initialization
    # ─────────────────────────────────────────────────────────────────────────
    
    def init_layer(self, conn: sqlite3.Connection, layer: str) -> int:
        """
        Initialize tables for a specific layer.
        
        Args:
            conn: SQLite connection
            layer: Layer name
            
        Returns:
            Number of statements executed
        """
        cursor = conn.cursor()
        statements = self.get_layer_statements(layer)
        
        for stmt in statements:
            cursor.execute(stmt)
        
        conn.commit()
        return len(statements)
    
    def init_core_tables(self, conn: sqlite3.Connection) -> int:
        """
        Initialize Monadic Core tables (Card, Handle, Version).
        
        This initializes both 'core' and 'handle' layers, as they constitute
        the minimal functional unit of the MCard system.
        """
        count = self.init_layer(conn, 'core')
        count += self.init_layer(conn, 'handle')
        return count
    
    def init_handle_tables(self, conn: sqlite3.Connection) -> int:
        """Initialize handle system tables."""
        return self.init_layer(conn, 'handle')
    
    def init_vector_tables(self, conn: sqlite3.Connection, enable_fts: bool = True) -> int:
        """Initialize vector storage tables."""
        cursor = conn.cursor()
        count = 0
        
        for stmt in self.get_layer_statements('vector'):
            if not enable_fts and 'fts' in stmt.lower():
                continue
            cursor.execute(stmt)
            count += 1
        
        conn.commit()
        return count
    
    def init_semantic_tables(self, conn: sqlite3.Connection) -> int:
        """Initialize semantic versioning tables."""
        return self.init_layer(conn, 'semantic')
    
    def init_graph_tables(self, conn: sqlite3.Connection) -> int:
        """Initialize knowledge graph tables."""
        return self.init_layer(conn, 'graph')
    
    def init_all_tables(
        self,
        conn: sqlite3.Connection,
        include_fts: bool = True,
        include_graph: bool = True,
        include_semantic: bool = True
    ) -> int:
        """
        Initialize all MCard tables on a database.
        
        Args:
            conn: SQLite connection
            include_fts: Whether to include FTS tables
            include_graph: Whether to include graph tables
            include_semantic: Whether to include semantic versioning tables
            
        Returns:
            Number of statements executed
        """
        count = 0
        count += self.init_core_tables(conn)
        count += self.init_handle_tables(conn)
        count += self.init_vector_tables(conn, enable_fts=include_fts)
        
        if include_semantic:
            count += self.init_semantic_tables(conn)
        
        if include_graph:
            count += self.init_graph_tables(conn)
        
        return count
    
    def init_vec0_table(self, conn: sqlite3.Connection, dimensions: int) -> None:
        """
        Initialize sqlite-vec virtual table.
        
        Note: This is the ONLY dynamically generated schema because
        dimensions are determined at runtime.
        
        Args:
            conn: SQLite connection
            dimensions: Embedding vector dimensions
        """
        conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS mcard_vec USING vec0(
                metadata_id INTEGER PRIMARY KEY,
                embedding float[{dimensions}]
            )
        """)
        conn.commit()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Schema Version Management
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_schema_version(self, conn: sqlite3.Connection) -> Optional[str]:
        """Get the current schema version from the database."""
        try:
            cursor = conn.execute(
                "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.OperationalError:
            return None
    
    def set_schema_version(
        self, 
        conn: sqlite3.Connection, 
        version: str, 
        description: str = ""
    ) -> None:
        """Record a schema version in the database."""
        conn.execute("""
            INSERT OR REPLACE INTO schema_version (version, applied_at, description)
            VALUES (?, datetime('now'), ?)
        """, (version, description))
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions (use singleton internally)
# ─────────────────────────────────────────────────────────────────────────────

def get_instance() -> MCardSchema:
    """Get the singleton MCardSchema instance."""
    return MCardSchema.get_instance()


def get_schema(table_or_index_name: str) -> Optional[str]:
    """Get CREATE statement for a table or index."""
    schema = MCardSchema.get_instance()
    result = schema.get_table(table_or_index_name)
    if result is None:
        result = schema.get_index(table_or_index_name)
    return result


def get_all_statements() -> List[str]:
    """Get all CREATE statements from the schema file."""
    return MCardSchema.get_instance().get_all_statements()


def get_schemas_by_layer(layer: str) -> Dict[str, str]:
    """Get all schemas for a specific layer."""
    schema = MCardSchema.get_instance()
    result = {}
    for table in schema.get_tables_by_layer(layer):
        stmt = schema.get_table(table)
        if stmt:
            result[table] = stmt
    return result


def get_tables_by_layer(layer: str) -> List[str]:
    """Get table names for a specific layer."""
    return MCardSchema.get_instance().get_tables_by_layer(layer)


def init_all_tables(
    conn: sqlite3.Connection,
    include_fts: bool = True,
    include_graph: bool = True
) -> int:
    """Initialize all MCard tables."""
    return MCardSchema.get_instance().init_all_tables(conn, include_fts, include_graph)


def init_core_tables(conn: sqlite3.Connection) -> int:
    """Initialize core tables."""
    return MCardSchema.get_instance().init_core_tables(conn)


def init_handle_tables(conn: sqlite3.Connection) -> int:
    """Initialize handle tables."""
    return MCardSchema.get_instance().init_handle_tables(conn)


def init_vector_tables(conn: sqlite3.Connection, enable_fts: bool = True) -> int:
    """Initialize vector tables."""
    return MCardSchema.get_instance().init_vector_tables(conn, enable_fts)


def init_semantic_tables(conn: sqlite3.Connection) -> int:
    """Initialize semantic versioning tables."""
    return MCardSchema.get_instance().init_semantic_tables(conn)


def init_graph_tables(conn: sqlite3.Connection) -> int:
    """Initialize graph tables."""
    return MCardSchema.get_instance().init_graph_tables(conn)


def init_vec0_table(conn: sqlite3.Connection, dimensions: int) -> None:
    """Initialize sqlite-vec table."""
    MCardSchema.get_instance().init_vec0_table(conn, dimensions)


def get_schema_version(conn: sqlite3.Connection) -> Optional[str]:
    """Get schema version."""
    return MCardSchema.get_instance().get_schema_version(conn)


def set_schema_version(conn: sqlite3.Connection, version: str, description: str = "") -> None:
    """Set schema version."""
    MCardSchema.get_instance().set_schema_version(conn, version, description)


# ─────────────────────────────────────────────────────────────────────────────
# Backward Compatibility Exports
# ─────────────────────────────────────────────────────────────────────────────

# These provide lazy-loaded access to commonly used schemas for backward
# compatibility with code that imports constants like CARD_TABLE_SCHEMA.
#
# IMPORTANT: These load ONLY from the SQL file. There are NO hardcoded fallbacks.
# If the SQL file is missing, an error will be raised.

_CARD_TABLE_SCHEMA: Optional[str] = None
_HANDLE_REGISTRY_SCHEMA: Optional[str] = None
_HANDLE_HISTORY_SCHEMA: Optional[str] = None
_HANDLE_INDEX_SCHEMA: Optional[str] = None


def __getattr__(name: str):
    """
    Lazy attribute access for backward compatibility constants.
    
    All schemas are loaded from schema/mcard_schema.sql.
    There are NO hardcoded fallbacks - the SQL file MUST exist.
    """
    global _CARD_TABLE_SCHEMA, _HANDLE_REGISTRY_SCHEMA, _HANDLE_HISTORY_SCHEMA, _HANDLE_INDEX_SCHEMA
    
    schema = MCardSchema.get_instance()
    
    if name == 'CARD_TABLE_SCHEMA':
        if _CARD_TABLE_SCHEMA is None:
            _CARD_TABLE_SCHEMA = schema.get_table('card')
        return _CARD_TABLE_SCHEMA
    
    elif name == 'HANDLE_REGISTRY_SCHEMA':
        if _HANDLE_REGISTRY_SCHEMA is None:
            _HANDLE_REGISTRY_SCHEMA = schema.get_table('handle_registry')
        return _HANDLE_REGISTRY_SCHEMA
    
    elif name == 'HANDLE_HISTORY_SCHEMA':
        if _HANDLE_HISTORY_SCHEMA is None:
            _HANDLE_HISTORY_SCHEMA = schema.get_table('handle_history')
        return _HANDLE_HISTORY_SCHEMA
    
    elif name == 'HANDLE_INDEX_SCHEMA':
        if _HANDLE_INDEX_SCHEMA is None:
            _HANDLE_INDEX_SCHEMA = schema.get_index('idx_handle_current_hash')
        return _HANDLE_INDEX_SCHEMA
    
    elif name == 'TABLE_LAYERS':
        return MCardSchema.TABLE_LAYERS
    
    raise AttributeError(f"module 'mcard.schema' has no attribute '{name}'")


__all__ = [
    # Singleton class
    'MCardSchema',
    'get_instance',
    # Primary API
    'get_schema',
    'get_all_statements',
    'get_schemas_by_layer',
    'get_tables_by_layer',
    # Initialization
    'init_all_tables',
    'init_core_tables',
    'init_handle_tables',
    'init_vector_tables',
    'init_semantic_tables',
    'init_graph_tables',
    'init_vec0_table',
    # Version management
    'get_schema_version',
    'set_schema_version',
    # Backward compatibility (loaded from SQL file only)
    'CARD_TABLE_SCHEMA',
    'HANDLE_REGISTRY_SCHEMA',
    'HANDLE_HISTORY_SCHEMA',
    'HANDLE_INDEX_SCHEMA',
    'TABLE_LAYERS',
]
