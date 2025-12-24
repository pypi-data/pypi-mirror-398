"""
Detectors package for content type interpretation.

Consolidated Modules:
- data_format_detectors: JSON, YAML, CSV, SQL
- markup_detectors: XML, Markdown, PlainText

Standalone Modules (too large or specialized to consolidate):
- binary_detector: Binary file signature detection
- language_detector: Programming language detection
- python_detector: Python-specific detection
- text_format_detector: General text format detection
- obj_detector: 3D OBJ file detection
"""

# Import from consolidated modules
from .data_format_detectors import JSONDetector, YAMLDetector, CSVDetector, SQLDetector
from .markup_detectors import XMLDetector, MarkdownDetector, PlainTextDetector

# Import from standalone modules
from .base_detector import BaseDetector
from .binary_detector import BinarySignatureDetector
from .python_detector import PythonDetector
from .language_detector import ProgrammingLanguageDetector
from .text_format_detector import TextFormatDetector
from .obj_detector import OBJDetector

# Registry
from .registry import DetectorRegistry, registry, DETECTORS

__all__ = [
    # Base
    "BaseDetector",
    # Consolidated: Data formats
    "JSONDetector",
    "YAMLDetector",
    "CSVDetector",
    "SQLDetector",
    # Consolidated: Markup
    "XMLDetector",
    "MarkdownDetector",
    "PlainTextDetector",
    # Standalone
    "BinarySignatureDetector",
    "PythonDetector",
    "ProgrammingLanguageDetector",
    "TextFormatDetector",
    "OBJDetector",
    # Registry
    "DetectorRegistry",
    "registry",
    "DETECTORS",
]

# Ordered list of detector classes for strategy pattern
DETECTOR_CLASSES = [
    PythonDetector,
    JSONDetector,
    XMLDetector,
    YAMLDetector,
    CSVDetector,
    SQLDetector,
    MarkdownDetector,
    PlainTextDetector,
]
