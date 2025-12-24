"""
Markup Detectors
================

Consolidated detectors for markup and text formats:
- XML (application/xml, text/html, image/svg+xml)
- Markdown (text/markdown)
- PlainText (text/plain) - fallback detector
"""

import json
import re
from typing import List, Optional
from .base_detector import BaseDetector

# Attempt to import lxml for more robust XML parsing
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# XML Detector
# ─────────────────────────────────────────────────────────────────────────────

class XMLDetector(BaseDetector):
    """Detects XML and its subtypes (HTML, SVG)."""
    
    XML_DECLARATION = r"^\s*<\?xml\s+version="
    BASIC_TAG_PAIR = r"<(\w+)\b[^>]*>.*?</\1\s*>"

    @property
    def content_type_name(self) -> str:
        return "xml"

    def detect(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> float:
        """Return confidence score for XML-based content."""
        # Accept both str and bytes
        if isinstance(content_sample, bytes):
            try:
                content_sample = content_sample.decode('utf-8', errors='replace')
            except Exception:
                return 0.0
                
        confidence = 0.0
        
        if file_extension == ".xml":
            confidence = max(confidence, 0.9)

        if re.match(self.XML_DECLARATION, first_line, re.IGNORECASE):
            confidence = max(confidence, 0.95)

        # Basic check for tags
        if '<' in content_sample and '>' in content_sample and '</' in content_sample:
            confidence = max(confidence, 0.5)
            if re.search(self.BASIC_TAG_PAIR, content_sample, re.DOTALL | re.IGNORECASE):
                confidence = max(confidence, 0.7)

        # If lxml is available, try parsing for higher confidence
        if LXML_AVAILABLE and confidence > 0.4:
            try:
                etree.fromstring(content_sample.encode('utf-8', errors='replace'))
                confidence = max(confidence, 0.98)
            except etree.XMLSyntaxError:
                if confidence > 0.8:
                    confidence = 0.6
            except Exception:
                pass
                
        # Negative: if it looks like HTML
        if "<!DOCTYPE html" in content_sample[:200].lower():
            if confidence > 0.3:
                confidence -= 0.4
                
        return max(0.0, min(confidence, 1.0))

    def get_mime_type(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> str:
        """Return the most likely MIME type for XML-based content."""
        if isinstance(content_sample, bytes):
            try:
                content_sample = content_sample.decode('utf-8', errors='replace')
            except Exception:
                return 'application/octet-stream'
                
        if file_extension == ".xml":
            return "application/xml"
        if '<svg' in content_sample.lower():
            return 'image/svg+xml'
        if '<html' in content_sample.lower() or '<!doctype html' in content_sample.lower():
            return 'text/html'
        if content_sample.strip().startswith('<?xml') or re.match(self.XML_DECLARATION, first_line, re.IGNORECASE):
            return 'application/xml'
        if '<' in content_sample and '>' in content_sample and '</' in content_sample:
            return 'application/xml'
        return 'text/plain'


# ─────────────────────────────────────────────────────────────────────────────
# Markdown Detector
# ─────────────────────────────────────────────────────────────────────────────

class MarkdownDetector(BaseDetector):
    """Detects Markdown content."""
    
    MD_PATTERNS = [
        r"^#{1,6}\s+\S+",             # ATX Headers
        r"^\s*[\*\+\-]\s+\S+",        # List items
        r"^\s*\d+\.\s+\S+",           # Ordered list items
        r"`{1,3}[^`]+`{1,3}",         # Inline code
        r"\[[^\]]+\]\([^\)]+\)",      # Links
        r"!\[[^\]]+\]\([^\)]+\)",     # Images
        r"^\s*>.*"                    # Blockquotes
    ]
    SETEXT_HEADER_PATTERN = r"^.*\n(?:={3,}|-{3,})\s*$"

    @property
    def content_type_name(self) -> str:
        return "markdown"

    def get_mime_type(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> str:
        conf = self.detect(content_sample, lines, first_line, file_extension)
        return 'text/markdown' if conf > 0.5 else 'text/plain'

    def detect(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> float:
        """Detect if content is Markdown format."""
        confidence = 0.0
        
        if file_extension in [".md", ".markdown"]:
            confidence = max(confidence, 0.95)

        md_features = 0
        
        if re.search(self.SETEXT_HEADER_PATTERN, content_sample, re.MULTILINE):
            md_features += 2

        for line in lines[:20]:
            if any(re.search(p, line) for p in self.MD_PATTERNS):
                md_features += 1

        has_code_fence = "```" in content_sample
        if has_code_fence:
            md_features += 1

        # Boost confidence based on features
        if md_features > 1 and has_code_fence:
            confidence = max(confidence, 0.85)
        if md_features > 3 and has_code_fence:
            confidence = max(confidence, 0.95)
        elif md_features > 1:
            confidence = max(confidence, 0.6)
        elif md_features > 3:
            confidence = max(confidence, 0.8)
        elif md_features > 5:
            confidence = max(confidence, 0.9)

        # Negative: if it looks like JSON or XML
        stripped = content_sample.strip()
        if (stripped.startswith('{') and stripped.endswith('}')) or \
           (stripped.startswith('[') and stripped.endswith(']')):
            try:
                json.loads(content_sample)
                if confidence > 0.3:
                    confidence -= 0.4
            except Exception:
                pass

        if stripped.startswith('<') and '<?xml' in content_sample[:100]:
            if confidence > 0.3:
                confidence -= 0.4

        return max(0.0, min(confidence, 1.0))


# ─────────────────────────────────────────────────────────────────────────────
# PlainText Detector (Fallback)
# ─────────────────────────────────────────────────────────────────────────────

# Known binary extensions that should not be classified as plain text
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
PDF_EXTENSIONS = {'.pdf'}


class PlainTextDetector(BaseDetector):
    """
    Fallback detector for plain text content.
    
    This provides a baseline confidence when no other specific text type is found.
    It should have low confidence so more specific detectors can override it.
    """

    @property
    def content_type_name(self) -> str:
        return "text"

    def get_mime_type(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> str:
        return 'text/plain'

    def detect(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> float:
        """Detect if content is plain text (fallback)."""
        if not content_sample and not lines:
            return 0.1  # Empty is still considered 'text' by default

        if content_sample:
            # Known binary extensions
            if file_extension and (file_extension in IMAGE_EXTENSIONS or file_extension in PDF_EXTENSIONS):
                return 0.0

            # Detect ambiguous CSV-like content
            if ',' in content_sample and isinstance(lines, list) and len(lines) < 5:
                comma_lines = sum(1 for line in lines if ',' in line)
                if comma_lines > 0 and comma_lines == len(lines):
                    delimiter_counts = [line.count(',') for line in lines[:3] if line.strip()]
                    if delimiter_counts and all(count <= 2 for count in delimiter_counts):
                        return 0.8

            return 0.15
            
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Module Exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    'XMLDetector',
    'MarkdownDetector',
    'PlainTextDetector',
]
