import os
import time
from typing import Any, Dict, Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

try:
    from PIL import Image
except ImportError:
    Image = None

class MetadataExtractor:
    """
    Extracts metadata from files. Supports general file info and format-specific metadata.
    """

    def extract(self, file_path: str, format: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract metadata from the file.
        
        Args:
            file_path: Path to the file.
            format: Optional format identifier to guide specific extraction.
            
        Returns:
            Dictionary containing metadata.
        """
        if not os.path.exists(file_path):
            return {}

        metadata = self._get_general_metadata(file_path)

        if format == 'pdf':
            metadata.update(self._get_pdf_metadata(file_path))
        elif format == 'docx':
            metadata.update(self._get_docx_metadata(file_path))
        elif format in ['jpg', 'jpeg', 'png', 'tiff']:
            metadata.update(self._get_image_metadata(file_path))

        return metadata

    def _get_general_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get general file metadata (size, dates)."""
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
        }

    def _get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get PDF specific metadata."""
        if PyPDF2 is None:
            return {"error": "PyPDF2 not installed"}
            
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                info = reader.metadata
                return {
                    "pages": len(reader.pages),
                    "title": info.title if info else None,
                    "author": info.author if info else None,
                }
        except Exception as e:
            return {"error": str(e)}

    def _get_docx_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get DOCX specific metadata."""
        if docx is None:
            return {"error": "python-docx not installed"}

        try:
            doc = docx.Document(file_path)
            core_props = doc.core_properties
            return {
                "title": core_props.title,
                "author": core_props.author,
                "created": core_props.created,
                "modified": core_props.modified,
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get Image specific metadata."""
        if Image is None:
            return {"error": "Pillow not installed"}

        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                }
        except Exception as e:
            return {"error": str(e)}
