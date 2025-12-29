import os
import logging
from typing import Dict, Any, Optional

try:
    import markdown
except ImportError:
    markdown = None

try:
    import html2text
except ImportError:
    html2text = None

from converter.base.converter_base import BaseConverter

logger = logging.getLogger(__name__)

class MarkdownConverter(BaseConverter):
    """
    Converter for Markdown and HTML files.
    Supports MD -> HTML and HTML -> MD.
    """

    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert MD to HTML or HTML to MD based on file extensions.
        
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

        input_ext = os.path.splitext(input_path)[1].lower()
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
                return self._convert_md_to_txt(input_path, output_path, **kwargs)

            if input_ext in ['.md', '.markdown'] and output_ext in ['.html', '.htm']:
                return self._convert_md_to_html(input_path, output_path, **kwargs)
            elif input_ext in ['.html', '.htm'] and output_ext in ['.md', '.markdown']:
                return self._convert_html_to_md(input_path, output_path, **kwargs)
            else:
                logger.error(f"Unsupported conversion direction: {input_ext} -> {output_ext}")
                return False
        except Exception as e:
            logger.error(f"Error converting Markdown/HTML: {e}")
            return False

    def _convert_md_to_html(self, input_path: str, output_path: str, **kwargs) -> bool:
        if not markdown:
            logger.error("markdown library not installed.")
            return False

        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()

        html = markdown.markdown(
            text,
            extensions=['tables', 'fenced_code', 'codehilite']
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return True

    def _convert_html_to_md(self, input_path: str, output_path: str, **kwargs) -> bool:
        if not html2text:
            logger.error("html2text library not installed.")
            return False

        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                html = f.read()
        except UnicodeDecodeError:
            encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                html = f.read()
        except UnicodeDecodeError:
            with open(input_path, 'r', encoding='utf-8') as f:
                html = f.read()

        h = html2text.HTML2Text()
        h.ignore_links = False
        text = h.handle(html)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return True

    def _convert_md_to_txt(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert Markdown to plain text (stripping formatting)."""
        if not markdown:
            logger.error("markdown library not installed.")
            return False
            
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("beautifulsoup4 library not installed.")
            return False

        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()

        # Convert to HTML then strip tags
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, 'html.parser')
        plain_text = soup.get_text(separator='\n')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(plain_text)
        
        return True

    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is a valid MD or HTML file.
        """
        if not os.path.exists(input_path):
            return False
            
        ext = os.path.splitext(input_path)[1].lower()
        return ext in ['.md', '.markdown', '.html', '.htm']

    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata from MD/HTML file.
        """
        if not os.path.exists(input_path):
            return {}

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return {
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except Exception:
            return {}
