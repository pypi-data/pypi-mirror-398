import logging
import os
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from converter.base.converter_base import BaseConverter

logger = logging.getLogger(__name__)

class TextToPDFConverter(BaseConverter):
    """
    Converter for generating PDF files from text.
    Uses ReportLab to create formatted PDFs.
    """

    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert text or markdown file to PDF.
        
        Args:
            input_path: Path to the input file.
            output_path: Path to the output PDF file.
            **kwargs: Additional arguments, including 'encoding'.
            
        Returns:
            True if conversion was successful, False otherwise.
        """
        try:
            if not self.validate_input(input_path):
                logger.error(f"Invalid input file: {input_path}")
                return False

            self._ensure_output_directory(output_path)
            logger.info(f"Converting {input_path} to PDF {output_path}")

            # Determine format
            ext = os.path.splitext(input_path)[1].lower()
            
            if ext == '.md':
                return self._convert_markdown(input_path, output_path, **kwargs)
            elif ext == '.html':
                return self._convert_html(input_path, output_path, **kwargs)
            else:
                return self._convert_text(input_path, output_path, **kwargs)

        except Exception as e:
            logger.error(f"Error converting to PDF: {e}")
            return False

    def _convert_text(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert plain text to PDF."""
        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                text = f.read()
        except UnicodeDecodeError:
            # Fallback if provided encoding fails
            logger.warning(f"Failed to read with {encoding}, falling back to utf-8")
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )

        styles = getSampleStyleSheet()
        flowables = []
        paragraphs = text.split('\n\n')
        
        for para_text in paragraphs:
            if para_text.strip():
                clean_text = para_text.replace('\n', ' ').strip()
                p = Paragraph(clean_text, styles["Normal"])
                flowables.append(p)
                flowables.append(Spacer(1, 12))

        doc.build(flowables)
        return True

    def _convert_html(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert HTML file to PDF."""
        encoding = kwargs.get('encoding', 'utf-8')
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                html_text = f.read()
            return self._convert_html_content(html_text, output_path)
        except Exception as e:
            logger.error(f"Error reading HTML file: {e}")
            return False

    def _convert_markdown(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert Markdown to PDF preserving formatting."""
        try:
            import markdown
        except ImportError:
            logger.error("Markdown not installed.")
            return False

        try:
            encoding = kwargs.get('encoding', 'utf-8')
            with open(input_path, 'r', encoding=encoding) as f:
                md_text = f.read()
            html = markdown.markdown(md_text)
            return self._convert_html_content(html, output_path)
        except Exception as e:
            logger.error(f"Error converting MD to PDF: {e}")
            return False

    def _convert_html_content(self, html_text: str, output_path: str) -> bool:
        """Shared logic to convert HTML string to PDF."""
        try:
            from bs4 import BeautifulSoup
            # ListFlowable, ListItem already imported at module level in most cases, 
            # but checking just in case or relying on file imports
            from reportlab.platypus import ListFlowable, ListItem
        except ImportError:
            logger.error("BeautifulSoup not installed.")
            return False

        soup = BeautifulSoup(html_text, 'html.parser')

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )

        styles = getSampleStyleSheet()
        flowables = []

        # Use body if available, otherwise soup
        root = soup.body if soup.body else soup

        # Map HTML tags to ReportLab styles
        for element in root.find_all(recursive=False):
            if element.name == 'h1':
                flowables.append(Paragraph(element.get_text(), styles['Heading1']))
                flowables.append(Spacer(1, 12))
            elif element.name == 'h2':
                flowables.append(Paragraph(element.get_text(), styles['Heading2']))
                flowables.append(Spacer(1, 10))
            elif element.name == 'h3':
                flowables.append(Paragraph(element.get_text(), styles['Heading3']))
                flowables.append(Spacer(1, 8))
            elif element.name == 'p':
                # Recursive processing for mixed content
                p_text = self._process_node_for_pdf(element)
                if p_text:
                    flowables.append(Paragraph(p_text, styles['Normal']))
                    flowables.append(Spacer(1, 12))
            
            elif element.name == 'ul':
                items = []
                for li in element.find_all('li', recursive=False):
                    text = self._process_node_for_pdf(li)
                    items.append(ListItem(Paragraph(text, styles['Normal'])))
                flowables.append(ListFlowable(items, bulletType='bullet', start='circle'))
                flowables.append(Spacer(1, 12))
            elif element.name == 'ol':
                items = []
                for li in element.find_all('li', recursive=False):
                    text = self._process_node_for_pdf(li)
                    items.append(ListItem(Paragraph(text, styles['Normal'])))
                flowables.append(ListFlowable(items, bulletType='1'))
                flowables.append(Spacer(1, 12))
            
            elif element.name == 'img':
                src = element.get('src')
                if src and os.path.exists(src):
                    try:
                        # ReportLab Image
                        # Use a max width to prevent overflow
                        img = Image(src)
                        
                        # Resize logic: constrain width to page width (approx 6 inches = 432 pts)
                        max_width = 450
                        if img.drawWidth > max_width:
                            ratio = max_width / img.drawWidth
                            img.drawWidth = max_width
                            img.drawHeight = img.drawHeight * ratio
                            
                        flowables.append(img)
                        flowables.append(Spacer(1, 12))
                    except Exception as e:
                        logger.warning(f"Failed to embedded image {src} in PDF: {e}")
                        flowables.append(Paragraph(f"[Image: {os.path.basename(src)}]", styles['Normal']))
                        flowables.append(Spacer(1, 12))

        doc.build(flowables)
        return True

    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is a valid text file.
        """
        if not os.path.exists(input_path):
            return False
        
        # Simple check for extension or readability
        # Simple check for extension or readability
        return input_path.lower().endswith(('.txt', '.md', '.html'))

    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata from text file (basic stats).
        """
        try:
            stats = os.stat(input_path)
            return {
                'size': stats.st_size,
                'created': stats.st_ctime,
                'modified': stats.st_mtime
            }
        except Exception:
            return {}

    def _process_node_for_pdf(self, node) -> str:
        """
        Recursively convert HTML node to ReportLab XML string.
        Handles b, i, span style=color.
        """
        if not node.name:
            import html
            return html.escape(str(node))
            
        text_content = ""
        for child in node.contents:
            text_content += self._process_node_for_pdf(child)
            
        if node.name in ['b', 'strong']:
            return f"<b>{text_content}</b>"
        if node.name in ['i', 'em']:
            return f"<i>{text_content}</i>"
        if node.name == 'span' and node.has_attr('style'):
            style = node['style']
            color_hex = None
            
            # Simple style parse
            for part in style.split(';'):
                if 'color' in part:
                    try:
                        val = part.split(':')[1].strip()
                        from converter.processors.style_processor import StyleProcessor
                        processor = StyleProcessor()
                        rgb = processor.css_to_rgb(val)
                        if rgb:
                            # Hex format #RRGGBB required for ReportLab <font color>
                            color_hex = '#{:02x}{:02x}{:02x}'.format(*rgb)
                    except (ImportError, Exception):
                        pass
            
            if color_hex:
                return f'<font color="{color_hex}">{text_content}</font>'
                
        return text_content
