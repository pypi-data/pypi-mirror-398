"""
Data Format Detectors
=====================

Consolidated detectors for structured data formats:
- JSON (application/json)
- YAML (application/x-yaml)
- CSV (text/csv)
- SQL (text/x-sql)
"""

import json
import re
from typing import List, Optional
from .base_detector import BaseDetector


# ─────────────────────────────────────────────────────────────────────────────
# JSON Detector
# ─────────────────────────────────────────────────────────────────────────────

class JSONDetector(BaseDetector):
    """Detects JSON content."""

    @property
    def content_type_name(self) -> str:
        return "json"

    def get_mime_type(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> str:
        """Return the MIME type if content is detected as JSON."""
        if self.detect(content_sample, lines, first_line, file_extension) > 0.5:
            return 'application/json'
        return 'text/plain'

    def detect(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> float:
        """Detect if content is JSON format."""
        # If file extension is .json, increase confidence
        if file_extension and file_extension.lower() == '.json':
            if self._verify_json_structure(content_sample):
                return 0.95
            return 0.6  # Extension matches but content doesn't look valid

        # Basic structural check
        stripped = content_sample.strip()
        if not ((stripped.startswith('{') and stripped.endswith('}')) or 
                (stripped.startswith('[') and stripped.endswith(']'))):
            return 0.0

        # Reject content with JavaScript/C-style comments
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('//') or stripped_line.startswith('/*'):
                return 0.0

        # Try to parse as JSON
        try:
            json.loads(content_sample)
            return 0.9
        except json.JSONDecodeError:
            return 0.0

    def _verify_json_structure(self, content_sample: str) -> bool:
        """Check if content has valid JSON structure."""
        try:
            json.loads(content_sample)
            return True
        except json.JSONDecodeError:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# YAML Detector
# ─────────────────────────────────────────────────────────────────────────────

class YAMLDetector(BaseDetector):
    """Detects YAML content."""
    
    YAML_START_PATTERNS = [r"^---\s*$", r"^%YAML"]
    KEY_VALUE_PATTERN = r"^\s*[\w.-]+:\s+(?![=\{\[])"
    LIST_ITEM_PATTERN = r"^\s*-\s+[\w\'\"]"

    @property
    def content_type_name(self) -> str:
        return "yaml"

    def get_mime_type(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> str:
        conf = self.detect(content_sample, lines, first_line, file_extension)
        return 'application/x-yaml' if conf > 0.5 else 'text/plain'

    def detect(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> float:
        """Detect if content is YAML format."""
        confidence = 0.0
        
        if file_extension in [".yaml", ".yml"]:
            confidence = max(confidence, 0.95)

        if any(re.match(p, first_line) for p in self.YAML_START_PATTERNS):
            confidence = max(confidence, 0.9)

        yaml_features = 0
        if any(re.match(p, content_sample, re.MULTILINE) for p in self.YAML_START_PATTERNS):
            yaml_features += 2

        for line in lines[:20]:
            stripped_line = line.strip()
            if re.match(self.KEY_VALUE_PATTERN, stripped_line):
                yaml_features += 1
            elif re.match(self.LIST_ITEM_PATTERN, stripped_line):
                yaml_features += 1

        # Only classify as YAML if document starts with '---'
        first_nonempty = next((line for line in lines if line.strip()), "")
        if first_nonempty.strip() == '---':
            if yaml_features > 1:
                confidence = max(confidence, 0.5)
            if yaml_features > 3:
                confidence = max(confidence, 0.75)
            if yaml_features > 5:
                confidence = max(confidence, 0.9)
        else:
            confidence = 0.0

        # Negative: if python keywords are abundant
        python_keywords = ['def ', 'class ', 'import ']
        py_kw_hits = sum(1 for kw in python_keywords if kw in content_sample[:1024])
        if py_kw_hits > 1 and confidence > 0.3:
            confidence -= 0.3

        return max(0.0, min(confidence, 1.0))


# ─────────────────────────────────────────────────────────────────────────────
# CSV Detector
# ─────────────────────────────────────────────────────────────────────────────

class CSVDetector(BaseDetector):
    """Detects CSV (Comma-Separated Values) content."""

    @property
    def content_type_name(self) -> str:
        return "csv"

    def get_mime_type(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> str:
        """Return the MIME type if content is detected as CSV."""
        if self.detect(content_sample, lines, first_line, file_extension) > 0.5:
            return 'text/csv'
        return 'text/plain'

    def detect(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> float:
        """Detect if content is CSV format."""
        if file_extension and file_extension.lower() == '.csv':
            if self._verify_csv_structure(lines):
                return 0.95
            return 0.6

        return self._analyze_csv_content(lines)

    def _verify_csv_structure(self, lines: List[str]) -> bool:
        """Check if content has valid CSV structure."""
        if not lines:
            return False

        sample_lines = [line for line in lines[:10] if line.strip()]
        if not sample_lines:
            return False

        if not all(',' in line for line in sample_lines):
            return False

        comma_counts = [line.count(',') for line in sample_lines]
        
        # All lines have same number of commas
        if len(set(comma_counts)) == 1 and comma_counts[0] > 0:
            return True

        # Allow header row with different comma count
        if len(sample_lines) > 1:
            data_commas_set = set(comma_counts[1:])
            if len(data_commas_set) == 1 and list(data_commas_set)[0] > 0:
                return True

        return False

    def _analyze_csv_content(self, lines: List[str]) -> float:
        """Analyze content to determine if it's CSV format."""
        if not lines:
            return 0.0

        sample_lines = [line for line in lines[:10] if line.strip()]
        if not sample_lines:
            return 0.0

        if not all(',' in line for line in sample_lines):
            return 0.0

        comma_counts = [line.count(',') for line in sample_lines]

        if len(set(comma_counts)) == 1 and comma_counts[0] > 0:
            return 0.9

        if len(sample_lines) > 1:
            data_commas_set = set(comma_counts[1:])
            if len(data_commas_set) == 1 and list(data_commas_set)[0] > 0:
                return 0.8

        if all(count > 0 for count in comma_counts):
            return 0.5

        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# SQL Detector
# ─────────────────────────────────────────────────────────────────────────────

class SQLDetector(BaseDetector):
    """Detects SQL content based on keywords and structure."""
    
    SQL_KEYWORDS = [
        'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'DROP ', 'ALTER ',
        'FROM ', 'WHERE ', 'JOIN ', 'TABLE ', 'INTO ', 'VALUES ', 'SET ', 'PRIMARY KEY',
    ]

    @property
    def content_type_name(self) -> str:
        return "sql"

    def get_mime_type(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> str:
        if self.detect(content_sample, lines, first_line, file_extension) > 0.5:
            return 'text/x-sql'
        return 'text/plain'

    def detect(
        self,
        content_sample: str,
        lines: List[str],
        first_line: str,
        file_extension: Optional[str] = None
    ) -> float:
        """Detect if content is SQL format."""
        if file_extension and file_extension.lower() == '.sql':
            return 0.95
            
        keyword_hits = 0
        for line in lines[:10]:
            for kw in self.SQL_KEYWORDS:
                if kw in line.upper():
                    keyword_hits += 1
                    
        if keyword_hits >= 2:
            return 0.85
        if keyword_hits == 1:
            return 0.6
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Module Exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    'JSONDetector',
    'YAMLDetector',
    'CSVDetector',
    'SQLDetector',
]
