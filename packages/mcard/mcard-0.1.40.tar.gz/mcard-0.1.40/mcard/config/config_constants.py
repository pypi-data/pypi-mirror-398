"""General configuration constants for the MCard application."""

# Environment Variable Names for Hashing
ENV_HASH_ALGORITHM = "MCARD_HASH_ALGORITHM"
ENV_HASH_CUSTOM_MODULE = "MCARD_HASH_CUSTOM_MODULE"
ENV_HASH_CUSTOM_FUNCTION = "MCARD_HASH_CUSTOM_FUNCTION"
ENV_HASH_CUSTOM_LENGTH = "MCARD_HASH_CUSTOM_LENGTH"

# ─────────────────────────────────────────────────────────────────────────────
# Database Schema
# ─────────────────────────────────────────────────────────────────────────────
# DEPRECATED: Use mcard.schema.MCardSchema instead.
# All schemas are loaded from: schema/mcard_schema.sql (the ONLY source)
#
# For schema access, use:
#   from mcard.schema import MCardSchema
#   schema = MCardSchema.get_instance()
#   schema.get_table('card')
# ─────────────────────────────────────────────────────────────────────────────

# Lazy-loaded for backward compatibility
_MCARD_TABLE_SCHEMA = None

def __getattr__(name):
    """
    Lazy attribute access for backward compatibility.
    
    MCARD_TABLE_SCHEMA is loaded exclusively from the singleton.
    There are NO hardcoded SQL fallbacks.
    """
    global _MCARD_TABLE_SCHEMA
    if name == 'MCARD_TABLE_SCHEMA':
        if _MCARD_TABLE_SCHEMA is None:
            from mcard.schema import MCardSchema
            schema = MCardSchema.get_instance()
            _MCARD_TABLE_SCHEMA = {
                'documents': schema.get_table('mcard_fts'),
                'card': schema.get_table('card')
            }
        return _MCARD_TABLE_SCHEMA
    raise AttributeError(f"module 'mcard.config.config_constants' has no attribute '{name}'")

# Triggers for Synchronizing FTS Table with Card Table
# Note: Consider using mcard_fts instead for new deployments
TRIGGERS = [
    "CREATE TRIGGER IF NOT EXISTS card_insert AFTER INSERT ON card BEGIN INSERT INTO documents(content) VALUES (new.content); END;",
    "CREATE TRIGGER IF NOT EXISTS card_update AFTER UPDATE ON card BEGIN UPDATE documents SET content = new.content WHERE rowid = (SELECT rowid FROM documents WHERE content = old.content LIMIT 1); END;",
    "CREATE TRIGGER IF NOT EXISTS card_delete AFTER DELETE ON card BEGIN DELETE FROM documents WHERE content = old.content; END;"
]


# Database Paths
DEFAULT_DB_PATH = './data/DEFAULT_DB_FILE.db'
TEST_DB_PATH = './tests/data/test_mcard.db'

# Environment Variable Names
ENV_DB_PATH = "MCARD_DB_PATH"
ENV_DB_MAX_CONNECTIONS = "MCARD_STORE_MAX_CONNECTIONS"
ENV_DB_TIMEOUT = "MCARD_STORE_TIMEOUT"
ENV_SERVICE_LOG_LEVEL = "MCARD_SERVICE_LOG_LEVEL"
ENV_API_PORT = "MCARD_API_PORT"
ENV_FORCE_DEFAULT_CONFIG = "MCARD_FORCE_DEFAULT_CONFIG"
ENV_API_KEY = "MCARD_API_KEY"

# Default Configuration Values
DEFAULT_POOL_SIZE = 10
DEFAULT_TIMEOUT = 30.0
DEFAULT_API_PORT = 5320
DEFAULT_API_KEY = 'your_api_key_here'

# Server Configuration
SERVER_HOST = "0.0.0.0"
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 1000
MIN_PAGE_SIZE = 1

# HTTP Status Codes
HTTP_STATUS_OK = 200
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

# Error Messages
ERROR_INVALID_API_KEY = "Invalid API key"
ERROR_CARD_NOT_FOUND = "Card not found"
ERROR_CARD_CREATION_FAILED = "Failed to create card"
ERROR_CARD_DELETION_FAILED = "Failed to delete card"

# Event Constants
TYPE = "type"
HASH = "hash"
FIRST_G_TIME = "first_g_time"
CONTENT_SIZE = "content_size"
COLLISION_TIME = "collision_time"
UPGRADED_FUNCTION = "upgraded_function"
UPGRADED_HASH = "upgraded_hash"
DUPLICATE_TIME = "duplicate_time"
DUPLICATE_EVENT_TYPE = "duplicate"
COLLISION_EVENT_TYPE = "collision"

# A Pair of colliding MD5 content values
MD5_COLLISION_PAIR_IN_BYTES_a = bytes.fromhex("4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518afbfa200a8284bf36e8e4b55b35f427593d849676da0d1555d8360fb5f07fea2")
MD5_COLLISION_PAIR_IN_BYTES_b = bytes.fromhex("4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518afbfa202a8284bf36e8e4b55b35f427593d849676da0d1d55d8360fb5f07fea2")

# Hash Algorithm Hierarchy
ALGORITHM_HIERARCHY = {
    'sha1': {'strength': 1, 'next': 'sha224'},
    'sha224': {'strength': 2, 'next': 'sha256'},
    'sha256': {'strength': 3, 'next': 'sha384'},
    'sha384': {'strength': 4, 'next': 'sha512'},
    'sha512': {'strength': 5, 'next': 'custom'},
    'custom': {'strength': 6, 'next': None}
}

# Logging Configuration
LOG_DIRECTORY = 'logs'
LOG_FILENAME = 'mcard.log'
DEFAULT_LOG_PATH = f'{LOG_DIRECTORY}/{LOG_FILENAME}'

# CORS origins
CORS_ORIGINS = [
    "http://localhost:3000",  # Default React dev server
    "http://localhost:8000",  # Default FastAPI dev server
    "https://localhost:3000",
    "https://localhost:8000",
    "http://localhost:8080",  # Additional CORS origin
    "https://example.com"  # Additional CORS origin
]

# API Key Header Name
API_KEY_HEADER_NAME = "X-API-Key"

# Search Parameters
SEARCH_CONTENT_DEFAULT = True
SEARCH_HASH_DEFAULT = True
SEARCH_TIME_DEFAULT = True

# Additional Error Messages
ERROR_SERVER_SHUTDOWN = "Server shutdown failed"
ERROR_INVALID_CONTENT = "Content cannot be empty"
ERROR_INVALID_METADATA = "Metadata must be a dictionary"
ERROR_LISTING_CARDS = "Error listing cards"
ERROR_DELETE_ALL_CARDS_FAILED = "Failed to delete all cards"
SUCCESS_DELETE_ALL_CARDS = "All cards deleted successfully"
HEALTH_CHECK_SUCCESS = "Server is healthy"
HEALTH_CHECK_FAILURE = "Server health check failed"
ERROR_INVALID_CREDENTIALS = "Invalid credentials"
ERROR_CARD_ALREADY_EXISTS = "Card already exists"
ERROR_CARD_NOT_AUTHORIZED = "Card not authorized"
ERROR_INVALID_REQUEST = "Invalid request"
ERROR_INVALID_CARD_ID = "Invalid card ID"
ERROR_CARD_UPDATE_FAILED = "Failed to update card"
ERROR_CARD_NOT_UPDATED = "Card not updated"
