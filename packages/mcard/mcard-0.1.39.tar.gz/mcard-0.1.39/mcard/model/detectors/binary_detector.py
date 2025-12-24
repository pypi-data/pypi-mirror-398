"""
Binary signature detection module.
"""
from typing import Dict

from .base_detector import BaseDetector

class BinarySignatureDetector(BaseDetector):
    """Detect file types using binary signatures."""

    # Dictionary of binary signatures mapped to MIME types
    SIGNATURES: Dict[bytes, str] = {
        # Images
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'BM': 'image/bmp',
        b'\x00\x00\x01\x00': 'image/x-icon',
        b'\x00\x00\x02\x00': 'image/x-icon',
        # WebP signature handled separately (via RIFF)
        # b'WEBP': 'image/webp', # This was a direct signature, but RIFF handles it

        # MP4 signatures
        b'\x00\x00\x00\x18ftypmp42': 'video/mp4',
        b'\x00\x00\x00\x18ftypisom': 'video/mp4',
        b'\x00\x00\x00\x14ftypmp42': 'video/mp4',
        b'\x00\x00\x00\x14ftypisom': 'video/mp4',
        b'\x00\x00\x00\x18ftypMSNV': 'video/mp4',
        b'\x00\x00\x00\x18ftypavc1': 'video/mp4',
        b'\x00\x00\x00\x18ftyp3gp5': 'video/mp4',

        # Documents
        b'%PDF': 'application/pdf',
        # For MS Office, PK\x03\x04 is ZIP, so specific checks are needed for DOCX, XLSX, PPTX
        # The b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' is for older OLE formats (DOC, XLS, PPT)
        b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': 'application/oleobject', # Generic OLE, further checks needed
        # Specific OpenXML signatures are more complex and often rely on ZIP structure inspection.
        # For simplicity, we rely on PK\x03\x04 for zip and then higher-level logic might inspect zip contents.
        # However, some direct signatures for OpenXML formats can be added if they are reliable enough.
        # b'PK\x03\x04\x14\x00\x06\x00': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX - This is too generic (ZIP)
        # b'PK\x03\x04\x14\x00\x08\x00': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # XLSX - Too generic
        # b'PK\x03\x04\x14\x00\x06\x00': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # PPTX - Too generic

        # Archives
        b'PK\x03\x04': 'application/zip', # General ZIP, could be DOCX, XLSX, etc.
        b'\x1f\x8b\x08': 'application/gzip',
        b'Rar!\x1a\x07\x00': 'application/x-rar-compressed',
        b'7z\xbc\xaf\x27\x1c': 'application/x-7z-compressed',

        # Database
        b'SQLite format 3\x00': 'application/x-sqlite3',

        # Other
        b'AT&TFORM': 'image/djvu',  # DjVu
        b'PAR1': 'application/x-parquet',  # Parquet files
    }

    # Signatures for OLE compound files (DOC, XLS, PPT)
    OLE_SIGNATURE = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    # Signatures for OpenXML (DOCX, XLSX, PPTX) - these are ZIP files
    # A more robust check involves inspecting the ZIP file contents for specific XML parts.
    # For now, we'll rely on higher-level logic or mimetypes for these if 'application/zip' is detected.
    # However, we can add some common ZIP-based signatures if they are distinct enough.
    # Example: b'PK\x03\x04' followed by specific bytes for certain OpenXML types, but this is fragile.

    @property
    def content_type_name(self) -> str:
        return "binary"

    def detect(self, content_sample, lines, first_line, file_extension=None):
        # Use a simple heuristic: if we detect a known binary type, return high confidence
        mime = self.get_mime_type(content_sample, lines, first_line, file_extension)
        if mime and mime != 'application/octet-stream':
            return 0.95
        return 0.0

    def get_mime_type(self, content_sample, lines, first_line, file_extension=None):
        # Establish content bytes
        try:
            # If it's already bytes, use it directly
            if isinstance(content_sample, bytes):
                content_bytes = content_sample
            else:
                content_bytes = content_sample.encode('utf-8', errors='replace')
        except Exception:
             # Fallback for any encoding issues
            content_bytes = str(content_sample).encode('utf-8', errors='replace')

        # Use the core byte detection logic
        detected_mime = self.detect_from_bytes(content_bytes)
        
        # If specific type found, return it
        if detected_mime != 'application/octet-stream':
            return detected_mime
            
        # Fallback: Check for XML-like content if binary signature didn't match
        # (This handles text-based XML that might have been passed as bytes)
        if content_bytes.startswith(b'<?xml') or content_bytes.lstrip(b' \t\n\r').startswith(b'<'):
            # Use XMLDetector to determine subtype
            from .markup_detectors import XMLDetector
            return XMLDetector().get_mime_type(content_sample, lines, first_line, file_extension)
            
        return 'application/octet-stream'


    def detect_from_bytes(self, content_bytes: bytes) -> str:
        """Detect MIME type directly from bytes, bypassing text-based processing."""
        # Handle RIFF container formats (WAV and WebP)
        if content_bytes.startswith(b'RIFF'):
            return self._detect_riff_format(content_bytes)
        # Check for standard file signatures
        for signature, mime_type in self.SIGNATURES.items():
            if content_bytes.startswith(signature):
                if signature == self.OLE_SIGNATURE:
                    return 'application/oleobject'
                if signature == b'PK\x03\x04':
                    if b'[Content_Types].xml' in content_bytes[:1024] and b'_rels/.rels' in content_bytes[:1024]:
                        if b'word/' in content_bytes[:2048]:
                            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        if b'xl/' in content_bytes[:2048]:
                            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        if b'ppt/' in content_bytes[:2048]:
                            return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    return 'application/zip'
                return mime_type
        return 'application/octet-stream'

    @staticmethod
    def _detect_riff_format(content: bytes) -> str:
        """Detect specific type of RIFF container format."""
        # Both WAV and WebP require at least 12 bytes for identification
        if len(content) >= 12:  
            # Check format type at offset 8
            format_type = content[8:12]

            if format_type == b'WAVE':
                return 'audio/wav'
            elif format_type == b'WEBP':                
                return 'image/webp'

        # Unidentifiable RIFF format
        return 'application/octet-stream'
