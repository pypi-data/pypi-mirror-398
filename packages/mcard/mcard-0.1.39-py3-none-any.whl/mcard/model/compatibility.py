"""
Compatibility layer for the refactored interpreter.

This module provides backward compatibility for the original interpreter.py
while allowing gradual migration to the new modular architecture.
"""
import warnings
from typing import Union

# Import the original ValidationError for compatibility
from .validators.base_validator import ValidationError

# Re-export ValidationError at module level for backward compatibility
__all__ = ['ValidationError']

def deprecated_method(old_name: str, new_location: str):
    """Decorator to mark methods as deprecated."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{old_name} is deprecated. Use {new_location} instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

class LegacyContentTypeInterpreter:
    """
    Legacy wrapper for the original ContentTypeInterpreter interface.
    
    This class provides the same interface as the original while delegating
    to the new modular components. It includes deprecation warnings to guide
    users toward the new architecture.
    """

    def __init__(self):
        from .interpreter_refactored import ContentTypeInterpreter
        self._interpreter = ContentTypeInterpreter()

    @deprecated_method("LegacyContentTypeInterpreter", "ContentTypeInterpreter")
    def detect_content_type(self, content: Union[str, bytes], file_extension: str = None):
        """Legacy method - use ContentTypeInterpreter.detect_content_type instead."""
        return self._interpreter.detect_content_type(content, file_extension)

    @deprecated_method("LegacyContentTypeInterpreter.validate_content", "validation_registry.validate")
    def validate_content(self, content: Union[str, bytes]) -> None:
        """Legacy method - use validation_registry.validate instead."""
        return self._interpreter.validate_content(content)

    # Add other legacy methods as needed...
