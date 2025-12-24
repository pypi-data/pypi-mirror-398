"""
DEPRECATED: This module is deprecated in favor of `mcard.config.logging`.

This file exists for backward compatibility only. All new code should import from:
    from mcard.config.logging import setup_logging, get_logger, PerformanceTimer, SecurityAuditLogger

This module will be removed in a future release.
"""

import warnings

# Issue deprecation warning on import
warnings.warn(
    "mcard.config.improved_logging is deprecated. "
    "Use mcard.config.logging instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the new unified module for backward compatibility
from .logging import (
    setup_logging as setup_improved_logging,  # Original name
    setup_logging,
    get_logging_config as get_improved_logging_config,  # Original name  
    get_logger,
    get_performance_logger,
    get_security_logger,
    get_database_logger,
    PerformanceTimer,
    SecurityAuditLogger,
)

__all__ = [
    "setup_improved_logging",
    "get_improved_logging_config",
    "get_logger",
    "get_performance_logger",
    "get_security_logger",
    "get_database_logger",
    "PerformanceTimer",
    "SecurityAuditLogger",
]
