import os
import chardet
from typing import Dict, Any, Optional
from converter.base.converter_base import BaseConverter

class TXTConverter(BaseConverter):
    """
    Converter for plain text files.
    Handles encoding detection and basic text processing.
    """

    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert a text file to another text file (potentially changing encoding or just copying).
        For now, it reads with detected encoding and writes as UTF-8.
        
        Args:
            input_path: Path to the input file.
            output_path: Path to the output file.
            **kwargs: Additional arguments (e.g., 'encoding' to force output encoding).
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.validate_input(input_path):
            return False

        self._ensure_output_directory(output_path)
        output_ext = os.path.splitext(output_path)[1].lower()

        # Detect encoding early to pass to delegates
        if 'encoding' not in kwargs:
             kwargs['encoding'] = self._detect_encoding(input_path)

        try:
            if output_ext == '.docx':
                from converter.formats.docx_writer import DOCXWriter
                return DOCXWriter().convert(input_path, output_path, **kwargs)
            
            if output_ext == '.pdf':
                from converter.formats.pdf_writer import TextToPDFConverter
                return TextToPDFConverter().convert(input_path, output_path, **kwargs)
            
            if output_ext == '.odt':
                from converter.formats.odt_writer import ODTWriter
                return ODTWriter().convert(input_path, output_path, **kwargs)

            if output_ext == '.md':
                from converter.formats.markdown_converter import MarkdownConverter
                # MarkdownConverter usually expects read from MD, but here we invoke it to write MD from TXT?
                # Actually TXT -> MD is just a copy or basic wrap. 
                # Let's check MarkdownConverter capability. 
                # MDConverter does MD->HTML or HTML->MD. It doesn't seem to have TXT->MD.
                # Standard TXT->MD is just text. 
                pass 
            
            if output_ext == '.html':
                 # TXT -> HTML
                 # We can use a simple implementation or if there is a TXT->HTML converter?
                 # Looking at code, TXTConverter handles txt->html internally if implemented?
                 # Wait, TXTConverter._convert_text handles simple text reading.
                 pass

            # Fallback to internal method
            return self._convert_text(input_path, output_path, **kwargs)
        except Exception as e:
            print(f"Error converting TXT: {e}")
            return False

    def _convert_text(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Internal method to handle basic text file conversion (read and write).
        """
        try:
            # Detect encoding
            encoding = kwargs.get('encoding', self._detect_encoding(input_path))
            
            # Read content
            with open(input_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Write content (default to utf-8)
            output_encoding = kwargs.get('output_encoding', 'utf-8') # Use 'output_encoding' if specified
            with open(output_path, 'w', encoding=output_encoding) as f:
                f.write(content)
                
            return True
        except Exception as e:
            print(f"Error converting TXT: {e}")
            return False

    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is a valid text file.
        """
        if not os.path.exists(input_path):
            return False
            
        # Simple check: try to read a bit with chardet or just check extension
        # For robustness, we could check if it's binary, but for now let's rely on extension/existence
        # and maybe a quick read attempt.
        return True

    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata from text file (lines, words, encoding).
        """
        if not os.path.exists(input_path):
            return {}

        try:
            encoding = self._detect_encoding(input_path)
            with open(input_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            return {
                "encoding": encoding,
                "lines": len(content.splitlines()),
                "words": len(content.split()),
                "characters": len(content)
            }
        except Exception:
            return {}

    def _detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding. Prioritizes UTF-8.
        """
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return 'utf-8'
        except UnicodeDecodeError:
            pass

        # Fallback to chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000) # Read first 10KB
        
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'
