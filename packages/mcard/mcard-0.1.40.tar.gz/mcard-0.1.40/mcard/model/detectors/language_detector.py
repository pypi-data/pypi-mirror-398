"""
Programming language detection module.
"""
import re
import json
from typing import List, Optional

# Import XMLDetector from consolidated markup module
from .markup_detectors import XMLDetector


from .base_detector import BaseDetector

class ProgrammingLanguageDetector(BaseDetector):
    """Detect various programming language source files."""
    @property
    def content_type_name(self) -> str:
        return "programming_language"

    def detect(self, content_sample: str, lines, first_line: str, file_extension: str = None) -> float:
        # Use the get_mime_type logic for detection, assign confidence
        mime = self.get_mime_type(content_sample, lines, first_line, file_extension)
        if mime and mime != 'text/plain':
            return 0.9
        return 0.0

    def get_mime_type(self, content_sample: str, lines, first_line: str, file_extension: str = None) -> str:
        # Original detection logic
        text_content = content_sample
        # Get the full content for better detection accuracy when it comes to programming languages
        if not lines:
            lines = text_content.split('\n')
        first_line = first_line or (lines[0].strip() if lines else '')
        content_sample = text_content[:5000] # Increased sample size for better accuracy
        # 1. Python detection - highest priority due to its flexibility
        if self._is_python(first_line, content_sample, lines):
            return 'text/x-python'
        # 2. C/C++ detection
        c_type = self._detect_c_family(content_sample)
        if c_type:
            return c_type
        # 3. JavaScript/JSX detection
        js_type = self._detect_js_type(content_sample)
        if js_type:
            return js_type
        # 4. TypeScript detection
        if self._is_typescript(content_sample):
            return 'text/typescript'
        # If no specific language is detected
        return 'text/plain'

        # Implement detection with priority order
        # 1. Python detection - highest priority due to its flexibility
        if ProgrammingLanguageDetector._is_python(first_line, content_sample, lines):
            return 'text/x-python'

        # 2. C/C++ detection - these have distinctive patterns
        c_type = ProgrammingLanguageDetector._detect_c_family(content_sample)
        if c_type:
            return c_type

        # 3. JavaScript/JSX detection
        js_type = ProgrammingLanguageDetector._detect_js_type(content_sample)
        if js_type:
            return js_type

        # 4. TypeScript detection
        if ProgrammingLanguageDetector._is_typescript(content_sample):
            return 'text/typescript'

        # If no specific language is detected
        return 'text/plain' # Default for unrecognized programming languages

    @staticmethod
    def _is_python(first_line: str, content_sample: str, lines: List[str]) -> bool:
        """Check if content is Python code using a comprehensive set of patterns."""
        # Look at imports first - this is the most reliable Python indicator
        import_patterns = [
            re.search(r'^\s*import\s+(\w+|\w+\.\w+)(\s+as\s+\w+)?\s*(#.*)?$', content_sample, re.MULTILINE) is not None,
            re.search(r'^\s*from\s+(\w+|\w+\.\w+)\s+import\s+', content_sample, re.MULTILINE) is not None,
        ]

        # Standard library imports are very strong indicators
        std_lib_imports = [
            'import os', 'import sys', 'import re', 'import json', 'import time', 'import datetime',
            'import math', 'import random', 'import io', 'import collections', 'import unittest',
            'from os import', 'from sys import', 'from datetime import', 'from collections import',
            'import numpy', 'import pandas', 'from PIL import', 'import matplotlib', 'import torch',
            'import tensorflow', 'import sklearn', 'import requests', 'import flask', 'import django',
            'import pathlib', 'import typing', 'import csv', 'import argparse', 'import logging',
            'import multiprocessing', 'import threading', 'import queue', 'import asyncio'
        ]

        has_std_lib_import = any(lib in content_sample for lib in std_lib_imports)

        # Very strong indicator - if we have multiple standard library imports, it's definitely Python
        if has_std_lib_import and any(import_patterns):
            return True

        # Strong indicators (individually sufficient)
        strong_indicators = [
            # Shebang line
            first_line.startswith('#!') and ('python' in first_line.lower()),
            # Module docstring pattern
            (first_line.startswith('"""') or first_line.startswith("'''")) and len(lines) > 3,
            # Python special methods or variables
            '__name__' in content_sample and '__main__' in content_sample,
            'if __name__ ==' in content_sample, # Common pattern: if __name__ == "__main__":
            # Class and function definitions with Python-specific syntax
            re.search(r'^\s*def\s+\w+\s*\(', content_sample, re.MULTILINE) is not None and not 'function' in content_sample,
            re.search(r'^\s*class\s+\w+\s*[\(:]', content_sample, re.MULTILINE) is not None,
            # Clear decorators (very Python-specific)
            re.search(r'^\s*@\w+', content_sample, re.MULTILINE) is not None,
            # Python-style exception handling
            re.search(r'try\s*:\s*\n.*?except\s+\w+', content_sample, re.DOTALL) is not None,
        ]

        if any(strong_indicators):
            return True

        # Count Python-specific patterns
        python_patterns = [
            # Common keywords with Python-specific syntax
            re.search(r'\bif\b.*?:', content_sample) is not None,
            re.search(r'\belif\b.*?:', content_sample) is not None,
            re.search(r'\belse\s*:', content_sample) is not None,
            re.search(r'\bfor\b.*?\bin\b.*?:', content_sample) is not None,
            re.search(r'\bwhile\b.*?:', content_sample) is not None,
            re.search(r'\btry\s*:', content_sample) is not None,
            re.search(r'\bexcept\b.*?:', content_sample) is not None,
            re.search(r'\bfinally\s*:', content_sample) is not None,
            re.search(r'\breturn\b\s+[^;]+$', content_sample, re.MULTILINE) is not None,  # Return without semicolon
            # Python's None, True, False with correct capitalization
            re.search(r'\bNone\b', content_sample) is not None,
            re.search(r'\bTrue\b', content_sample) is not None,
            re.search(r'\bFalse\b', content_sample) is not None,
            # Python-specific string formatting
            re.search(r'f["\']\{.*?\}', content_sample) is not None,  # f-strings
            re.search(r'\.format\(', content_sample) is not None,  # str.format()
            re.search(r'%[sd]\s+%' , content_sample) is not None,  # % formatting (less common now)
            # Python's with statement 
            re.search(r'\bwith\b.*?\bas\b.*?:', content_sample) is not None,
            # Typical Python style indentation with consistent 4-space blocks
            len([line for line in lines[:20] if line.startswith('    ') and not line.startswith('        ')]) > 3,
            # Python decorators (already in strong_indicators, but can be counted here too)
            any(line.strip().startswith('@') for line in lines[:50]), # Check more lines for decorators
            # Python comprehensions (very distinctive)
            re.search(r'\[.*?\bfor\b.*?\bin\b.*?\]', content_sample) is not None,  # List comprehension
            re.search(r'\{.*?:.*?\bfor\b.*?\bin\b.*?\}', content_sample) is not None,  # Dict comprehension
            # Python lambda functions
            re.search(r'\blambda\b.*?:', content_sample) is not None,
        ]

        # If we have multiple Python patterns, it's likely Python code
        pattern_count = sum(1 for pattern in python_patterns if pattern)
        if pattern_count >= 3:  # Threshold for confidence
            return True

        # Check for negative indicators that would indicate it's not Python
        # This is checked AFTER strong positive indicators and general pattern counts.

        _new_negative_indicators = []

        # YAML specific negative indicators
        if content_sample.lstrip().startswith('---') and '\n' in content_sample.lstrip(): # YAML document start
            _new_negative_indicators.append(True)
        if content_sample.lstrip().startswith('%YAML'): # YAML directive
            _new_negative_indicators.append(True)

        yaml_heuristic_lines = 0
        for line_idx, line_content in enumerate(lines[:20]): # Check first 20 lines
            stripped_line = line_content.strip()
            if stripped_line.startswith('#'): continue

            # Matches "key: value" not part of a Python dict/type hint, or complex expression
            if re.match(r'^\s*[\w.-]+:\s+(?![=\{\[])', stripped_line) and \
               not re.search(r'\b(def|class|if|for|while|lambda)\b', stripped_line) and \
               not (stripped_line.count(':') == 1 and '(' in stripped_line and ')' in stripped_line): # Avoid simple func(arg: type)
                yaml_heuristic_lines += 1
            # Matches "- item"
            elif re.match(r'^\s*-\s+[\w\'"]', stripped_line):
                 yaml_heuristic_lines += 1
        if yaml_heuristic_lines > 3: # Heuristic: if more than 3 such lines, likely YAML
            _new_negative_indicators.append(True)

        # Markdown specific negative indicators
        atx_header_count = 0
        for line_content in lines[:20]: # Check first 20 lines
            stripped_line = line_content.strip()
            # Matches '# Header' but not just '### comment'
            if re.match(r'^#{1,6}\s+\S+', stripped_line):
                 atx_header_count +=1
        if atx_header_count > 2: # Heuristic: if more than 2 ATX headers
            _new_negative_indicators.append(True)

        if re.search(r'^.*\n(?:={3,}|-{3,})\s*$', content_sample, re.MULTILINE): # Setext header
            _new_negative_indicators.append(True)

        md_list_item_count = sum(1 for line_content in lines[:20] if re.match(r'^\s*[\*\+\-]\s+\S+|^\s*\d+\.\s+\S+', line_content.strip()) and not line_content.strip().startswith('#'))
        if md_list_item_count > 3: # Heuristic: if more than 3 Markdown list items
            _new_negative_indicators.append(True)

        if re.search(r'^```(?!(python|py)\b)', content_sample, re.MULTILINE): # Non-Python fenced code block
            _new_negative_indicators.append(True)

        negative_indicators = [
            # Original: Clear XML-like content (HTML, SVG, XML)
            # This is better handled by checking if XMLDetector identifies it as such first.
            # content_sample.strip().startswith('<') and '>' in content_sample,

            # Original: Mermaid-specific content
            content_sample.strip().startswith('graph ') or content_sample.strip().startswith('flowchart '),
        ]
        negative_indicators.extend(_new_negative_indicators)

        # Refined JSON check:
        # If it looks like JSON, parses as JSON, and has no strong Python keywords, it's a negative.
        looks_like_json_struct = (content_sample.strip().startswith('{') and content_sample.strip().endswith('}')) or \
                                 (content_sample.strip().startswith('[') and content_sample.strip().endswith(']'))
        if looks_like_json_struct:
            try:
                json.loads(content_sample) # Try to parse
                # Check for absence of Python keywords in what looks like pure JSON
                if not any(kw in content_sample for kw in ['import ', 'def ', 'class ', 'for ', 'while ', 'try:', 'lambda ', ' if ', ' else ']):
                    negative_indicators.append(True) # It's pure JSON
            except json.JSONDecodeError:
                pass # Doesn't parse as JSON, so not a JSON negative indicator.

        if any(indicator for indicator in negative_indicators if indicator is True):
            return False

        # Final check: ratio of Python-like lines to total non-empty lines
        # This is a weaker heuristic and should be used cautiously.
        python_line_count = 0
        non_empty_lines = [line for line in lines[:50] if line.strip()] # Analyze first 50 non-empty lines
        if not non_empty_lines:
            return False

        for line in non_empty_lines:
            stripped = line.strip()
            if (re.match(r'^[\s]*def\s+', line) or
                re.match(r'^[\s]*class\s+', line) or
                re.match(r'^[\s]*import\s+', line) or
                re.match(r'^[\s]*from\s+.+\s+import\s+', line) or
                (stripped.endswith(':') and not stripped.startswith('#')) or # Ends with colon (e.g., control flow, func/class def)
                '#' in stripped and not stripped.startswith('#') or # Contains a comment not at the start
                'self.' in stripped or # Common in Python classes
                'return ' in stripped or
                re.search(r'\s+=\s+', stripped)): # Assignment
                    python_line_count += 1

        # If more than 25% of the lines look like Python, it probably is Python
        # This threshold might need adjustment based on testing.
        if len(non_empty_lines) > 5: # Apply ratio only if there are enough lines
             return (python_line_count / len(non_empty_lines)) > 0.25
        elif pattern_count >=1 and len(non_empty_lines) <=5 : # For very short snippets, 1-2 patterns might be enough
            return True

        return False # Default if not confidently Python

    # HTML detection is now handled by XMLDetector with proper XML hierarchy
    # This is kept as a placeholder to maintain backward compatibility if anything was relying on it.
    @staticmethod
    def _is_html(content: str) -> bool:
        """Check if content is HTML - delegates to XMLDetector for proper hierarchy."""
        return XMLDetector.is_html_content(content)

    @staticmethod
    def _detect_js_type(content_sample: str) -> Optional[str]:
        """Detect if content is JavaScript or JSX."""
        # JavaScript patterns
        js_patterns = [
            'function ' in content_sample and '{' in content_sample, # function foo() { ... }
            re.search(r'\bconst\s+\w+\s*=', content_sample) is not None,
            re.search(r'\blet\s+\w+\s*=', content_sample) is not None,
            re.search(r'\bvar\s+\w+\s*=', content_sample) is not None,
            re.search(r'\bimport\s+.*\s+from\s+[\'"].*[\'"]', content_sample) is not None, # import ... from '...'
            re.search(r'\bexport\s+(default\s+)?(function|const|let|var|class)\b', content_sample) is not None,
            re.search(r'\=\>\s*\{', content_sample) is not None, # Arrow functions: () => {
            re.search(r'\.\w+\s*\(.*\)\s*;', content_sample) is not None, # Method calls ending with semicolon
            'console.log(' in content_sample,
        ]

        # JSX specific patterns (often found in React)
        jsx_patterns = [
            re.search(r'<\w+(>|\s+.*?>)[\s\S]*?</\w+>', content_sample) is not None, # Basic HTML-like tags
            re.search(r'<\w+\s+/>', content_sample) is not None, # Self-closing tags
            'React.createElement' in content_sample, # Less common now but indicative
            'render() {' in content_sample and ('return (' in content_sample or 'return <' in content_sample),
            'className=' in content_sample, # Common in JSX for CSS classes
            re.search(r'\{\s*.*\s*\}', content_sample) is not None, # JS expressions in JSX: {variable}
        ]

        # Count matches
        js_match_count = sum(1 for p in js_patterns if p)
        jsx_match_count = sum(1 for p in jsx_patterns if p)

        # If strong JSX patterns are present, classify as JSX
        if jsx_match_count > 0 and (re.search(r'<\w+', content_sample) and (re.search(r'/>', content_sample) or re.search(r'</\w+>', content_sample))):
             # Check for React import as a strong JSX indicator
            if 'import React' in content_sample or 'from "react"' in content_sample:
                return 'text/jsx'
            if jsx_match_count >=2 : # Require multiple JSX features
                 return 'text/jsx'


        # If strong JS patterns are present (and not overwhelmingly JSX)
        if js_match_count >= 2: # Require at least two JS features
            # Avoid misclassifying JSON as JS
            if (content_sample.strip().startswith('{') and content_sample.strip().endswith('}')) or \
               (content_sample.strip().startswith('[') and content_sample.strip().endswith(']')):
                try:
                    json.loads(content_sample)
                    # If it parses as JSON and has few JS specific keywords, it's likely JSON
                    if js_match_count < 2 and not any(kw in content_sample for kw in ['function', 'const', 'let', 'var', 'import', 'export']):
                        return None # Let JSON detector handle it
                except json.JSONDecodeError:
                    pass # Not JSON, proceed with JS check
            return 'text/javascript'

        # If JSX was detected but not strongly, and JS is also present, lean towards JSX if HTML tags are clear
        if jsx_match_count > 0 and js_match_count > 0:
            if re.search(r'<\w+(>|\s+.*?>)', content_sample): # Presence of opening tags
                return 'text/jsx'

        return None

    @staticmethod
    def _is_typescript(content_sample: str) -> bool:
        """Check if content is TypeScript code."""
        ts_patterns = [
            re.search(r':\s*(string|number|boolean|any|void|null|undefined)\b', content_sample) is not None, # Type annotations
            re.search(r'\binterface\s+\w+\s*\{', content_sample) is not None, # Interfaces
            re.search(r'\bclass\s+\w+\s+implements\s+\w+', content_sample) is not None, # Class implements interface
            re.search(r'\btype\s+\w+\s*=', content_sample) is not None, # Type aliases
            re.search(r'\bpublic\s+(static\s+)?\w+', content_sample) is not None, # Access modifiers
            re.search(r'\bprivate\s+(static\s+)?\w+', content_sample) is not None,
            re.search(r'\bprotected\s+(static\s+)?\w+', content_sample) is not None,
            re.search(r'\bmodule\s+\w+\s*\{', content_sample) is not None, # Modules (older syntax) or namespaces
            re.search(r'\bnamespace\s+\w+\s*\{', content_sample) is not None, # Namespaces
            re.search(r'<\w+>', content_sample) is not None, # Generics <T>
        ]
        return sum(1 for p in ts_patterns if p) >= 2 # Require at least two TS features

    @staticmethod
    def _detect_c_family(content_sample: str) -> Optional[str]:
        """Detect if content is C or C++ code."""
        # Common C family patterns (C and C++)
        c_patterns = [
            re.search(r'#include\s*<.*?>', content_sample) is not None, # #include <stdio.h>
            re.search(r'#include\s*".*?"', content_sample) is not None, # #include "myheader.h"
            re.search(r'\b(int|void|char|float|double)\s+main\s*\(.*\)\s*\{', content_sample) is not None, # main function
            re.search(r'\bstruct\s+\w+\s*\{', content_sample) is not None, # struct definition
            re.search(r'#define\s+\w+', content_sample) is not None, # #define macro
            re.search(r'\btypedef\s+.*\s+\w+;', content_sample) is not None, # typedef
            re.search(r'printf\(.*?\);', content_sample) is not None, # C-style print
            re.search(r'scanf\(.*?\);', content_sample) is not None, # C-style scan
            re.search(r'->', content_sample) is not None, # Pointer member access
            re.search(r'\bNULL\b', content_sample) is not None, # NULL pointer
        ]

        # C++ specific patterns
        cpp_patterns = [
            re.search(r'\bclass\s+\w+\s*\{', content_sample) is not None, # class definition
            re.search(r'\bnamespace\s+\w+\s*\{', content_sample) is not None, # namespace
            re.search(r'\btemplate\s*<.*?>', content_sample) is not None, # template
            re.search(r'::', content_sample) is not None, # Scope resolution operator
            re.search(r'\bstd::', content_sample) is not None, # std namespace usage (cout, cin, vector, etc.)
            re.search(r'\bcout\s*<<', content_sample) is not None, # C++ style output
            re.search(r'\bcin\s*>>', content_sample) is not None, # C++ style input
            re.search(r'\bnew\s+\w+', content_sample) is not None, # new operator
            re.search(r'\bdelete\s+\w+', content_sample) is not None, # delete operator
            re.search(r'\bvirtual\s+\w+', content_sample) is not None, # virtual keyword
            re.search(r'\boverride\b', content_sample) is not None, # override keyword
            re.search(r'#include\s*<iostream>', content_sample) is not None, # Common C++ include
        ]

        c_match_count = sum(1 for p in c_patterns if p)
        cpp_match_count = sum(1 for p in cpp_patterns if p)

        # If significant C++ patterns are found, it's C++
        if cpp_match_count >= 2 or (cpp_match_count >= 1 and 'std::' in content_sample):
            return 'text/x-c++'

        # If significant C patterns are found (and not C++), it's C
        if c_match_count >= 2:
            return 'text/x-c'

        return None
