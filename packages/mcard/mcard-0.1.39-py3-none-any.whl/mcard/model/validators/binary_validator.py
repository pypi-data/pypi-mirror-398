"""
Binary content validator.
"""
from typing import Union

from .base_validator import BaseValidator, ValidationError
from ..detectors.binary_detector import BinarySignatureDetector

class BinaryValidator(BaseValidator):
    """Validator for binary content types."""

    BINARY_MIME_TYPES = {
        'image/png', 'image/jpeg', 'image/gif', 'image/bmp',
        'application/pdf', 'application/zip', 'video/mp4',
        'audio/wav', 'application/octet-stream'
    }

    def can_validate(self, mime_type: str) -> bool:
        return (mime_type in self.BINARY_MIME_TYPES or 
                mime_type.startswith(('image/', 'audio/', 'video/')))

    def validate(self, content: Union[str, bytes], mime_type: str) -> None:
        """Validate binary content based on MIME type."""
        if isinstance(content, str):
            content = content.encode('utf-8')

        if mime_type.startswith('image/'):
            self._validate_image(content, mime_type)
        elif mime_type == 'application/pdf':
            self._validate_pdf(content)
        elif mime_type == 'application/zip':
            self._validate_zip(content)

    def _validate_image(self, content: bytes, mime_type: str) -> None:
        """Validate image content."""
        if mime_type == 'image/png' and len(content) <= 8:
            raise ValidationError("Invalid PNG content: truncated file")
        elif mime_type == 'image/jpeg' and len(content) <= 3:
            raise ValidationError("Invalid JPEG content: truncated file")
        elif mime_type == 'image/gif' and len(content) <= 6:
            raise ValidationError("Invalid GIF content: truncated file")

        # Check for proper signature
        signatures = {mime: sig for sig, mime in BinarySignatureDetector.SIGNATURES.items()}
        if mime_type in signatures and not content.startswith(signatures[mime_type]):
            raise ValidationError(f"Invalid {mime_type} content: missing proper header")

    def _validate_pdf(self, content: bytes) -> None:
        """Validate PDF content."""
        if not content.startswith(b'%PDF-'):
            raise ValidationError("Invalid PDF content")

    def _validate_zip(self, content: bytes) -> None:
        """Validate ZIP content."""
        if len(content) <= 4:
            raise ValidationError("Invalid ZIP content")
