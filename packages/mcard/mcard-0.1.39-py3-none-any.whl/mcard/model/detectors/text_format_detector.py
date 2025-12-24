"""
Text format detection module (JSON, CSV, Markdown, YAML, Mermaid, TeX, OBJ).
"""
import re
import json
from typing import List

from .base_detector import BaseDetector  # Add this import


class TextFormatDetector(BaseDetector):
    """Detect various text-based file formats."""

    @property
    def content_type_name(self) -> str:
        return "text"

    def detect(self, content_sample: str, lines: List[str], first_line: str, file_extension: str = None) -> float:
        # Use get_mime_type for detection and assign confidence based on type
        mime = self.get_mime_type(content_sample, lines, first_line, file_extension)
        if mime and mime != 'text/plain':
            return 0.9
        return 0.0

    def get_mime_type(self, content_sample: str, lines: List[str], first_line: str, file_extension: str = None) -> str:
        # Use the previous detection logic
        text_content = content_sample
        text_content_stripped = text_content.strip()
        if not text_content_stripped:
            return 'text/plain'
        lines = text_content.split('\n')
        # JSON detection
        if TextFormatDetector._is_json(text_content_stripped, lines):
            return 'application/json'
        if text_content_stripped.startswith('<'):
            from .markup_detectors import XMLDetector
            xml_type = XMLDetector().get_mime_type(text_content_stripped, lines, lines[0] if lines else '', file_extension)
            if xml_type != 'text/plain':
                return xml_type
        if lines and hasattr(__import__('mcard.model.detectors.language_detector', fromlist=['ProgrammingLanguageDetector']), 'ProgrammingLanguageDetector'):
            ProgrammingLanguageDetector = __import__('mcard.model.detectors.language_detector', fromlist=['ProgrammingLanguageDetector']).ProgrammingLanguageDetector
            if ProgrammingLanguageDetector._is_python(lines[0].strip() if lines else '', text_content, lines):
                return 'text/x-python'
        if TextFormatDetector._is_markdown(text_content, lines):
            return 'text/markdown'
        if TextFormatDetector._is_yaml(text_content, lines):
            return 'application/x-yaml'
        if TextFormatDetector._is_csv(lines):
            return 'text/csv'
        if TextFormatDetector._is_mermaid(text_content):
            return 'text/x-mermaid'
        if TextFormatDetector._is_tex(text_content, lines):
            return 'application/x-tex'
        if TextFormatDetector._is_obj_3d(text_content_stripped, lines):
            return 'application/3d-obj'
        return 'text/plain'

        """Detect text format from content."""
        # Prepare content for analysis
        text_content_stripped = text_content.strip()
        if not text_content_stripped: # Handle empty or whitespace-only content
            return 'text/plain'

        lines = text_content.split('\n') # Use original text_content for splitting lines

        # Detection priority order based on reliability and clear markers

        # 1. First check formats with definitive signatures or structures

        # JSON detection - has a strict format making it highly reliable
        if TextFormatDetector._is_json(text_content_stripped, lines):
            return 'application/json'

        # XML-based formats detection (XML, HTML, SVG) are handled by XMLDetector
        # This is called before general text format detection in ContentTypeInterpreter
        # However, if called directly, XMLDetector should be used.
        # For this class, we assume XMLDetector has already been tried if applicable.
        # If text_content starts with '<', it's likely XML-based.
        if text_content_stripped.startswith('<'):
            xml_type = XMLDetector.detect_from_string(text_content_stripped) # Use stripped content
            if xml_type != 'text/plain':  # If any XML format was detected
                return xml_type

        # 2. Check for programming languages with strong markers (e.g., Python)
        # This helps differentiate code files from YAML/Markdown if there's ambiguity.
        # We use a limited check here; full language detection is separate.
        # Python detection - specifically to avoid misidentifying Python as YAML/Markdown.
        # Use ProgrammingLanguageDetector for a more robust check if needed,
        # but a quick check here can help with ordering.
        # For now, rely on ProgrammingLanguageDetector being called by ContentTypeInterpreter.
        # If _is_python is called, it should be from ProgrammingLanguageDetector.
        # Let's assume ContentTypeInterpreter calls ProgrammingLanguageDetector.detect if needed.
        # However, the original logic had a Python check here.
        if ProgrammingLanguageDetector._is_python(lines[0].strip() if lines else '', text_content, lines): # Use full text_content for _is_python
            return 'text/x-python' # This might be redundant if ProgLangDetector is called first by orchestrator

        # 3. Check for markup languages and structured text formats

        # Markdown detection
        if TextFormatDetector._is_markdown(text_content, lines): # Use full text_content
            return 'text/markdown'

        # YAML detection - after Python to avoid misidentifying Python as YAML
        if TextFormatDetector._is_yaml(text_content, lines): # Use full text_content
            return 'application/x-yaml'

        # 4. Then check for other formats

        # CSV detection
        if TextFormatDetector._is_csv(lines):
            return 'text/csv'

        # Mermaid diagram detection
        if TextFormatDetector._is_mermaid(text_content): # Use full text_content
            return 'text/x-mermaid'

        # TeX document detection
        if TextFormatDetector._is_tex(text_content, lines): # Use full text_content
            return 'application/x-tex'

        # OBJ 3D model format
        if TextFormatDetector._is_obj_3d(text_content_stripped, lines): # Use stripped for startswith check
            return 'application/3d-obj'

        # Default to plain text if no other format is detected
        return 'text/plain'

    @staticmethod
    def _is_json(text_content: str, lines: List[str]) -> bool:
        """Check if content is JSON."""
        # Basic structural check
        if not ((text_content.startswith('{') and text_content.endswith('}')) or \
                (text_content.startswith('[') and text_content.endswith(']'))):
            return False

        # Reject content with JavaScript/C-style comments, as pure JSON doesn't allow them.
        # This check needs to be careful not to misinterpret strings containing "//" or "/*".
        # A simple line check is a heuristic.
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('//') or stripped_line.startswith('/*'):
                # Further check if it's inside a string
                # This is complex; for now, a simple check. A robust parser would be better.
                # If we find comments not inside strings, it's not pure JSON.
                # This heuristic might be too aggressive.
                # Consider removing if it causes false negatives for JSON with embedded strings.
                # json.loads will fail anyway if comments are not valid.
                pass # Let json.loads handle comment validation

        try:
            json.loads(text_content)
            return True
        except json.JSONDecodeError:
            return False

    # _is_html is better handled by XMLDetector.is_html_content
    # @staticmethod
    # def _is_html(text_content: str) -> bool: ...

    @staticmethod
    def _is_csv(lines: List[str]) -> bool:
        """Check if content is CSV."""
        if not lines or len(lines) == 0:
            return False

        # Heuristic: Check first few lines for consistent comma delimiters
        sample_lines = [line for line in lines[:10] if line.strip()] # Take up to 10 non-empty lines
        if not sample_lines or len(sample_lines) < 1: # Need at least one line to check
            return False

        # All sample lines must contain at least one comma
        if not all(',' in line for line in sample_lines):
            return False

        # Check for consistent comma count (or header having different count)
        comma_counts = [line.count(',') for line in sample_lines]

        if not comma_counts:
            return False

        # If all lines have the same number of commas (and > 0)
        if len(set(comma_counts)) == 1 and comma_counts[0] > 0:
            return True

        # Allow for a header row with a different number of commas than data rows
        # if len(sample_lines) > 1:
        #     header_commas = comma_counts[0]
        #     data_commas_set = set(comma_counts[1:])
        #     if len(data_commas_set) == 1 and list(data_commas_set)[0] > 0:
        #         # Header can be different, or all same
        #         return True

        # A simpler check: if average number of commas is high and consistent
        # This is tricky. The original check was:
        # (comma_counts and all(count > 0 for count in comma_counts) and max(comma_counts) - min(comma_counts) <= 1)
        # This allows for slight variations, which might be too loose or too strict.
        # Let's stick to a more conservative check: at least N lines have same >0 comma count.

        if len(sample_lines) >= 3: # Require at least 3 sample lines for this heuristic
            counts_dict = {}
            for c in comma_counts:
                if c > 0: # Only consider lines with commas
                    counts_dict[c] = counts_dict.get(c, 0) + 1

            # If a significant number of lines share the same comma count
            for count_val, num_lines_with_count in counts_dict.items():
                if num_lines_with_count >= len(sample_lines) * 0.6 and num_lines_with_count >=2 : # e.g., 60% of lines, and at least 2 lines
                    return True
        elif len(sample_lines) > 0 and all(c > 0 for c in comma_counts) and len(set(comma_counts)) == 1:
            # For 1 or 2 lines, they must have same comma count > 0
            return True

        return False

    @staticmethod
    def _is_markdown(text_content: str, lines: List[str]) -> bool:
        """Check if content is Markdown."""
        # Common Markdown patterns (regex strings)
        markdown_regex_list = [
            r"^#{1,6}\s+\S+",             # ATX Headers
            r"^\s*[\*\+\-]\s+\S+",        # List items (unordered)
            r"^\s*\d+\.\s+\S+",           # Ordered list items
            r"`{1,3}[^`]+`{1,3}",         # Inline code
            r"\[[^\]]+\]\([^\)]+\)",      # Links [text](url)
            r"!\[[^\]]+\]\([^\)]+\)",     # Images ![alt](url)
            r"^\s*>.*"                    # Blockquotes
        ]

        # Check for Setext headers (e.g., Title\n==== or Title\n----)
        # This is a strong indicator and should be checked early.
        if re.search(r"^.*\n(?:={3,}|-{3,})\s*$", text_content, re.MULTILINE):
            return True

        feature_count = 0
        for pattern in markdown_regex_list:
            # Search in the whole content for multi-line patterns.
            if re.search(pattern, text_content, re.MULTILINE):
                feature_count += 1

        # Check for bold formatting (inspired by one of the mis-indented lines)
        if re.search(r'\*\*.+?\*\*|__.+?__', text_content): # Bold
            feature_count += 1

        # Check for italic formatting (more specific to avoid false positives)
        # Looks for word boundaries around single asterisks/underscores.
        if re.search(r'(?<!\w)\*(?!\s|\*).+?(?<!\s|\*)\*(?!\w)|(?<!\w)_(?!\s|_).+?(?<!\s|_)_(?!\w)', text_content): # Italic
             feature_count +=1

        # Heuristic: if multiple Markdown features are present
        if feature_count >= 2: # If at least 2 different types of markdown elements are found
            return True

        # Check for fenced code blocks as another strong indicator
        if "```" in text_content: 
            return True

        # If only one distinct feature was found from the list/specific checks, 
        # it might still be markdown (e.g., a file with just one # Header).
        if feature_count >= 1:
            return True

        return False

    @staticmethod
    def _is_yaml(text_content: str, lines: List[str]) -> bool:
        """Check if content is YAML, with stricter rules to avoid Python dict false positives."""
        if not lines or (text_content.startswith('{') and text_content.endswith('}')):
            return False

        # Strong indicator: starts with --- (YAML document separator)
        if lines[0].strip() == '---':
            return True

        # Heuristic: Check for key-value pairs with colons
        # and indentation, which are common in YAML.
        key_value_pairs = 0
        indentation_levels = set()
        sample_lines = [line for line in lines[:20] if line.strip() and not line.strip().startswith('#')]

        if len(sample_lines) < 2: # Not enough content to be sure
            return False

        for line in sample_lines:
            # Check for key: value format
            if ':' in line:
                key_value_pairs += 1

            # Check for indentation (must be spaces, not tabs for strict YAML)
            match = re.match(r'^(\s+)', line)
            if match:
                indentation_levels.add(len(match.group(1)))

        # Conditions for being YAML:
        # 1. A high percentage of lines are key-value pairs.
        # 2. There's some indentation present.
        is_yaml = (
            (key_value_pairs / len(sample_lines) > 0.5) and
            (len(indentation_levels) > 0 or any(line.strip().startswith('- ') for line in sample_lines))
        )

        return is_yaml

    @staticmethod
    def _is_mermaid(text_content: str) -> bool:
        """Check if content is a Mermaid diagram."""
        # Mermaid diagrams often start with graph, sequenceDiagram, gantt, etc.
        # Using a regex to check for these keywords at the start of a line.
        mermaid_keywords = [
            "graph", "flowchart", "sequenceDiagram", "gantt", "classDiagram", 
            "stateDiagram", "pie", "erDiagram", "journey"
        ]
        # A file is likely a mermaid file if it starts with one of the keywords,
        # possibly with some leading whitespace.
        pattern = r"^\s*(" + "|".join(mermaid_keywords) + r")"
        if re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE):
            return True
        return False

    @staticmethod
    def _is_tex(text_content: str, lines: List[str]) -> bool:
        """Check if content is a TeX/LaTeX document."""
        # Check for common LaTeX commands
        tex_commands = [
            r"\\documentclass",
            r"\\begin\{document\}",
            r"\\usepackage",
            r"\\section",
            r"\\chapter",
            r"\\title",
            r"\\author"
        ]

        feature_count = 0
        for command in tex_commands:
            if re.search(command, text_content):
                feature_count += 1

        # If we find at least one major command like \documentclass or \begin{document}
        if re.search(r"\\documentclass", text_content) or re.search(r"\\begin\{document\}", text_content):
            return True

        # Or if we find multiple other common commands
        if feature_count >= 2:
            return True

        # Another heuristic: a high density of backslashes and curly braces
        if len(lines) > 5: # Only for reasonably sized files
            backslash_count = text_content.count('\\')
            brace_count = text_content.count('{')
            if len(text_content) > 0 and (backslash_count + brace_count) / len(text_content) > 0.05: # 5% density
                return True

        return False

    @staticmethod
    def _is_obj_3d(text_content_stripped: str, lines: List[str]) -> bool:
        """Check if content is 3D model."""
        if not text_content_stripped.startswith('.obj'):
            return False

        # Heuristic: Check for consistent '.obj' extension
        if '.' in text_content_stripped[3:]:
            return True

        return False
