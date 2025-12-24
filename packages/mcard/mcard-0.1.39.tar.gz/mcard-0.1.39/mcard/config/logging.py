"""
MCard Unified Logging Configuration
====================================

This module provides the canonical logging configuration for MCard.
It consolidates previous separate logging modules into a single, maintainable source.

Features:
- Structured logging with multiple formatters (simple, detailed, JSON, performance)
- Rotating file handlers for general, error, and performance logs
- Specialized loggers for API, database, performance, and security
- Context managers for performance timing and security auditing
- Backward compatible with previous logging APIs

Usage:
    from mcard.config.logging import setup_logging, get_logger

    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application started")

    # Performance timing
    from mcard.config.logging import PerformanceTimer
    with PerformanceTimer("database_query"):
        result = db.query(...)

    # Security auditing
    from mcard.config.logging import SecurityAuditLogger
    audit = SecurityAuditLogger()
    audit.log_access_attempt(user_id="123", resource="/api/cards", success=True)
"""

import logging
import logging.config
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config_constants import LOG_DIRECTORY, LOG_FILENAME
from .env_parameters import EnvParameters

# ─────────────────────────────────────────────────────────────────────────────
# Module State
# ─────────────────────────────────────────────────────────────────────────────

_logging_initialized = False
_project_root: Optional[Path] = None
_logs_dir: Optional[Path] = None


def _get_project_root() -> Path:
    """Get the project root directory."""
    global _project_root
    if _project_root is None:
        _project_root = Path(__file__).parent.parent.parent.resolve()
    return _project_root


def _get_logs_dir() -> Path:
    """Get the logs directory, creating it if necessary."""
    global _logs_dir
    if _logs_dir is None:
        _logs_dir = _get_project_root() / LOG_DIRECTORY
        _logs_dir.mkdir(parents=True, exist_ok=True)
    return _logs_dir


# ─────────────────────────────────────────────────────────────────────────────
# Configuration Factory
# ─────────────────────────────────────────────────────────────────────────────

def get_logging_config() -> dict[str, Any]:
    """
    Generate the logging configuration dictionary.
    
    Returns:
        dict: A logging.config.dictConfig compatible configuration.
    """
    env_params = EnvParameters()
    log_level = env_params.get_log_level()
    logs_dir = _get_logs_dir()

    log_file = str(logs_dir / LOG_FILENAME)
    error_log_file = str(logs_dir / "mcard.error.log")
    performance_log_file = str(logs_dir / "mcard.performance.log")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # Simple format for console output
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            # Detailed format for file output
            "detailed": {
                "format": "%(asctime)s | %(name)-25s | %(levelname)-8s | %(funcName)-20s:%(lineno)-4d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            # JSON format for structured logging
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            # Performance format
            "performance": {
                "format": "%(asctime)s | PERF | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            # Console handler - outputs to stderr
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple",
                "stream": "ext://sys.stderr",
            },
            # Main file handler - rotating, detailed format
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": log_file,
                "maxBytes": 50_000_000,  # 50MB
                "backupCount": 10,
                "encoding": "utf-8",
            },
            # Error file handler - only ERROR and above
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": error_log_file,
                "maxBytes": 10_000_000,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            # Performance file handler
            "performance_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "performance",
                "filename": performance_log_file,
                "maxBytes": 10_000_000,  # 10MB
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            # Main MCard logger
            "mcard": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # API logger
            "mcard.api": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            # Performance metrics logger
            "mcard.performance": {
                "level": "INFO",
                "handlers": ["performance_file"],
                "propagate": False,
            },
            # Security events logger
            "mcard.security": {
                "level": "WARNING",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # Database operations logger
            "mcard.database": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console", "file"],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Setup Functions
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(force_reinit: bool = False) -> None:
    """
    Set up the MCard logging configuration.
    
    This function is idempotent - it will only initialize logging once unless
    force_reinit is True.
    
    Args:
        force_reinit: If True, reinitialize logging even if already set up.
    """
    global _logging_initialized

    if _logging_initialized and not force_reinit:
        return

    try:
        config = get_logging_config()
        logging.config.dictConfig(config)

        logger = logging.getLogger("mcard.logging")
        logger.info(
            "Logging configuration initialized",
            extra={"log_level": config["loggers"]["mcard"]["level"]},
        )

        _logging_initialized = True

    except Exception as e:
        # Fallback to basic logging if setup fails
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logger = logging.getLogger("mcard.logging")
        logger.error(f"Failed to setup logging, using basic configuration: {e}")


# Backward compatibility alias
setup_improved_logging = setup_logging


# ─────────────────────────────────────────────────────────────────────────────
# Logger Factory Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The logger name (typically __name__).
        
    Returns:
        logging.Logger: The configured logger.
    """
    return logging.getLogger(name)


def get_performance_logger() -> logging.Logger:
    """Get a specialized logger for performance metrics."""
    return logging.getLogger("mcard.performance")


def get_security_logger() -> logging.Logger:
    """Get a specialized logger for security events."""
    return logging.getLogger("mcard.security")


def get_database_logger() -> logging.Logger:
    """Get a specialized logger for database operations."""
    return logging.getLogger("mcard.database")


def get_api_logger() -> logging.Logger:
    """Get a specialized logger for API operations."""
    return logging.getLogger("mcard.api")


# ─────────────────────────────────────────────────────────────────────────────
# Context Managers
# ─────────────────────────────────────────────────────────────────────────────

class PerformanceTimer:
    """
    Context manager for timing operations and logging performance metrics.
    
    Usage:
        with PerformanceTimer("database_query"):
            result = db.query(...)
    """

    def __init__(self, operation: str, logger: Optional[logging.Logger] = None):
        self.operation = operation
        self.logger = logger or get_performance_logger()
        self.start_time: Optional[datetime] = None

    def __enter__(self) -> "PerformanceTimer":
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() * 1000
            if exc_type:
                self.logger.error(
                    f"Operation '{self.operation}' failed after {duration:.2f}ms: {exc_val}"
                )
            else:
                self.logger.info(
                    f"Operation '{self.operation}' completed in {duration:.2f}ms"
                )


# ─────────────────────────────────────────────────────────────────────────────
# Security Audit Helpers
# ─────────────────────────────────────────────────────────────────────────────

class SecurityAuditLogger:
    """
    Helper class for logging security-related events.
    
    Usage:
        audit = SecurityAuditLogger()
        audit.log_access_attempt("user123", "/api/cards", success=True)
    """

    def __init__(self):
        self.logger = get_security_logger()

    def log_access_attempt(self, user_id: str, resource: str, success: bool) -> None:
        """Log access attempts."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(f"Access {status}: user={user_id}, resource={resource}")

    def log_authentication(self, user_id: str, method: str, success: bool) -> None:
        """Log authentication events."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(f"Auth {status}: user={user_id}, method={method}")

    def log_suspicious_activity(self, activity: str, details: str) -> None:
        """Log suspicious activities."""
        self.logger.error(f"SUSPICIOUS: {activity} - {details}")


# ─────────────────────────────────────────────────────────────────────────────
# Module Exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    # Setup functions
    "setup_logging",
    "setup_improved_logging",  # Backward compatibility alias
    "get_logging_config",
    # Logger factories
    "get_logger",
    "get_performance_logger",
    "get_security_logger",
    "get_database_logger",
    "get_api_logger",
    # Context managers and helpers
    "PerformanceTimer",
    "SecurityAuditLogger",
]
