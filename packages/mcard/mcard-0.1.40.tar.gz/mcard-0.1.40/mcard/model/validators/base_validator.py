"""
Base validator interface for content validation.
"""
from abc import ABC, abstractmethod
from typing import Union

class ValidationError(Exception):
    """Exception raised for validation errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class BaseValidator(ABC):
    """Abstract base class for content validators."""

    @abstractmethod
    def validate(self, content: Union[str, bytes], mime_type: str) -> None:
        """
        Validate content for a specific MIME type.
        
        Args:
            content: The content to validate
            mime_type: The detected MIME type
            
        Raises:
            ValidationError: If content is invalid
        """
        pass

    @abstractmethod
    def can_validate(self, mime_type: str) -> bool:
        """
        Check if this validator can handle the given MIME type.
        
        Args:
            mime_type: The MIME type to check
            
        Returns:
            True if this validator can handle the MIME type
        """
        pass
