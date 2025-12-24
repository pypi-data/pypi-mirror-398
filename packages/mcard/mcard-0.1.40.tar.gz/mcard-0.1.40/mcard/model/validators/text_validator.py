"""
Text content validator.
"""
import json
import xml.etree.ElementTree as ET
from typing import Union

from .base_validator import BaseValidator, ValidationError

class TextValidator(BaseValidator):
    """Validator for text-based content types."""

    TEXT_MIME_TYPES = {
        'text/plain', 'application/json', 'application/xml', 
        'text/xml', 'image/svg+xml', 'text/html', 'text/markdown'
    }

    def can_validate(self, mime_type: str) -> bool:
        return mime_type in self.TEXT_MIME_TYPES

    def validate(self, content: Union[str, bytes], mime_type: str) -> None:
        """Validate text content based on MIME type."""
        if isinstance(content, bytes):
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                raise ValidationError("Invalid content: not valid UTF-8")
        else:
            text_content = content

        if mime_type == 'text/plain':
            self._validate_plain_text(text_content)
        elif mime_type == 'application/json':
            self._validate_json(text_content)
        elif mime_type in ('application/xml', 'text/xml', 'image/svg+xml'):
            self._validate_xml(text_content)

    def _validate_plain_text(self, content: str) -> None:
        """Validate plain text content."""
        if not content.strip():
            raise ValidationError("Invalid content: empty text")
        if len(content.strip()) < 3:
            raise ValidationError("Invalid content: too short")
        if all(ord(c) < 32 for c in content.strip()):
            raise ValidationError("Invalid content: contains only control characters")
        # Heuristic: valid plain text should contain some whitespace
        if not any(c.isspace() for c in content):
            # Check for multi-word content without spaces
            if len(content.split()) == 1 and len(content) > 20: # Arbitrary length check
                 raise ValidationError("Invalid content: likely not plain text")

    def _validate_json(self, content: str) -> None:
        """Validate JSON content."""
        try:
            # Check for comments before attempting to parse
            lines = content.split('\n')
            if any(line.strip().startswith('//') for line in lines):
                raise ValidationError("Invalid JSON content: contains comments")
            json.loads(content)
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON content")

    def _validate_xml(self, content: str) -> None:
        """Validate XML content."""
        try:
            ET.fromstring(content)
        except ET.ParseError:
            raise ValidationError("Invalid XML content")
