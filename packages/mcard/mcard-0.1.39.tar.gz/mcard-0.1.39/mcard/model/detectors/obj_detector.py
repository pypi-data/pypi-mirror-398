"""3D OBJ content type detector."""
from typing import List, Optional
from .base_detector import BaseDetector

class OBJDetector(BaseDetector):
    """Detects Wavefront OBJ (3D object) file content."""

    # Common OBJ file commands
    OBJ_COMMANDS = [
        'v ', 'vt ', 'vn ', 'f ', 'g ', 'o ', 's ', 'mtllib ', 'usemtl '
    ]

    def get_mime_type(self, content_sample: str, lines: List[str], first_line: str, file_extension: Optional[str] = None) -> str:
        """Return the MIME type if content is detected as OBJ."""
        if self.detect(content_sample, lines, first_line, file_extension) > 0.5:
            return 'application/3d-obj'
        return 'text/plain'

    @property
    def content_type_name(self) -> str:
        """Return the detector name."""
        return "obj"

    def detect(self, content_sample: str, lines: List[str], first_line: str, file_extension: Optional[str] = None) -> float:
        """
        Detect if content is Wavefront OBJ format.
        
        Returns a confidence score between 0.0 and 1.0.
        """
        # If file extension is .obj, increase confidence
        if file_extension and file_extension.lower() == '.obj':
            # Still verify content
            if self._verify_obj_structure(lines):
                return 0.95
            return 0.6  # Extension matches but content doesn't look like valid OBJ

        # For non-obj extensions, be very cautious
        if file_extension and file_extension.lower() not in ["", ".obj", ".txt"]:
            return 0.0  # Don't try to detect OBJ in files with other known extensions

        # Check if content has typical Python or code markers that would rule out OBJ format
        if any(marker in content_sample.lower()[:1000] for marker in [
            "def ", "class ", "import ", "from ", "print(", "if ", "for ", "while ", 
            "function ", "var ", "let ", "const ", "#include", "package "]):
            return 0.0  # Looks like code, not OBJ

        # No extension hint, check content but be more strict
        score = self._analyze_obj_content(lines)

        # Only return a positive score for very confident matches without extension
        if score < 0.7 and (not file_extension or file_extension.lower() != '.obj'):
            return 0.0

        return score

    def _verify_obj_structure(self, lines: List[str]) -> bool:
        """Check if content has valid OBJ structure."""
        if not lines:
            return False

        # Skip empty lines and comments
        valid_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        if not valid_lines:
            return False

        # Check for OBJ command presence
        command_count = 0
        for line in valid_lines[:20]:  # Check first 20 non-empty lines
            for cmd in self.OBJ_COMMANDS:
                if line.strip().startswith(cmd):
                    command_count += 1
                    break

        # For simple OBJ files: Need at least 2 commands to be an OBJ file
        # This will detect simple triangles with just vertices and faces
        return command_count >= 2

    def _analyze_obj_content(self, lines: List[str]) -> float:
        """Analyze content to determine if it's OBJ format."""
        if not lines:
            return 0.0

        # Strip empty lines and comments
        valid_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        if not valid_lines:
            return 0.0

        # Count OBJ commands
        command_counts = {cmd: 0 for cmd in self.OBJ_COMMANDS}
        total_lines = min(len(valid_lines), 50)  # Only check first 50 non-empty lines

        for line in valid_lines[:total_lines]:
            line_stripped = line.strip()
            for cmd in self.OBJ_COMMANDS:
                if line_stripped.startswith(cmd):
                    command_counts[cmd] += 1
                    break

        # Calculate how many distinct commands are present
        distinct_commands = sum(1 for count in command_counts.values() if count > 0)

        # Calculate percentage of lines that contain OBJ commands
        command_lines = sum(command_counts.values())
        command_ratio = command_lines / total_lines if total_lines > 0 else 0

        # Calculate confidence based on command presence and distribution
        if distinct_commands >= 4 and command_ratio > 0.8:
            # High confidence - multiple commands and most lines are OBJ commands
            return 0.9
        elif distinct_commands >= 3 and command_ratio > 0.6:
            return 0.8
        elif distinct_commands >= 2 and command_ratio > 0.5:
            return 0.7
        elif distinct_commands >= 2 and command_ratio > 0.3:
            return 0.6
        elif distinct_commands >= 1 and command_ratio > 0.3:
            return 0.5

        # Check for vertex and face definitions
        has_vertices = any(line.startswith('v ') for line in valid_lines)
        has_faces = any(line.startswith('f ') for line in valid_lines)

        if has_vertices and has_faces:
            return 0.85  # Basic OBJ structure - vertices and faces are the core OBJ components
        elif has_vertices:
            return 0.4  # Some OBJ structure

        return 0.0  # Not OBJ content
