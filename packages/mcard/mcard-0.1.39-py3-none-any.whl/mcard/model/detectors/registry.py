"""
Central registry for all content type detectors.

This module imports detectors from:
- Consolidated modules (data_format_detectors, markup_detectors)
- Standalone modules (binary, language, python, obj, text_format)
"""

from .binary_detector import BinarySignatureDetector
from .data_format_detectors import JSONDetector, YAMLDetector, CSVDetector, SQLDetector
from .markup_detectors import XMLDetector, MarkdownDetector, PlainTextDetector
from .language_detector import ProgrammingLanguageDetector
from .python_detector import PythonDetector
from .text_format_detector import TextFormatDetector
from .obj_detector import OBJDetector


# Detectors in execution priority order
DETECTORS = [
    # Binary format detection first
    BinarySignatureDetector(),

    # Programming languages have higher priority
    PythonDetector(),
    ProgrammingLanguageDetector(),

    # Structured data formats
    XMLDetector(),
    JSONDetector(),

    # 3D file formats
    OBJDetector(),

    # Markup/documentation formats
    MarkdownDetector(),

    # Data formats - lower priority to avoid false positives
    SQLDetector(),
    CSVDetector(),
    YAMLDetector(),  # Lower priority to avoid misclassification

    # Generic text formats (fallback)
    TextFormatDetector(),
    PlainTextDetector(),
]


class DetectorRegistry:
    """
    Central registry to manage and invoke detectors in order.
    
    Uses highest confidence matching strategy.
    """
    
    def __init__(self):
        self.detectors = DETECTORS

    def detect(
        self,
        content_sample: str,
        lines,
        first_line: str,
        file_extension: str = None
    ) -> str:
        """
        Detect content type and return the most likely MIME type.
        
        Args:
            content_sample: String sample of the content
            lines: List of lines from the beginning of content
            first_line: The first line of content
            file_extension: Optional file extension hint
            
        Returns:
            The detected MIME type string
        """
        # Special case for ambiguous CSV-like content
        if isinstance(content_sample, str) and ',' in content_sample:
            if isinstance(lines, list) and len(lines) < 3:
                comma_lines = sum(1 for line in lines if ',' in line)
                if comma_lines > 0 and comma_lines == len(lines):
                    delimiter_counts = [line.count(',') for line in lines if line.strip()]
                    if delimiter_counts and all(count <= 2 for count in delimiter_counts):
                        return 'text/plain'

        # Normal detection: find highest confidence match
        best_confidence = 0.0
        best_mime = 'text/plain'
        
        for detector in self.detectors:
            confidence = detector.detect(content_sample, lines, first_line, file_extension)
            if confidence > best_confidence:
                mime = detector.get_mime_type(content_sample, lines, first_line, file_extension)
                if mime:
                    best_confidence = confidence
                    best_mime = mime
                    
        return best_mime


# Singleton registry instance
registry = DetectorRegistry()
