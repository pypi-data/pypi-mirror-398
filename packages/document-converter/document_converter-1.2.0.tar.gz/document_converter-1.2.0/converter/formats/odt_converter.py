import logging
import os
from typing import Dict, Any, List
from odf.opendocument import load
from odf import text, teletype
from converter.base.converter_base import BaseConverter

logger = logging.getLogger(__name__)

class ODTConverter(BaseConverter):
    """
    Converter for ODT files.
    Extracts text from ODT files using odfpy.
    """

    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert ODT to text, markdown, or html.
        
        Args:
            input_path: Path to the input ODT file.
            output_path: Path to the output file (.txt, .md, .html).
            **kwargs: Additional arguments.
            
        Returns:
            True if conversion was successful, False otherwise.
        """
        try:
            if not self.validate_input(input_path):
                logger.error(f"Invalid input file: {input_path}")
                return False

            self._ensure_output_directory(output_path)
            
            output_ext = os.path.splitext(output_path)[1].lower()
            
            if output_ext == '.md':
                return self._convert_to_markdown(input_path, output_path)
            elif output_ext == '.html':
                return self._convert_to_html(input_path, output_path)
            elif output_ext == '.docx':
                return self._convert_to_docx(input_path, output_path, **kwargs)
            elif output_ext == '.pdf':
                return self._convert_to_pdf(input_path, output_path, **kwargs)
            else:
                return self._convert_to_text(input_path, output_path)

        except Exception as e:
            logger.error(f"Error converting ODT: {e}")
            return False

    def _convert_to_text(self, input_path: str, output_path: str) -> bool:
        """Convert ODT to plain text."""
        logger.info(f"Converting ODT {input_path} to text {output_path}")
        try:
            doc = load(input_path)
            text_content = []

            # Iterate through all text elements in order
            for element in doc.getElementsByType(text.P):
                content = teletype.extractText(element)
                if content:
                    text_content.append(content)
            
            # Also get headers
            for element in doc.getElementsByType(text.H):
                content = teletype.extractText(element)
                if content:
                    text_content.append(content)

            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write("\n\n".join(text_content))
            return True
        except Exception as e:
            logger.error(f"Failed to convert ODT to text: {e}")
            return False

    def _convert_to_markdown(self, input_path: str, output_path: str) -> bool:
        """Convert ODT to Markdown."""
        logger.info(f"Converting ODT {input_path} to Markdown {output_path}")
        try:
            doc = load(input_path)
            lines = []

            # We need to process the document body to keep order, but odfpy 
            # structure is a bit complex. For simplicity, we'll iterate over 
            # top-level text elements if possible, or just specific types.
            # A more robust approach iterates over the body's children.
            
            body = doc.text
            for element in body.childNodes:
                if element.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'p'):
                    content = teletype.extractText(element)
                    if content.strip():
                        lines.append(content)
                elif element.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'h'):
                    content = teletype.extractText(element)
                    level = int(element.getAttribute('outlinelevel') or 1)
                    if content.strip():
                        lines.append(f"{'#' * level} {content}")
                elif element.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'list'):
                    self._process_list_markdown(element, lines)
                
            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write("\n\n".join(lines))
            return True
        except Exception as e:
            logger.error(f"Failed to convert ODT to Markdown: {e}")
            return False

    def _process_list_markdown(self, list_element, lines: List[str], level=0):
        """Helper to process lists for Markdown."""
        for item in list_element.childNodes:
            if item.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'list-item'):
                # Extract text from the list item
                item_text = ""
                for child in item.childNodes:
                    if child.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'p'):
                        item_text += teletype.extractText(child) + " "
                    elif child.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'list'):
                        # Nested list
                        if item_text.strip():
                            lines.append(f"{'  ' * level}- {item_text.strip()}")
                            item_text = ""
                        self._process_list_markdown(child, lines, level + 1)
                
                if item_text.strip():
                    lines.append(f"{'  ' * level}- {item_text.strip()}")

    def _convert_to_html(self, input_path: str, output_path: str) -> bool:
        """Convert ODT to HTML."""
        logger.info(f"Converting ODT {input_path} to HTML {output_path}")
        try:
            doc = load(input_path)
            html_parts = ['<html><body>']

            body = doc.text
            for element in body.childNodes:
                if element.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'p'):
                    content = teletype.extractText(element)
                    if content.strip():
                        html_parts.append(f"<p>{content}</p>")
                elif element.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'h'):
                    content = teletype.extractText(element)
                    level = int(element.getAttribute('outlinelevel') or 1)
                    if content.strip():
                        html_parts.append(f"<h{level}>{content}</h{level}>")
                elif element.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'list'):
                    self._process_list_html(element, html_parts)

            html_parts.append('</body></html>')

            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write("\n".join(html_parts))
            return True
        except Exception as e:
            logger.error(f"Failed to convert ODT to HTML: {e}")
            return False

    def _process_list_html(self, list_element, html_parts: List[str]):
        """Helper to process lists for HTML."""
        html_parts.append("<ul>")
        for item in list_element.childNodes:
            if item.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'list-item'):
                html_parts.append("<li>")
                for child in item.childNodes:
                    if child.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'p'):
                        html_parts.append(teletype.extractText(child))
                    elif child.qname == ('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'list'):
                        self._process_list_html(child, html_parts)
                html_parts.append("</li>")
        html_parts.append("</ul>")

    def _convert_to_docx(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert ODT to DOCX via intermediate HTML."""
        import tempfile
        
        # 1. Convert ODT to temp HTML
        fd, temp_html_path = tempfile.mkstemp(suffix='.html')
        os.close(fd)
        
        try:
            if not self._convert_to_html(input_path, temp_html_path):
                logger.error("Intermediate ODT->HTML conversion failed for DOCX output.")
                return False
                
            # 2. Convert HTML to DOCX using DOCXWriter
            from converter.formats.docx_writer import DOCXWriter
            return DOCXWriter().convert(temp_html_path, output_path, **kwargs)
            
        finally:
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)

    def _convert_to_pdf(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert ODT to PDF via intermediate HTML."""
        import tempfile
        
        # 1. Convert ODT to temp HTML
        fd, temp_html_path = tempfile.mkstemp(suffix='.html')
        os.close(fd)
        
        try:
            if not self._convert_to_html(input_path, temp_html_path):
                logger.error("Intermediate ODT->HTML conversion failed for PDF output.")
                return False
                
            # 2. Convert HTML to PDF using TextToPDFConverter
            from converter.formats.pdf_writer import TextToPDFConverter
            # TextToPDFConverter can now read HTML files thanks to previous fixes
            return TextToPDFConverter().convert(temp_html_path, output_path, **kwargs)
            
        finally:
            if os.path.exists(temp_html_path):
                try:
                    os.unlink(temp_html_path)
                except:
                    pass

    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is a valid ODT.
        """
        if not os.path.exists(input_path):
            return False
            
        if not input_path.lower().endswith('.odt'):
            return False

        try:
            # Try opening it
            load(input_path)
            return True
        except Exception:
            return False

    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata from ODT.
        """
        metadata = {}
        try:
            doc = load(input_path)
            # odfpy metadata handling might vary, checking common attributes
            # This is a placeholder as odfpy metadata access is specific
            # We can access doc.meta if available or iterate over meta.xml content
            
            # Simple extraction if possible, otherwise leave empty for now
            # or implement specific meta extraction logic
            pass
            
        except Exception as e:
            logger.warning(f"Could not extract metadata from {input_path}: {e}")
            
        return metadata
