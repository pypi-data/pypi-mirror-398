import os
import os
try:
    import magic
except ImportError:
    magic = None
import mimetypes

class FormatDetector:
    """
    Detects file format based on extension and magic bytes.
    """
    def detect_format(self, file_path: str) -> str:
        """
        Detect format of the file.
        Returns extension without dot (e.g. 'pdf', 'docx').
        """
        if not os.path.exists(file_path):
            return "unknown"
            
        # Try extension first if it matches known types
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        # Verify with magic if possible
        try:
            mime = magic.from_file(file_path, mime=True)
            # Map mime to extensions
            # This is a simplified check.
            # If mime matches extension, trust extension.
            # If extension is missing, use mime.
            
            guessed_ext = mimetypes.guess_extension(mime)
            if guessed_ext:
                guessed_ext = guessed_ext.lstrip('.')
                if guessed_ext == ext:
                    return ext
        except Exception:
            pass
            
        return ext if ext else "unknown"
