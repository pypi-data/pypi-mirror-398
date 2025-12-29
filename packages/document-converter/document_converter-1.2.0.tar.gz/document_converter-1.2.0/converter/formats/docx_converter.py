import logging
import os
from typing import Dict, Any
from converter.base.converter_base import BaseConverter

logger = logging.getLogger(__name__)

class DOCXConverter(BaseConverter):
    """
    Converter for DOCX files.
    Extracts text from DOCX files using python-docx.
    """

    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert DOCX to text, markdown, or html.
        
        Args:
            input_path: Path to the input DOCX file.
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
            elif output_ext == '.pdf':
                return self._convert_to_pdf(input_path, output_path)
            else:
                return self._convert_to_text(input_path, output_path)

        except Exception as e:
            logger.error(f"Error converting DOCX: {e}")
            return False

    def _extract_image_from_run(self, run, output_dir):
        """Helper to extract image from a run if present."""
        try:
            # This is a basic heuristic for finding images in runs using python-docx
            # Images are distinct parts referenced by rId
            drawing = run.element.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing')
            if drawing is not None:
                # Find blip
                blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                if blip is not None:
                    embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if embed_id:
                        part = run.part.related_parts[embed_id]
                        
                        # Determine filename
                        filename = os.path.basename(part.partname)
                        image_path = os.path.join(output_dir, filename)
                        
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                            
                        with open(image_path, "wb") as f:
                            f.write(part.blob)
                        
                        return image_path
        except Exception as e:
            logger.warning(f"Failed to extract image from run: {e}")
        return None

    def _convert_to_pdf(self, input_path: str, output_path: str) -> bool:
        """Convert DOCX to PDF."""
        logger.info(f"Converting DOCX {input_path} to PDF {output_path}")
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
        except ImportError:
            logger.error("ReportLab not installed.")
            return False

        try:
            doc = docx.Document(input_path)
            
            pdf_doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72, leftMargin=72,
                topMargin=72, bottomMargin=18
            )

            styles = getSampleStyleSheet()
            flowables = []

            # Helper to map DOCX styles to ReportLab styles
            def get_style(docx_style_name):
                if docx_style_name.startswith('Heading 1'): return styles['Heading1']
                if docx_style_name.startswith('Heading 2'): return styles['Heading2']
                if docx_style_name.startswith('Heading 3'): return styles['Heading3']
                if docx_style_name.startswith('Heading'): return styles['Heading4'] # Fallback
                return styles['Normal']

            current_list_items = []
            current_list_style = None # 'Bullet' or 'Number'

            def flush_list():
                nonlocal current_list_items, current_list_style
                if current_list_items:
                    bullet_type = 'bullet' if current_list_style == 'Bullet' else '1'
                    flowables.append(ListFlowable(current_list_items, bulletType=bullet_type))
                    flowables.append(Spacer(1, 12))
                    current_list_items = []
                    current_list_style = None

            for para in doc.paragraphs:
                # We need to process runs to find images
                if not para.runs:
                    continue
                    
                style_name = para.style.name
                
                # Check for images in runs
                # Note: Splitting paragraph if image is found is complex with just flowables.
                # For simplicity, we add images before or after text segments, or reconstructing paragraph.
                # ReportLab Paragraph can take <img> tag, or we can use separate Image flowables.
                # Let's use separate Image flowables for robustness.
                
                # Accumulate text
                para_text = ""
                images_in_para = []
                
                for run in para.runs:
                    para_text += run.text
                    
                    # Check for image
                    img_path = self._extract_image_from_run(run, os.path.dirname(output_path) + "/images")
                    if img_path:
                        images_in_para.append(img_path)

                clean_text = para_text.strip()
                if not clean_text and not images_in_para:
                    continue

                if style_name.startswith('List'):
                    # List item
                    list_type = 'Bullet' if 'Bullet' in style_name else 'Number'
                    if current_list_style and current_list_style != list_type:
                        flush_list()
                    
                    current_list_style = list_type
                    current_list_items.append(ListItem(Paragraph(clean_text, styles['Normal'])))
                    # What if list item has image? Tough. Append to list item?
                    # ReportLab ListItem can take flowables. But standard usage is Paragraph.
                    # For now ignoring images in lists to avoid breakage, or append.
                else:
                    flush_list()
                    rl_style = get_style(style_name)
                    if clean_text:
                        flowables.append(Paragraph(clean_text, rl_style))
                    
                    for img_path in images_in_para:
                        try:
                            from reportlab.platypus import Image
                            img = Image(img_path)
                            # Resize
                            max_width = 450
                            if img.drawWidth > max_width:
                                ratio = max_width / img.drawWidth
                                img.drawWidth = max_width
                                img.drawHeight = img.drawHeight * ratio
                            flowables.append(img)
                            flowables.append(Spacer(1, 12))
                        except Exception as e:
                            logger.warning(f"Failed to embed extracted image {img_path}: {e}")
                    
                    if clean_text:
                        flowables.append(Spacer(1, 12))

            flush_list()

            # Tables
            for table in doc.tables:
                data = []
                for row in table.rows:
                    row_data = [Paragraph(cell.text, styles['Normal']) for cell in row.cells]
                    data.append(row_data)
                
                if data:
                    t = Table(data)
                    t.setStyle(TableStyle([
                        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ]))
                    flowables.append(t)
                    flowables.append(Spacer(1, 12))

            pdf_doc.build(flowables)
            logger.info("DOCX to PDF conversion completed.")
            return True
        except Exception as e:
            logger.error(f"Failed to convert directly to PDF: {e}")
            raise

    def _convert_to_text(self, input_path: str, output_path: str) -> bool:
        """Convert DOCX to plain text."""
        logger.info(f"Converting DOCX {input_path} to text {output_path}")
        from utils.lazy_loader import lazy_import
        docx = lazy_import('docx')
        
        doc = docx.Document(input_path)
        text_content = []

        for para in doc.paragraphs:
            if para.text:
                prefix = ""
                if para.style.name.startswith('List'):
                    prefix = "- "
                text_content.append(f"{prefix}{para.text}")

        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text for cell in row.cells]
                text_content.append(" | ".join(row_text))

        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write("\n\n".join(text_content))
        return True

    def _convert_to_markdown(self, input_path: str, output_path: str) -> bool:
        """Convert DOCX to Markdown."""
        logger.info(f"Converting DOCX {input_path} to Markdown {output_path}")
        doc = docx.Document(input_path)
        lines = []

        for para in doc.paragraphs:
            if not para.runs:
                continue
                
            style_name = para.style.name
            
            # Accumulate text and images
            para_text = ""
            images_in_para = []
            
            for run in para.runs:
                para_text += run.text
                img_path = self._extract_image_from_run(run, os.path.dirname(output_path) + "/images")
                if img_path:
                    images_in_para.append(img_path)

            text = para_text.strip()
            
            # Add images before text (or after? markdown is flexible, let's append)
            image_lines = []
            for img_path in images_in_para:
                rel_path = os.path.relpath(img_path, os.path.dirname(output_path)).replace("\\", "/")
                image_lines.append(f"![Image]({rel_path})")

            if not text and not image_lines:
                continue
            
            # Add images first
            lines.extend(image_lines)

            if not text:
                continue

            if style_name.startswith('Heading'):
                try:
                    level = int(style_name.split()[-1])
                    lines.append(f"{'#' * level} {text}")
                except ValueError:
                    lines.append(f"# {text}")
            elif style_name.startswith('List Bullet'):
                lines.append(f"- {text}")
            elif style_name.startswith('List Number'):
                lines.append(f"1. {text}")
            else:
                lines.append(text)

        # Tables to Markdown
        for table in doc.tables:
            lines.append("") # Spacing
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows.append(f"| {' | '.join(cells)} |")
            
            if rows:
                lines.append(rows[0])
                # Separator
                cols = len(table.rows[0].cells)
                lines.append(f"| {' | '.join(['---'] * cols)} |")
                lines.extend(rows[1:])
            lines.append("")

        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write("\n\n".join(lines))
        return True

    def _convert_to_html(self, input_path: str, output_path: str) -> bool:
        """Convert DOCX to HTML."""
        logger.info(f"Converting DOCX {input_path} to HTML {output_path}")
        doc = docx.Document(input_path)
        html_parts = ['<html><body>']

        # Helper to close lists
        current_list_type = None # 'ul', 'ol', None

        def close_list():
            nonlocal current_list_type
            if current_list_type:
                html_parts.append(f"</{current_list_type}>")
                current_list_type = None

        for para in doc.paragraphs:
            if not para.runs:
                continue
                
            style_name = para.style.name
            
            # Accumulate HTML parts for this paragraph
            para_html = ""
            images_in_para = []
            
            for run in para.runs:
                # Text with styles
                run_text = run.text
                if not run_text:
                    # Might be just an image run
                    pass
                
                # Apply styles
                # Bold/Italic
                if run.bold:
                    run_text = f"<b>{run_text}</b>"
                if run.italic:
                    run_text = f"<i>{run_text}</i>"
                
                # Color
                if run.font.color and run.font.color.rgb:
                    color_hex = f"#{run.font.color.rgb}"
                    run_text = f'<span style="color: {color_hex}">{run_text}</span>'
                    
                para_html += run_text

                img_path = self._extract_image_from_run(run, os.path.dirname(output_path) + "/images")
                if img_path:
                    images_in_para.append(img_path)

            text = para.text.strip() # Just for checking if empty
            
            # Helper to append images
            def append_images():
                for img_path in images_in_para:
                    rel_path = os.path.relpath(img_path, os.path.dirname(output_path)).replace("\\", "/")
                    html_parts.append(f'<img src="{rel_path}" alt="Image" />')

            if not text and not images_in_para:
                continue

            # Add images before text
            append_images()

            if not text:
                continue
            
            # Use para_html instead of text
            final_html = para_html
            
            # Handle Lists
            if style_name.startswith('List'):
                list_type = 'ol' if 'Number' in style_name else 'ul'
                if current_list_type != list_type:
                    close_list()
                    html_parts.append(f"<{list_type}>")
                    current_list_type = list_type
                html_parts.append(f"<li>{final_html}</li>")
                continue
            else:
                close_list()

            # Handle Headings and Paragraphs
            if style_name.startswith('Heading'):
                try:
                    level = int(style_name.split()[-1])
                    html_parts.append(f"<h{level}>{final_html}</h{level}>")
                except ValueError:
                    html_parts.append(f"<h1>{final_html}</h1>")
            else:
                html_parts.append(f"<p>{final_html}</p>")

        close_list()

        # Tables
        for table in doc.tables:
            html_parts.append("<table border='1'>")
            for row in table.rows:
                html_parts.append("<tr>")
                for cell in row.cells:
                    html_parts.append(f"<td>{cell.text.strip()}</td>")
                html_parts.append("</tr>")
            html_parts.append("</table>")

        html_parts.append('</body></html>')

        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write("\n".join(html_parts))
        return True

    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is a valid DOCX.
        """
        if not os.path.exists(input_path):
            return False
            
        if not input_path.lower().endswith('.docx'):
            return False
            
        try:
            from utils.lazy_loader import lazy_import
            docx = lazy_import('docx')
            doc = docx.Document(input_path)
            return True
        except Exception:
            return False

    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata from DOCX.
        """
        metadata = {}
        try:
            doc = docx.Document(input_path)
            core_props = doc.core_properties
            
            metadata['author'] = core_props.author
            metadata['created'] = core_props.created
            metadata['modified'] = core_props.modified
            metadata['title'] = core_props.title
            metadata['subject'] = core_props.subject
            metadata['keywords'] = core_props.keywords
            metadata['last_modified_by'] = core_props.last_modified_by
            metadata['revision'] = core_props.revision
            
        except Exception as e:
            logger.warning(f"Could not extract metadata from {input_path}: {e}")
            
        return metadata
