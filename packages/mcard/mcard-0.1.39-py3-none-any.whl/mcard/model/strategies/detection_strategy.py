"""
Content type detection strategy interface and implementations.
"""
from abc import ABC, abstractmethod
from typing import Union, Tuple, Optional
import os

from ..detectors.registry import registry as detector_registry
from ..detectors.binary_detector import BinarySignatureDetector
from ..utils.content_analyzer import ContentAnalyzer

class DetectionStrategy(ABC):
    """Abstract base class for content type detection strategies."""

    @abstractmethod
    def detect(self, content: Union[str, bytes], file_extension: Optional[str] = None) -> Tuple[str, str]:
        """
        Detect content type and extension.
        
        Args:
            content: The content to analyze
            file_extension: Optional file extension hint
            
        Returns:
            Tuple of (mime_type, extension)
        """
        pass

class BinaryFirstStrategy(DetectionStrategy):
    """Strategy that prioritizes binary detection first."""

    def detect(self, content: Union[str, bytes], file_extension: Optional[str] = None) -> Tuple[str, str]:
        """Detect content type with binary-first approach."""
        # Convert to bytes if needed for binary detection
        if isinstance(content, bytes):
            content_bytes = content

            # Check for binary signatures first
            detector = BinarySignatureDetector()
            mime_type = detector.detect_from_bytes(content_bytes)

            # If we detected a specific binary format, return it
            if mime_type != 'application/octet-stream':
                from ..interpreter import ContentTypeInterpreter
                ext = ContentTypeInterpreter.get_extension(mime_type)
                return mime_type, ext

            # Optional guard: treat problematic bytes as binary
            if os.getenv('MCARD_INTERPRETER_GUARD_PROBLEMATIC', '0') in ('1', 'true', 'True'):
                try:
                    if ContentAnalyzer.is_problematic_bytes(content_bytes, file_extension):
                        return 'application/octet-stream', ''
                except Exception:
                    pass

            # Try to decode as text if no binary signature matched
            try:
                content_sample = content_bytes.decode('utf-8', errors='replace')
            except Exception:
                return 'application/octet-stream', ''
        else:
            content_sample = content

        # Process as text content using detector registry
        content_sample, lines, first_line = ContentAnalyzer.prepare_content_sample(
            content_sample.encode('utf-8') if isinstance(content_sample, str) else content_sample
        )

        mime_type = detector_registry.detect(content_sample, lines, first_line, file_extension)
        from ..interpreter import ContentTypeInterpreter
        ext = ContentTypeInterpreter.get_extension(mime_type)
        return mime_type, ext

class TextFirstStrategy(DetectionStrategy):
    """Strategy that prioritizes text detection first."""

    def detect(self, content: Union[str, bytes], file_extension: Optional[str] = None) -> Tuple[str, str]:
        """Detect content type with text-first approach."""
        # Always try text detection first
        if isinstance(content, bytes):
            try:
                content_sample = content.decode('utf-8', errors='strict')
            except UnicodeDecodeError:
                # If can't decode as UTF-8, fall back to binary detection
                return BinaryFirstStrategy().detect(content, file_extension)
        else:
            content_sample = content

        # Use detector registry for text detection
        content_sample, lines, first_line = ContentAnalyzer.prepare_content_sample(
            content_sample.encode('utf-8') if isinstance(content_sample, str) else content_sample
        )

        mime_type = detector_registry.detect(content_sample, lines, first_line, file_extension)
        from ..interpreter import ContentTypeInterpreter
        ext = ContentTypeInterpreter.get_extension(mime_type)
        return mime_type, ext
