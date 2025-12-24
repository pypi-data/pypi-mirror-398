"""
MCard Configuration Package
============================

This package provides configuration management for MCard including:
- Unified settings (organized by category in `settings.py`)
- Logging configuration (unified in `logging.py`)
- Environment parameters (legacy, in `env_parameters.py`)
- Configuration constants (legacy, in `config_constants.py`)

Recommended Usage (New):
    from mcard.config import settings
    
    # Access settings by category
    db_path = settings.database.path
    api_port = settings.api.port
    hash_algo = settings.hashing.algorithm
    ptr_timeout = settings.ptr.default_timeout

Legacy Usage (Still Supported):
    from mcard.config import setup_logging, get_logger
    from mcard.config import EnvParameters
"""

# ─────────────────────────────────────────────────────────────────────────────
# Unified Settings (Recommended)
# ─────────────────────────────────────────────────────────────────────────────

from .settings import (
    settings,
    Settings,
    DatabaseSettings,
    APISettings,
    PaginationSettings,
    HashingSettings,
    LoggingSettings,
    FileProcessingSettings,
    PTRSettings,
    HTTPStatus,
)

# ─────────────────────────────────────────────────────────────────────────────
# Logging (Unified Module)
# ─────────────────────────────────────────────────────────────────────────────

from .logging import (
    setup_logging,
    setup_improved_logging,  # Backward compatibility alias
    get_logger,
    get_performance_logger,
    get_security_logger,
    get_database_logger,
    get_api_logger,
    get_logging_config,
    PerformanceTimer,
    SecurityAuditLogger,
)

# ─────────────────────────────────────────────────────────────────────────────
# Legacy Exports (Backward Compatibility)
# ─────────────────────────────────────────────────────────────────────────────

from .env_parameters import EnvParameters
from .config_constants import (
    # Database
    DEFAULT_DB_PATH,
    TEST_DB_PATH,
    MCARD_TABLE_SCHEMA,
    TRIGGERS,
    # API
    DEFAULT_API_PORT,
    DEFAULT_API_KEY,
    SERVER_HOST,
    CORS_ORIGINS,
    API_KEY_HEADER_NAME,
    # Pagination
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
    # Pool/Timeout
    DEFAULT_POOL_SIZE,
    DEFAULT_TIMEOUT,
    # Logging
    LOG_DIRECTORY,
    LOG_FILENAME,
    DEFAULT_LOG_PATH,
    # Environment Variable Names
    ENV_DB_PATH,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_SERVICE_LOG_LEVEL,
    ENV_API_PORT,
    ENV_API_KEY,
    ENV_HASH_ALGORITHM,
    ENV_HASH_CUSTOM_MODULE,
    ENV_HASH_CUSTOM_FUNCTION,
    ENV_HASH_CUSTOM_LENGTH,
)

__all__ = [
    # ─────────────────────────────────────────────────────────────────────────
    # Unified Settings (Recommended)
    # ─────────────────────────────────────────────────────────────────────────
    "settings",
    "Settings",
    "DatabaseSettings",
    "APISettings",
    "PaginationSettings",
    "HashingSettings",
    "LoggingSettings",
    "FileProcessingSettings",
    "PTRSettings",
    "HTTPStatus",
    
    # ─────────────────────────────────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────────────────────────────────
    "setup_logging",
    "setup_improved_logging",
    "get_logger",
    "get_performance_logger",
    "get_security_logger",
    "get_database_logger",
    "get_api_logger",
    "get_logging_config",
    "PerformanceTimer",
    "SecurityAuditLogger",
    
    # ─────────────────────────────────────────────────────────────────────────
    # Legacy (Backward Compatibility)
    # ─────────────────────────────────────────────────────────────────────────
    "EnvParameters",
    # Database
    "DEFAULT_DB_PATH",
    "TEST_DB_PATH",
    "MCARD_TABLE_SCHEMA",
    "TRIGGERS",
    # API
    "DEFAULT_API_PORT",
    "DEFAULT_API_KEY",
    "SERVER_HOST",
    "CORS_ORIGINS",
    "API_KEY_HEADER_NAME",
    # Pagination
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MIN_PAGE_SIZE",
    # Pool/Timeout
    "DEFAULT_POOL_SIZE",
    "DEFAULT_TIMEOUT",
    # Logging
    "LOG_DIRECTORY",
    "LOG_FILENAME",
    "DEFAULT_LOG_PATH",
    # Environment Variable Names
    "ENV_DB_PATH",
    "ENV_DB_MAX_CONNECTIONS",
    "ENV_DB_TIMEOUT",
    "ENV_SERVICE_LOG_LEVEL",
    "ENV_API_PORT",
    "ENV_API_KEY",
    "ENV_HASH_ALGORITHM",
    "ENV_HASH_CUSTOM_MODULE",
    "ENV_HASH_CUSTOM_FUNCTION",
    "ENV_HASH_CUSTOM_LENGTH",
]
