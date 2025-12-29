import os
import mimetypes
from typing import Optional, Dict

try:
    import magic
except ImportError:
    magic = None

class FormatDetector:
    """
    Detects the format of a file using magic bytes (MIME type) and file extension.
    """
    
    # Mapping of MIME types to internal format identifiers
    MIME_TO_FORMAT: Dict[str, str] = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'doc',
        'text/plain': 'txt',
        'text/markdown': 'md',
        'text/html': 'html',
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/tiff': 'tiff',
        'application/json': 'json',
        'application/xml': 'xml',
        'text/xml': 'xml',
    }

    def detect(self, file_path: str) -> Optional[str]:
        """
        Detect the format of the file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Format identifier (e.g., 'pdf', 'docx') or None if detection fails.
        """
        if not os.path.exists(file_path):
            return None

        # Try detection by magic bytes first
        format_by_magic = self._detect_by_magic(file_path)
        if format_by_magic:
            return format_by_magic

        # Fallback to extension
        return self._detect_by_extension(file_path)

    def _detect_by_magic(self, file_path: str) -> Optional[str]:
        """
        Detect format using python-magic (libmagic).
        """
        if magic is None:
            return None

        try:
            mime = magic.Magic(mime=True)
            file_mime = mime.from_file(file_path)
            
            # Check for exact match
            if file_mime in self.MIME_TO_FORMAT:
                return self.MIME_TO_FORMAT[file_mime]
            
            # Check for partial match (e.g. text/plain; charset=utf-8)
            for mime_type, fmt in self.MIME_TO_FORMAT.items():
                if file_mime.startswith(mime_type):
                    return fmt
                    
            return None
        except ImportError:
            # libmagic not installed
            return None
        except Exception:
            return None

    def _detect_by_extension(self, file_path: str) -> Optional[str]:
        """
        Detect format using file extension.
        """
        _, ext = os.path.splitext(file_path)
        if not ext:
            return None
            
        ext = ext.lower().lstrip('.')
        
        # Simple mapping for common extensions if not covered by mimetypes or specific logic
        # Note: mimetypes module can also be used here if needed, but direct extension usage is often enough for fallback
        return ext
