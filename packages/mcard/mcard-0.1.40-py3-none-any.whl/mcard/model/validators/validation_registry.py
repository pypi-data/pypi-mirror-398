"""
Central registry for content validators.
"""
from typing import List, Union

from .base_validator import BaseValidator, ValidationError
from .text_validator import TextValidator
from .binary_validator import BinaryValidator

class ValidationRegistry:
    """Central registry for managing content validators."""

    def __init__(self):
        self.validators: List[BaseValidator] = [
            TextValidator(),
            BinaryValidator(),
        ]

    def validate(self, content: Union[str, bytes], mime_type: str) -> None:
        """
        Validate content using appropriate validator.
        
        Args:
            content: The content to validate
            mime_type: The detected MIME type
            
        Raises:
            ValidationError: If content is invalid
        """
        if not content:
            raise ValidationError("Empty content")

        # Find appropriate validator
        for validator in self.validators:
            if validator.can_validate(mime_type):
                validator.validate(content, mime_type)
                return

        # If no specific validator found, do basic validation
        self._basic_validation(content)

    def _basic_validation(self, content: Union[str, bytes]) -> None:
        """Basic validation for unknown content types."""
        if isinstance(content, bytes) and not content.strip():
            raise ValidationError("Invalid content: empty byte array")

# Global registry instance
validation_registry = ValidationRegistry()
