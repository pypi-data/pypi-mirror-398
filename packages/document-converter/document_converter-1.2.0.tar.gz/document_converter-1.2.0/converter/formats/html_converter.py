import os
import logging
from typing import Dict, Any, Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import html2text
except ImportError:
    html2text = None

from converter.base.converter_base import BaseConverter

logger = logging.getLogger(__name__)

class HTMLConverter(BaseConverter):
    """
    Converter for HTML files.
    Supports HTML -> TXT and HTML -> MD.
    """

    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert HTML to TXT or MD based on output extension.
        
        Args:
            input_path: Path to the input file.
            output_path: Path to the output file.
            **kwargs: Additional arguments.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.validate_input(input_path):
            return False

        self._ensure_output_directory(output_path)

        output_ext = os.path.splitext(output_path)[1].lower()

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

            if output_ext == '.txt':
                return self._convert_html_to_txt(input_path, output_path, **kwargs)
            elif output_ext in ['.md', '.markdown']:
                return self._convert_html_to_md(input_path, output_path, **kwargs)
            else:
                logger.error(f"Unsupported output format for HTML conversion: {output_ext}")
                return False
        except Exception as e:
            logger.error(f"Error converting HTML: {e}")
            return False

    def _convert_html_to_txt(self, input_path: str, output_path: str, **kwargs) -> bool:
        if not BeautifulSoup:
            logger.error("beautifulsoup4 library not installed.")
            return False

        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator='\n')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return True

    def _convert_html_to_md(self, input_path: str, output_path: str, **kwargs) -> bool:
        if not html2text:
            logger.error("html2text library not installed.")
            return False

        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        h = html2text.HTML2Text()
        h.ignore_links = False
        text = h.handle(html_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return True

    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is a valid HTML file.
        """
        if not os.path.exists(input_path):
            return False
            
        ext = os.path.splitext(input_path)[1].lower()
        return ext in ['.html', '.htm']

    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML file (title, description).
        """
        if not os.path.exists(input_path) or not BeautifulSoup:
            return {}

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else None
            
            description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content')
                
            return {
                "title": title,
                "description": description
            }
        except Exception:
            return {}
