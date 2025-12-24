"""
Content analysis utilities for detecting problematic content patterns.
"""
from typing import Optional

# Constants for sampling and limits
MAX_SAMPLE_BYTES = 64 * 1024  # 64KB
MAX_SAMPLE_LINES = 100

# Heuristic thresholds for problematic content detection
_EXT_LONG_LINE_KNOWN = {
    '.js', '.mjs', '.min.js', '.bundle.js',
    '.css', '.min.css',
    '.json', '.jsonl',
    '.xml', '.svg',
    '.html', '.htm',
    '.map',  # source maps
    '.wasm',
}

_PROBLEMATIC_MAX_KNOWN_TYPE = 1024 * 1024  # 1MB
_PROBLEMATIC_SAMPLE_SIZE = 32 * 1024  # 32KB
_PROBLEMATIC_MIN_MULTI_POSITION = 100 * 1024  # 100KB
_PATHOLOGICAL_NO_BREAK_MIN = 8192
_PATHOLOGICAL_NO_BREAK_STRICT_MIN = 32 * 1024
_NULL_RATIO_THRESHOLD = 0.1
_CTRL_RATIO_THRESHOLD = 0.2
_MAX_LINE_LENGTH_KNOWN = 100000
_MAX_LINE_LENGTH_DEFAULT = 50000
_AVG_LINE_LENGTH_KNOWN = 20000
_AVG_LINE_LENGTH_DEFAULT = 5000

class ContentAnalyzer:
    """Utility class for analyzing content patterns and detecting problematic content."""

    @staticmethod
    def is_known_long_line_extension(file_extension: Optional[str]) -> bool:
        """Return True if extension is typically legitimate with long lines."""
        if not file_extension:
            return False
        return file_extension.lower() in _EXT_LONG_LINE_KNOWN

    @staticmethod
    def is_unstructured_binary(sample: bytes) -> bool:
        """Heuristic check for unstructured binary content."""
        if len(sample) < 512:
            return False
        null_count = sample.count(b'\x00')
        control_chars = sum(1 for b in sample if b < 32 and b not in (9, 10, 13))
        null_ratio = null_count / len(sample)
        control_ratio = control_chars / len(sample)
        return null_ratio > _NULL_RATIO_THRESHOLD or control_ratio > _CTRL_RATIO_THRESHOLD

    @staticmethod
    def has_pathological_lines(sample: bytes, is_known_type: bool) -> bool:
        """Detect pathological line structures (extremely long or no breaks)."""
        max_line_len = _MAX_LINE_LENGTH_KNOWN if is_known_type else _MAX_LINE_LENGTH_DEFAULT
        max_avg_len = _AVG_LINE_LENGTH_KNOWN if is_known_type else _AVG_LINE_LENGTH_DEFAULT

        if b'\n' not in sample and b'\r' not in sample and len(sample) >= _PATHOLOGICAL_NO_BREAK_MIN:
            if (not is_known_type) or len(sample) >= _PATHOLOGICAL_NO_BREAK_STRICT_MIN:
                return True

        lines = sample.replace(b'\r\n', b'\n').replace(b'\r', b'\n').split(b'\n')
        if not lines:
            return False

        if any(len(line) > max_line_len for line in lines):
            return True

        if len(lines) > 1:
            avg_len = sum(len(line) for line in lines) / len(lines)
            if avg_len > max_avg_len:
                return True

        return False

    @staticmethod
    def is_problematic_bytes(content: bytes, file_extension: Optional[str] = None) -> bool:
        """
        Byte-content heuristic for detecting problematic content patterns.
        
        Args:
            content: The byte content to analyze
            file_extension: Optional file extension for type-aware thresholds
            
        Returns:
            True if content appears problematic
        """
        if not content:
            return False

        is_known_type = ContentAnalyzer.is_known_long_line_extension(file_extension)
        sample = content[:_PROBLEMATIC_SAMPLE_SIZE]

        if ContentAnalyzer.is_unstructured_binary(sample):
            return True

        if ContentAnalyzer.has_pathological_lines(sample, is_known_type):
            return True

        return False

    @staticmethod
    def prepare_content_sample(content: bytes, max_bytes: int = MAX_SAMPLE_BYTES, 
                             max_lines: int = MAX_SAMPLE_LINES) -> tuple[str, list[str], str]:
        """
        Prepare content sample for analysis.
        
        Args:
            content: Raw byte content
            max_bytes: Maximum bytes to sample
            max_lines: Maximum lines to process
            
        Returns:
            Tuple of (content_sample, lines, first_line)
        """
        try:
            content_sample = content.decode('utf-8', errors='replace')
        except Exception:
            content_sample = str(content, errors='replace')

        # For very large content, use a sample
        if len(content_sample) > max_bytes:
            content_for_lines = content_sample[:max_bytes]
        else:
            content_for_lines = content_sample

        lines = content_for_lines.split('\n')[:max_lines]
        first_line = lines[0] if lines else ''

        return content_sample, lines, first_line
