"""Content Handle system for MCard.

A ContentHandle provides a mutable pointer to immutable MCard content,
enabling human-friendly naming and versioning while preserving data immutability.

## UTF-8 Support
Handles support Unicode characters for internationalization:
- Must start with a Unicode letter (any language)
- Can contain letters, digits, underscores, and hyphens
- Maximum 63 characters
- Normalized to NFC (Canonical Decomposition, then Canonical Composition)

Examples: "my_doc", "文檔", "مستند", "ドキュメント", "документ"
"""
import re
import logging
import unicodedata
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mcard.ptr.core.clm_template import Maybe

logger = logging.getLogger(__name__)

# Maximum handle length
MAX_HANDLE_LENGTH = 255


def _is_valid_start_char(char: str) -> bool:
    """Check if character is valid as the first character of a handle.
    
    Must be a Unicode letter (category 'L').
    """
    return unicodedata.category(char).startswith('L')


def _is_valid_body_char(char: str) -> bool:
    """Check if character is valid in the body of a handle.
    
    Can be: letter, number, underscore, hyphen.
    """
    cat = unicodedata.category(char)
    return (
        cat.startswith('L') or  # Letters (any language)
        cat.startswith('N') or  # Numbers (any language)
        char == '_' or          # Underscore
        char == '-' or          # Hyphen
        char == '.' or          # Dot
        char == '/' or          # Forward slash
        char == ' ' or          # Space
        char == ':'             # Colon (for URIs)
    )


class HandleValidationError(ValueError):
    """Raised when a handle string is invalid."""
    pass


def validate_handle(handle: str) -> str:
    """Validate and normalize a handle string.
    
    Args:
        handle: The handle string to validate.
        
    Returns:
        The validated and normalized handle (NFC normalized, case-folded).
        
    Raises:
        HandleValidationError: If the handle is invalid.
    """
    if not handle:
        raise HandleValidationError("Handle cannot be empty.")
    
    # Normalize: strip whitespace, apply Unicode NFC normalization, case-fold
    normalized = unicodedata.normalize('NFC', handle.strip()).casefold()
    
    if len(normalized) > MAX_HANDLE_LENGTH:
        raise HandleValidationError(
            f"Handle '{handle}' is too long ({len(normalized)} chars). "
            f"Maximum length is {MAX_HANDLE_LENGTH} characters."
        )
    
    if len(normalized) == 0:
        raise HandleValidationError("Handle cannot be empty after normalization.")
    
    # Validate first character
    if not _is_valid_start_char(normalized[0]):
        raise HandleValidationError(
            f"Invalid handle '{handle}'. Must start with a letter (any language)."
        )
    
    # Validate remaining characters
    for i, char in enumerate(normalized[1:], start=1):
        if not _is_valid_body_char(char):
            raise HandleValidationError(
                f"Invalid character '{char}' at position {i} in handle '{handle}'. "
                "Allowed: letters, digits, underscores, hyphens."
            )
    
    return normalized



class ContentHandle:
    """A mutable pointer to an immutable MCard hash.
    
    Attributes:
        handle: The validated handle string.
        current_hash: The hash of the MCard this handle points to.
        created_at: When this handle was first created.
        updated_at: When this handle was last updated to point to a new hash.
    """
    
    def __init__(self, handle: str, current_hash: str, 
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """Initialize a ContentHandle.
        
        Args:
            handle: The user-defined handle string (will be validated).
            current_hash: The MCard hash this handle points to.
            created_at: Creation timestamp (defaults to now).
            updated_at: Last update timestamp (defaults to created_at).
        """
        self.handle = validate_handle(handle)
        self.current_hash = current_hash
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or self.created_at
    
    def update(self, new_hash: str) -> str:
        """Update the handle to point to a new hash.
        
        Args:
            new_hash: The new MCard hash to point to.
            
        Returns:
            The previous hash (for history tracking).
        """
        previous_hash = self.current_hash
        self.current_hash = new_hash
        self.updated_at = datetime.now(timezone.utc)
        logger.info(f"Handle '{self.handle}' updated: {previous_hash[:8]}... -> {new_hash[:8]}...")
        return previous_hash
    
    def __repr__(self) -> str:
        return f"ContentHandle(handle='{self.handle}', current_hash='{self.current_hash[:8]}...')"
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'handle': self.handle,
            'current_hash': self.current_hash,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
