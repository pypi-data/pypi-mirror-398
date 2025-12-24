"""
Content type detection and validation service.

This module provides a unified interface for content type detection and validation
using a modular architecture with separate concerns for detection strategies,
validation, and content analysis utilities.
"""
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, Union

# Import modular components
from .validators.validation_registry import validation_registry, ValidationError
from .strategies.detection_strategy import BinaryFirstStrategy, DetectionStrategy
from .utils.content_analyzer import ContentAnalyzer
from .detectors.binary_detector import BinarySignatureDetector


# Module logger
LOGGER = logging.getLogger(__name__)

# Re-export ValidationError for backward compatibility
__all__ = ['ContentTypeInterpreter', 'ValidationError']

class ContentTypeInterpreter:
    """
    Unified service for content type detection and validation.
    
    This consolidated class uses modular components internally while maintaining
    the same external API for backward compatibility.
    """

    # Collection of text-based MIME types (maintained for compatibility)
    TEXT_MIME_TYPES = frozenset({
        # Basic text formats
        'text/plain', 'text/html', 'text/xml', 'text/csv', 'text/css',
        'text/javascript', 'text/markdown', 'text/x-python', 'text/x-java',
        'text/x-c', 'text/x-c++', 'text/x-sql', 'text/jsx', 'text/typescript',

        # Application text formats
        'application/json', 'application/xml', 'application/x-yaml',
        'application/javascript', 'application/x-httpd-php', 'application/x-sh',
        'application/x-tex', 'application/3d-obj',

        # Diagram formats
        'text/vnd.graphviz', 'text/x-mermaid', 'text/x-plantuml',

        # Configuration formats
        'application/x-properties', 'application/toml',
    })

    # Unified MIME to extension mapping (maintained for compatibility)
    _MIME_TO_EXTENSION = {
        # Images
        'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif',
        'image/bmp': 'bmp', 'image/x-icon': 'ico', 'image/svg+xml': 'svg',
        'image/djvu': 'djvu', 'image/vnd.djvu': 'djv', 'image/webp': 'webp',

        # Audio/Video
        'audio/wav': 'wav', 'audio/x-wav': 'wav', 'video/mp4': 'mp4',
        'video/quicktime': 'mov',

        # Documents
        'application/pdf': 'pdf', 'application/msword': 'doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.ms-excel': 'xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.ms-powerpoint': 'ppt',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',

        # Archives
        'application/zip': 'zip', 'application/gzip': 'gz',
        'application/x-rar-compressed': 'rar', 'application/x-7z-compressed': '7z',

        # Database
        'application/x-sqlite3': 'db', 'application/x-parquet': 'parquet',

        # Text formats
        'text/plain': 'txt', 'text/html': 'html', 'text/xml': 'xml',
        'text/csv': 'csv', 'text/css': 'css', 'text/javascript': 'js',
        'text/markdown': 'md', 'text/x-python': 'py', 'text/x-java': 'java',
        'text/x-c': 'c', 'text/x-sql': 'sql', 'text/jsx': 'js',

        # Application formats
        'application/json': 'json', 'application/xml': 'xml',
        'application/x-yaml': 'yaml', 'application/javascript': 'js',
        'application/x-httpd-php': 'php', 'application/x-sh': 'sh',
        'application/x-tex': 'tex',

        # Diagram formats
        'text/vnd.graphviz': 'dot', 'text/x-mermaid': 'mmd',
        'text/x-plantuml': 'puml',

        # 3D Object formats
        'application/3d-obj': 'obj',

        # Configuration formats
        'application/x-properties': 'properties', 'application/toml': 'toml',
    }

    def __init__(self, detection_strategy: Optional[DetectionStrategy] = None):
        """
        Initialize the interpreter with a detection strategy.
        
        Args:
            detection_strategy: Strategy for content type detection.
                               Defaults to BinaryFirstStrategy for compatibility.
        """
        self._detection_strategy = detection_strategy or BinaryFirstStrategy()

    @staticmethod
    def _decode_utf8(data: bytes) -> str:
        """Decode bytes to UTF-8 string using a consistent policy."""
        return data.decode('utf-8', errors='replace')

    @staticmethod
    def detect_content_type(content: Union[str, bytes], file_extension: str = None) -> Tuple[str, str]:
        """
        Detect content type and suggested extension.
        
        This method now uses the modular detection strategy while maintaining
        the same external interface for backward compatibility.
        
        Args:
            content: The content to analyze
            file_extension: Optional file extension hint
            
        Returns:
            Tuple of (mime_type, extension)
        """
        # Use default strategy for static method (maintains backward compatibility)
        strategy = BinaryFirstStrategy()
        return strategy.detect(content, file_extension)

    def detect_content_type_with_strategy(self, content: Union[str, bytes], file_extension: str = None) -> Tuple[str, str]:
        """
        Detect content type using the configured strategy.
        
        Args:
            content: The content to analyze
            file_extension: Optional file extension hint
            
        Returns:
            Tuple of (mime_type, extension)
        """
        return self._detection_strategy.detect(content, file_extension)

    # Backward compatibility methods that delegate to ContentAnalyzer
    @staticmethod
    def _is_known_long_line_extension(file_extension: Optional[str]) -> bool:
        """Backward compatibility wrapper for ContentAnalyzer."""
        return ContentAnalyzer.is_known_long_line_extension(file_extension)

    @staticmethod
    def _is_unstructured_binary(sample: bytes) -> bool:
        """Backward compatibility wrapper for ContentAnalyzer."""
        return ContentAnalyzer.is_unstructured_binary(sample)

    @staticmethod
    def _has_pathological_lines(sample: bytes, is_known_type: bool) -> bool:
        """Backward compatibility wrapper for ContentAnalyzer."""
        return ContentAnalyzer.has_pathological_lines(sample, is_known_type)

    @staticmethod
    def _is_problematic_bytes(content: bytes, file_extension: Optional[str] = None) -> bool:
        """Backward compatibility wrapper for ContentAnalyzer."""
        return ContentAnalyzer.is_problematic_bytes(content, file_extension)

    @staticmethod
    def _detect_by_signature(content: bytes) -> str:
        """Backward compatibility method that delegates to BinarySignatureDetector."""
        detector = BinarySignatureDetector()
        return detector.detect_from_bytes(content)

    @staticmethod
    def _detect_bytes_content(content: bytes) -> str:
        """Backward compatibility method that uses the detection strategy."""
        strategy = BinaryFirstStrategy()
        mime_type, _ = strategy.detect(content)
        return mime_type

    def validate_content(self, content: Union[str, bytes]) -> None:
        """
        Validate content based on its detected type.
        
        This method now delegates to the validation registry for better modularity.
        
        Args:
            content: The content to validate
            
        Raises:
            ValidationError: If content is invalid
        """
        mime_type, _ = self._detection_strategy.detect(content)
        validation_registry.validate(content, mime_type)

    @staticmethod
    def validate_content_static(content: Union[str, bytes]) -> None:
        """
        Static method for validating content (backward compatibility).
        
        Args:
            content: The content to validate
            
        Raises:
            ValidationError: If content is invalid
        """
        # Use default strategy for static method
        strategy = BinaryFirstStrategy()
        mime_type, _ = strategy.detect(content)
        validation_registry.validate(content, mime_type)


    @staticmethod
    def is_binary_content(content: Union[str, bytes]) -> bool:
        """
        Determine if content should be treated as binary.
        
        This method uses multiple heuristics:
        1. If content is already a string, it's not binary
        2. For bytes content:
           - Check for known binary signatures
           - Try UTF-8 decoding
           - Analyze content patterns
        """
        # Delegate to BinarySignatureDetector's is_binary_content method
        # If content is already a string, it's not binary
        if isinstance(content, str):
            return False

        # Check for binary signatures
        for signature, _ in BinarySignatureDetector.SIGNATURES.items():
            if content.startswith(signature):
                return True

        # Try to decode as UTF-8
        try:
            # If content has null bytes, it's likely binary
            if b'\x00' in content:
                return True

            # Attempt to decode as UTF-8
            content.decode('utf-8', errors='strict')

            # If we get here, the content can be decoded as UTF-8
            # Check for high concentration of non-printable chars (indicating binary)
            sample = content[:4096] if len(content) > 4096 else content
            
            # Handle empty content - not binary (it's just empty text)
            if len(sample) == 0:
                return False
            
            non_text_chars = sum(1 for b in sample if b < 9 or (b > 13 and b < 32) or b > 126)
            text_ratio = 1 - (non_text_chars / len(sample))

            # If more than 30% non-printable characters, consider it binary
            return text_ratio < 0.7

        except UnicodeDecodeError:
            # If it can't be decoded as UTF-8, it's binary
            return True

    @staticmethod
    def is_xml_content(content: Union[str, bytes]) -> bool:
        """Check if content is valid XML."""
        # Delegate to XMLDetector's is_valid_xml method
        try:
            if isinstance(content, str):
                content = content.encode('utf-8')

            # Try to parse the XML without requiring XML declaration
            ET.fromstring(content)
            LOGGER.debug("Valid XML content detected.")
            return True
        except Exception as e:
            LOGGER.debug("Invalid XML content detected: %s", str(e))
            return False

    @staticmethod
    def is_svg_content(content: Union[str, bytes]) -> bool:
        """Check if content is SVG."""
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')

        # First check if it's valid XML
        if not ContentTypeInterpreter.is_xml_content(content):
            return False

        try:
            # Parse XML and check for SVG namespace
            tree = ET.fromstring(content)
            return (
                tree.tag == 'svg' or
                tree.tag.endswith('}svg') or
                any(attr.endswith('xmlns') and 'svg' in value
                    for attr, value in tree.attrib.items())
            )
        except Exception:
            return False

    @staticmethod
    def is_mermaid_content(content: str) -> bool:
        """Check if content is Mermaid diagram."""
        content = content.strip().lower()
        mermaid_keywords = [
            'graph ', 'sequencediagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'gantt',
            'pie', 'flowchart', 'journey'
        ]
        return any(content.startswith(keyword.lower()) for keyword in mermaid_keywords)

    @staticmethod
    def is_diagram_content(content: str) -> bool:
        """Check if content is a diagram format."""
        content = content.strip().lower()
        # Check for PlantUML
        if content.startswith('@startuml') and content.endswith('@enduml'):
            return True
        # Check for Graphviz
        if content.startswith(('digraph', 'graph', 'strict')):
            return True
        # Check for Mermaid
        return ContentTypeInterpreter.is_mermaid_content(content)

    @staticmethod
    def get_extension(mime_type: str) -> str:
        """Get file extension from MIME type."""
        return ContentTypeInterpreter._MIME_TO_EXTENSION.get(mime_type, '')

    @staticmethod
    def get_default_extension(mime_type: str) -> str:
        """
        Return the default file extension for a given MIME type.
        """
        return ContentTypeInterpreter._MIME_TO_EXTENSION.get(mime_type, '')
