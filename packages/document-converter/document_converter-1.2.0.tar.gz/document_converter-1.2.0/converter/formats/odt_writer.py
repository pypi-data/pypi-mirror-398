import logging
import os
from typing import Dict, Any
from odf.opendocument import OpenDocumentText
from odf.text import P, H
from odf.style import Style, TextProperties
from converter.base.converter_base import BaseConverter

logger = logging.getLogger(__name__)

class ODTWriter(BaseConverter):
    """
    Converter for generating ODT files from text/markdown/html.
    Uses odfpy to create formatted documents.
    """

    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert text, markdown, or html file to ODT.
        
        Args:
            input_path: Path to the input file.
            output_path: Path to the output ODT file.
            **kwargs: Additional arguments.
            
        Returns:
            True if conversion was successful, False otherwise.
        """
        try:
            if not self.validate_input(input_path):
                logger.error(f"Invalid input file: {input_path}")
                return False

            self._ensure_output_directory(output_path)
            logger.info(f"Converting {input_path} to ODT {output_path}")

            ext = os.path.splitext(input_path)[1].lower()
            
            if ext == '.md':
                return self._convert_markdown(input_path, output_path)
            elif ext == '.html':
                return self._convert_html(input_path, output_path)
            else:
                return self._convert_text(input_path, output_path)

        except Exception as e:
            logger.error(f"Error converting to ODT: {e}")
            return False

    def _convert_text(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert plain text to ODT."""
        doc = OpenDocumentText()
        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                text = f.read()
        except UnicodeDecodeError:
             with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()

        for para in text.split('\n\n'):
            if para.strip():
                p = P()
                p.addText(para.strip())
                doc.text.addElement(p)

        doc.save(output_path)
        return True

    def _convert_markdown(self, input_path: str, output_path: str) -> bool:
        """Convert Markdown to ODT preserving basic formatting."""
        try:
            import markdown
        except ImportError:
            logger.error("Markdown not installed.")
            return False

        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                md_text = f.read()
        except UnicodeDecodeError:
             with open(input_path, 'r', encoding='utf-8') as f:
                md_text = f.read()

        html = markdown.markdown(md_text)
        return self._convert_html_content(html, output_path)

    def _convert_html(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert HTML file to ODT."""
        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                html_content = f.read()
        except UnicodeDecodeError:
             with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        return self._convert_html_content(html_content, output_path)

    def _convert_html_content(self, html_content: str, output_path: str) -> bool:
        """Shared logic to convert HTML string to ODT."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup not installed.")
            return False

        soup = BeautifulSoup(html_content, 'html.parser')
        doc = OpenDocumentText()

        # If there's a body, use it, otherwise use the whole soup
        root = soup.body if soup.body else soup

        for element in root.find_all(recursive=False):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                h = H(outlinelevel=level)
                h.addText(element.get_text())
                doc.text.addElement(h)
            
            elif element.name == 'p':
                p = P()
                self._process_inline_elements(p, element, doc)
                doc.text.addElement(p)
                
            elif element.name in ['ul', 'ol']:
                # ODT lists are more complex, for simplicity we'll just add items as paragraphs with bullets
                for li in element.find_all('li', recursive=False):
                    p = P()
                    p.addText("• " + li.get_text())
                    doc.text.addElement(p)

        doc.save(output_path)
        return True

    def _process_inline_elements(self, paragraph, element, doc):
        """Helper to process inline elements like <b>, <i> within a paragraph."""
        # For simplicity, we'll just extract text
        # Full formatting would require creating text spans with styles
        for child in element.contents:
            if hasattr(child, 'name') and child.name:
                # It's a tag - for now just extract text
                # TODO: Add proper bold/italic support with text spans
                paragraph.addText(child.get_text())
            else:
                # It's text
                paragraph.addText(str(child))

    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is a valid text/md/html file.
        """
        if not os.path.exists(input_path):
            return False
        return input_path.lower().endswith(('.txt', '.md', '.html'))

    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """Metadata extraction not applicable for writer input (it's just text)."""
        return {}
