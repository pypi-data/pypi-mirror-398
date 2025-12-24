"""
DEPRECATED: This module is deprecated in favor of `mcard.config.logging`.

This file exists for backward compatibility only. All new code should import from:
    from mcard.config.logging import setup_logging, get_logger

This module will be removed in a future release.
"""

import warnings

# Issue deprecation warning on import
warnings.warn(
    "mcard.config.logging_config is deprecated. "
    "Use mcard.config.logging instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from the new unified module for backward compatibility
from .logging import (
    setup_logging,
    get_logger,
    get_logging_config as LOGGING_CONFIG,  # For code that accessed the dict directly
)

__all__ = [
    "setup_logging",
    "get_logger",
    "LOGGING_CONFIG",
]
