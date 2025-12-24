import re
import json # For negative JSON check
from typing import List, Optional
from .base_detector import BaseDetector

class PythonDetector(BaseDetector):
    def get_mime_type(self, content_sample: str, lines: List[str], first_line: str, file_extension: Optional[str] = None) -> str:
        conf = self.detect(content_sample, lines, first_line, file_extension)
        return 'text/x-python' if conf > 0.5 else 'text/plain'
    @property
    def content_type_name(self) -> str:
        return "python"

    # Keywords that strongly indicate Python
    PYTHON_KEYWORDS = [
        'def ', 'class ', 'import ', 'from ', 'if ', 'else:', 'elif ', 
        'for ', 'while ', 'try:', 'except:', 'finally:', 'with ', 
        'return ', 'yield ', 'lambda ', 'async ', 'await '
    ]
    # Common constructs
    PYTHON_CONSTRUCTS = [
        r'\w+\s*=\s*.*',  # Assignments
        r'print\(',       # Print function
    ]
    # Patterns that are less likely in Python but common in other types
    YAML_PATTERNS = [
        r'^\s*[\w.-]+:\s+(?![=\{\[])', # key: value (not dict or type hint)
        r'^\s*-\s+[\w\'"]',            # - list item
    ]
    MARKDOWN_PATTERNS = [
        r'^#{1,6}\s+\S+',             # ATX Headers: # Header
        r'^.*\n(?:={3,}|-{3,})\s*$',  # Setext Headers
        r'^\s*[\*\+\-]\s+\S+',        # List items: * item, + item, - item
        r'^\s*\d+\.\s+\S+',           # Ordered list items: 1. item
        r'^```(?!(python|py)\b)',     # Non-Python fenced code blocks
    ]

    def detect(self, content_sample: str, lines: List[str], first_line: str, file_extension: Optional[str] = None) -> float:
        confidence = 0.0

        if file_extension == ".py":
            confidence = max(confidence, 0.95)

        if re.match(r"^#!.*python", first_line):
            confidence = max(confidence, 0.98)

        # Positive Python indicators
        keyword_hits = sum(1 for kw in self.PYTHON_KEYWORDS if kw in content_sample)
        construct_hits = sum(1 for pattern in self.PYTHON_CONSTRUCTS if re.search(pattern, content_sample, re.MULTILINE))

        if keyword_hits >= 2: confidence = max(confidence, 0.6)
        if keyword_hits >= 4: confidence = max(confidence, 0.8)
        if keyword_hits > 0 and construct_hits > 0 : confidence = max(confidence, 0.5)


        # Negative indicators (reduce confidence if these are present)
        # Check for YAML structure
        yaml_like_lines = 0
        for line_idx, line_content in enumerate(lines[:15]): # Check first 15 lines
            stripped_line = line_content.strip()
            if stripped_line.startswith('#'): continue # Python comments are fine
            if any(re.match(p, stripped_line) for p in self.YAML_PATTERNS) and \
               not any(kw in stripped_line for kw in ['def ', 'class ', ' = ']): # Avoid flagging Python dicts/assignments
                yaml_like_lines += 1

        if content_sample.lstrip().startswith('---') and '\n' in content_sample.lstrip(): yaml_like_lines += 2 # Strong YAML start
        if content_sample.lstrip().startswith('%YAML'): yaml_like_lines +=3

        if yaml_like_lines > 2 and confidence > 0.3: confidence -= 0.4 # Penalize if YAML signs are strong
        if yaml_like_lines > 4 and confidence > 0.1: confidence -= 0.6


        # Check for Markdown structure
        markdown_like_features = 0
        has_fenced_code_block = False
        for line_content in lines[:15]:
            if '```' in line_content:
                has_fenced_code_block = True
            if any(re.search(p, line_content, re.MULTILINE) for p in self.MARKDOWN_PATTERNS):
                markdown_like_features += 1
        # If there is a fenced code block and multiple markdown features, strongly penalize Python confidence
        if has_fenced_code_block and markdown_like_features > 2:
            confidence = min(confidence, 0.1)
        elif markdown_like_features > 2 and confidence > 0.3:
            confidence -= 0.5
        elif markdown_like_features > 4 and confidence > 0.1:
            confidence -= 0.7


        # Check for pure JSON (if it parses as JSON and lacks Python keywords)
        is_json_structure = (content_sample.strip().startswith('{') and content_sample.strip().endswith('}')) or \
                            (content_sample.strip().startswith('[') and content_sample.strip().endswith(']'))
        if is_json_structure:
            try:
                json.loads(content_sample) # Try to parse
                if not any(kw in content_sample for kw in self.PYTHON_KEYWORDS[:6]): # Check a few core keywords
                    confidence = max(0.0, confidence - 0.8) # Strongly penalize if it's valid JSON without Python keywords
            except json.JSONDecodeError:
                pass # Not valid JSON, so no penalty from this check

        # Check for XML/HTML
        if content_sample.strip().startswith('<') and '>' in content_sample and '</' in content_sample:
            if not any(kw in content_sample for kw in ['def ', 'class ', 'import ']): # if no python keywords
                 confidence = max(0.0, confidence - 0.7)


        # Line structure analysis (indentation, colons)
        python_like_lines = 0
        total_significant_lines = 0
        for line in lines[:30]:
            s_line = line.strip()
            if not s_line or s_line.startswith('#'):
                if s_line.startswith('#!') and 'python' in s_line: # shebang is a strong indicator
                    python_like_lines +=2
                continue
            total_significant_lines += 1
            if s_line.endswith(':') and any(kw in s_line for kw in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except ']):
                python_like_lines += 1
            elif re.match(r'^\s{2,}', line) and not line.isspace(): # Indented line
                python_like_lines += 0.5 

        if total_significant_lines > 3: # Only consider if enough lines
            line_ratio = python_like_lines / total_significant_lines
            if line_ratio > 0.2: confidence = max(confidence, min(0.8, confidence + 0.2))
            if line_ratio > 0.4: confidence = max(confidence, min(0.9, confidence + 0.2))

        return max(0.0, min(confidence, 1.0))
