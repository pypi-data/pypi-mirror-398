"""
MCard Unified Settings
======================

This module provides a single, unified interface for all MCard configuration.
It organizes settings into logical categories for better discoverability.

Usage:
    from mcard.config.settings import settings
    
    # Access database settings
    db_path = settings.database.path
    
    # Access API settings
    port = settings.api.port
    
    # Access hash settings
    algorithm = settings.hashing.algorithm
    
    # Access PTR runtime settings
    timeout = settings.ptr.default_timeout
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

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
    # Hashing
    ALGORITHM_HIERARCHY,
    # Logging
    LOG_DIRECTORY,
    LOG_FILENAME,
    DEFAULT_LOG_PATH,
    # HTTP Status
    HTTP_STATUS_OK,
    HTTP_STATUS_FORBIDDEN,
    HTTP_STATUS_NOT_FOUND,
    HTTP_STATUS_INTERNAL_SERVER_ERROR,
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


# ─────────────────────────────────────────────────────────────────────────────
# Settings Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DatabaseSettings:
    """Database-related settings."""
    path: str = DEFAULT_DB_PATH
    test_path: str = TEST_DB_PATH
    pool_size: int = DEFAULT_POOL_SIZE
    timeout: float = DEFAULT_TIMEOUT
    max_connections: int = DEFAULT_POOL_SIZE
    schema: Dict = field(default_factory=lambda: MCARD_TABLE_SCHEMA)
    triggers: List[str] = field(default_factory=lambda: TRIGGERS)


@dataclass
class APISettings:
    """API server settings."""
    port: int = DEFAULT_API_PORT
    host: str = SERVER_HOST
    api_key: str = DEFAULT_API_KEY
    api_key_header: str = API_KEY_HEADER_NAME
    cors_origins: List[str] = field(default_factory=lambda: CORS_ORIGINS.copy())
    

@dataclass
class PaginationSettings:
    """Pagination settings."""
    default_page_size: int = DEFAULT_PAGE_SIZE
    max_page_size: int = MAX_PAGE_SIZE
    min_page_size: int = MIN_PAGE_SIZE


@dataclass
class HashingSettings:
    """Hashing algorithm settings."""
    algorithm: str = "sha256"
    custom_module: str = "custom_module"
    custom_function: str = "custom_function"
    custom_length: int = 64
    hierarchy: Dict = field(default_factory=lambda: ALGORITHM_HIERARCHY.copy())


@dataclass
class LoggingSettings:
    """Logging settings."""
    directory: str = LOG_DIRECTORY
    filename: str = LOG_FILENAME
    default_path: str = DEFAULT_LOG_PATH
    level: str = "DEBUG"


@dataclass 
class FileProcessingSettings:
    """File processing settings."""
    wrap_width_default: int = 1000
    wrap_width_known: int = 1200
    max_problem_text_bytes: int = 2 * 1024 * 1024  # 2MB
    read_timeout_secs: float = 30.0


@dataclass
class PTRSettings:
    """Polynomial Type Runtime settings."""
    # Subprocess timeouts
    default_timeout: int = 5
    lean_timeout: int = 60
    julia_timeout: int = 15
    r_timeout: int = 10
    
    # Allowed imports for sandboxed Python
    allowed_imports: Dict[str, str] = field(default_factory=lambda: {
        'math': 'math',
        'json': 'json',
        'yaml': 'yaml',
        'pathlib': 'pathlib',
        'typing': 'typing',
        'hashlib': 'hashlib',
        'mcard': 'mcard',
        'mcard.ptr.core.runtime': 'mcard.ptr.core.runtime',
        'mcard.ptr.core.llm': 'mcard.ptr.core.llm',
        'mcard.file_io': 'mcard.file_io',
        'mcard.model.card': 'mcard.model.card',
        'mcard.model.card_collection': 'mcard.model.card_collection',
        'mcard.model.handle': 'mcard.model.handle',
        'mcard.rag.vector.store': 'mcard.rag.vector.store',
        'os': 'os',
        'time': 'time',
        'random': 'random',
        'logging': 'logging',
    })
    
    # Safe builtins for sandbox
    safe_builtins: Set[str] = field(default_factory=lambda: {
        'int', 'float', 'str', 'len', 'range', 'list', 'dict', 'tuple', 'set',
        'abs', 'round', 'max', 'min', 'sum', 'sorted', 'enumerate', 'zip',
        'ValueError', 'Exception', '__build_class__', 'super', 'open',
        'all', 'any', 'bool', 'isinstance', 'bytes', 'print', 'globals',
    })
    
    # Runtime command configurations
    runtime_config: Dict = field(default_factory=lambda: {
        'python': {'command': 'python3', 'version_flag': '--version'},
        'javascript': {'command': ['npx', 'tsx'], 'version_flag': '--version', 'eval_flag': '-e'},
        'deno': {'command': 'deno', 'version_flag': '--version', 'eval_flag': '-e'},
        'rust': {'command': 'rustc', 'version_flag': '--version'},
        'c': {'command': None},
        'lean': {'command': 'lean', 'version_flag': '--version', 'run_flag': '--run'},
        'r': {'command': 'Rscript', 'version_flag': '--version'},
        'julia': {'command': 'julia', 'version_flag': '--version'},
        'wasm': {'command': None},
    })


@dataclass
class HTTPStatus:
    """HTTP status code constants."""
    OK: int = HTTP_STATUS_OK
    FORBIDDEN: int = HTTP_STATUS_FORBIDDEN
    NOT_FOUND: int = HTTP_STATUS_NOT_FOUND
    INTERNAL_SERVER_ERROR: int = HTTP_STATUS_INTERNAL_SERVER_ERROR


# ─────────────────────────────────────────────────────────────────────────────
# Main Settings Class
# ─────────────────────────────────────────────────────────────────────────────

class Settings:
    """
    Unified settings container for MCard.
    
    Provides organized access to all configuration through category-specific
    properties.
    
    This is a singleton - use `settings` instance instead of creating new ones.
    """
    
    _instance: Optional['Settings'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'Settings':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if Settings._initialized:
            return
            
        # Load environment variables
        load_dotenv()
        
        # Initialize category settings
        self._database = self._init_database_settings()
        self._api = self._init_api_settings()
        self._pagination = PaginationSettings()
        self._hashing = self._init_hashing_settings()
        self._logging = self._init_logging_settings()
        self._file_processing = self._init_file_processing_settings()
        self._ptr = PTRSettings()
        self._http_status = HTTPStatus()
        
        Settings._initialized = True
    
    def _init_database_settings(self) -> DatabaseSettings:
        """Initialize database settings from environment."""
        return DatabaseSettings(
            path=os.getenv(ENV_DB_PATH, DEFAULT_DB_PATH),
            test_path=os.getenv('TEST_DB_PATH', TEST_DB_PATH),
            pool_size=int(os.getenv('DEFAULT_POOL_SIZE', DEFAULT_POOL_SIZE)),
            timeout=float(os.getenv(ENV_DB_TIMEOUT, DEFAULT_TIMEOUT)),
            max_connections=int(os.getenv(ENV_DB_MAX_CONNECTIONS, DEFAULT_POOL_SIZE)),
        )
    
    def _init_api_settings(self) -> APISettings:
        """Initialize API settings from environment."""
        return APISettings(
            port=int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT)),
            api_key=os.getenv(ENV_API_KEY, DEFAULT_API_KEY),
        )
    
    def _init_hashing_settings(self) -> HashingSettings:
        """Initialize hashing settings from environment."""
        return HashingSettings(
            algorithm=os.getenv(ENV_HASH_ALGORITHM, 'sha256'),
            custom_module=os.getenv(ENV_HASH_CUSTOM_MODULE, 'custom_module'),
            custom_function=os.getenv(ENV_HASH_CUSTOM_FUNCTION, 'custom_function'),
            custom_length=int(os.getenv(ENV_HASH_CUSTOM_LENGTH, 64)),
        )
    
    def _init_logging_settings(self) -> LoggingSettings:
        """Initialize logging settings from environment."""
        return LoggingSettings(
            level=os.getenv(ENV_SERVICE_LOG_LEVEL, 'DEBUG'),
        )
    
    def _init_file_processing_settings(self) -> FileProcessingSettings:
        """Initialize file processing settings from environment."""
        return FileProcessingSettings(
            wrap_width_default=int(os.getenv('MCARD_WRAP_WIDTH_DEFAULT', 1000)),
            wrap_width_known=int(os.getenv('MCARD_WRAP_WIDTH_KNOWN', 1200)),
            max_problem_text_bytes=int(os.getenv('MCARD_MAX_PROBLEM_TEXT_BYTES', 2 * 1024 * 1024)),
            read_timeout_secs=float(os.getenv('MCARD_READ_TIMEOUT_SECS', 30)),
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────────────────────────────────────
    
    @property
    def database(self) -> DatabaseSettings:
        """Database configuration."""
        return self._database
    
    @property
    def api(self) -> APISettings:
        """API server configuration."""
        return self._api
    
    @property
    def pagination(self) -> PaginationSettings:
        """Pagination configuration."""
        return self._pagination
    
    @property
    def hashing(self) -> HashingSettings:
        """Hashing algorithm configuration."""
        return self._hashing
    
    @property
    def logging(self) -> LoggingSettings:
        """Logging configuration."""
        return self._logging
    
    @property
    def file_processing(self) -> FileProcessingSettings:
        """File processing configuration."""
        return self._file_processing
    
    @property
    def ptr(self) -> PTRSettings:
        """Polynomial Type Runtime configuration."""
        return self._ptr
    
    @property
    def http_status(self) -> HTTPStatus:
        """HTTP status code constants."""
        return self._http_status
    
    def reload(self) -> None:
        """Reload settings from environment (for testing)."""
        Settings._initialized = False
        self.__init__()


# ─────────────────────────────────────────────────────────────────────────────
# Singleton Instance
# ─────────────────────────────────────────────────────────────────────────────

# The canonical settings instance
settings = Settings()


# ─────────────────────────────────────────────────────────────────────────────
# Module Exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    # Main settings object
    'settings',
    'Settings',
    # Category classes (for type hints)
    'DatabaseSettings',
    'APISettings',
    'PaginationSettings',
    'HashingSettings',
    'LoggingSettings',
    'FileProcessingSettings',
    'PTRSettings',
    'HTTPStatus',
]
