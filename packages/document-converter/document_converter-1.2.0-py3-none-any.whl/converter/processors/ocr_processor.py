import logging
import os
import io
from typing import List, Dict, Any, Optional
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    from langdetect import detect
except ImportError:
    pytesseract = None
    Image = None
    convert_from_path = None
    detect = None

from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    Processor for Optical Character Recognition (OCR).
    Uses pytesseract (Tesseract-OCR) to extract text from scanned documents and images.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR Processor.
        
        Args:
            tesseract_cmd: Optional path to tesseract executable.
        """
        if tesseract_cmd and pytesseract:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.enabled = pytesseract is not None and convert_from_path is not None

    def is_scanned_pdf(self, pdf_path: str, text_threshold: int = 50) -> bool:
        """
        Detect if a PDF is likely scanned (contains little to no text).
        
        Args:
            pdf_path: Path to PDF file.
            text_threshold: Minimum number of characters per page to consider it "text-based".
            
        Returns:
            True if PDF is likely scanned, False otherwise.
        """
        if not os.path.exists(pdf_path):
            return False

        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                num_pages = len(reader.pages)
                if num_pages == 0:
                    return False
                
                # Check first few pages (e.g., up to 3) to enable fast detection
                pages_to_check = min(3, num_pages)
                total_text_len = 0
                
                for i in range(pages_to_check):
                    text = reader.pages[i].extract_text()
                    if text:
                        total_text_len += len(text.strip())
                
                avg_text = total_text_len / pages_to_check
                
                # If average text is very low, it's likely scanned or image-based
                return avg_text < text_threshold
                
        except Exception as e:
            logger.error(f"Error analyzing PDF for OCR detection: {e}")
            return False

    def perform_ocr(self, input_path: str, output_path: str = None, lang: str = 'eng') -> str:
        """
        Perform OCR on a file (PDF or Image).
        
        Args:
            input_path: Path to input file.
            output_path: Optional path to save the extracted text.
            lang: Language code for Tesseract (default: 'eng').
            
        Returns:
            Extracted text string.
        """
        if not self.enabled:
            logger.error("OCR dependencies (pytesseract, pdf2image) not installed.")
            return ""

        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return ""

        lang = self._resolve_language(input_path, lang)
        logger.info(f"Starting OCR on {input_path} with language {lang}")
        extracted_text = ""
        
        try:
            ext = os.path.splitext(input_path)[1].lower()
            
            if ext == '.pdf':
                # Convert PDF to images
                try:
                    images = convert_from_path(input_path)
                    for i, image in enumerate(images):
                        logger.info(f"Processing page {i+1}...")
                        text = pytesseract.image_to_string(image, lang=lang)
                        extracted_text += f"--- Page {i+1} ---\n{text}\n\n"
                except Exception as e:
                    logger.error(f"Failed to convert PDF to images: {e}")
                    return ""
            
            elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp']:
                # Process image directly
                try:
                    with Image.open(input_path) as img:
                        extracted_text = pytesseract.image_to_string(img, lang=lang)
                except Exception as e:
                    logger.error(f"Failed to process image: {e}")
                    return ""
            else:
                logger.error(f"Unsupported file type for OCR: {ext}")
                return ""

            # Save to output file if requested
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                logger.info(f"OCR result saved to {output_path}")

            return extracted_text

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def create_searchable_pdf(self, input_path: str, output_path: str, lang: str = 'eng') -> bool:
        """
        Convert a scanned PDF (or images) to a searchable PDF.
        
        Args:
            input_path: Path to input file (PDF or Image).
            output_path: Path to output searchable PDF.
            lang: Language code.
            
        Returns:
            True if successful.
        """
        if not self.enabled:
            logger.error("OCR dependencies not installed.")
            return False

        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return False
            
        lang = self._resolve_language(input_path, lang)
        logger.info(f"Creating searchable PDF from {input_path} with language {lang}")
        
        try:
            pdf_writer = PdfWriter()
            ext = os.path.splitext(input_path)[1].lower()
            
            # Get images to process
            images_to_process = []
            if ext == '.pdf':
                try:
                    images_to_process = convert_from_path(input_path)
                except Exception as e:
                    logger.error(f"Failed to convert PDF to images: {e}")
                    return False
            elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp']:
                try:
                    with Image.open(input_path) as img:
                        # Ensure we work with a copy or keep it valid? 
                        # pdf2image returns PIL images. We should unify list.
                        # For single image, just a list of 1.
                        # Image.open is lazy, so we might need to load or copy if we close it.
                        # But here we are in a block? No, `with` closes it efficiently.
                        # Better to load it fully.
                        img_copy = img.copy()
                        images_to_process = [img_copy]
                except Exception as e:
                    logger.error(f"Failed to open image: {e}")
                    return False
            else:
                logger.error(f"Unsupported input format: {ext}")
                return False

            # Process each image
            for i, image in enumerate(images_to_process):
                logger.info(f"Performing OCR on page {i+1}...")
                try:
                    # Get PDF bytes from Tesseract
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension='pdf', lang=lang)
                    
                    # Read into PyPDF2 page
                    page_reader = PdfReader(io.BytesIO(pdf_bytes))
                    if len(page_reader.pages) > 0:
                        pdf_writer.add_page(page_reader.pages[0])
                    else:
                        logger.warning(f"No content generated for page {i+1}")
                        
                except Exception as e:
                    logger.error(f"OCR failed for page {i+1}: {e}")
                    # Continue or fail? Let's continue to save what we can.
                    continue

            # Write output
            with open(output_path, "wb") as f_out:
                pdf_writer.write(f_out)
                
            logger.info(f"Searchable PDF saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create searchable PDF: {e}")
            return False

    def detect_language(self, input_path: str) -> str:
        """
        Detect language of the document.
        
        Args:
            input_path: Path to input file.
            
        Returns:
            Language code (e.g. 'eng', 'spa'), or 'eng' default.
            Returns concatenated codes if multi-lang is detected (not supported here, simpler logic).
        """
        if not self.enabled:
            return 'eng'

        if detect is None:
            logger.warning("langdetect not installed, defaulting to 'eng'")
            return 'eng'

        try:
            # Extract sample text using default 'eng' or 'osd'
            # 'osd' might not give enough text for langdetect.
            # Using 'eng' is safer to get some Latin characters.
            # We only need a small sample.
            text_sample = ""
            ext = os.path.splitext(input_path)[1].lower()
            
            if ext == '.pdf':
                # Convert first page only
                try:
                    images = convert_from_path(input_path, first_page=1, last_page=1)
                    if images:
                        text_sample = pytesseract.image_to_string(images[0], lang='eng')
                except Exception:
                    pass
            else:
                 try:
                    with Image.open(input_path) as img:
                        text_sample = pytesseract.image_to_string(img, lang='eng')
                 except Exception:
                    pass
            
            if not text_sample or len(text_sample.strip()) < 10:
                logger.warning("Not enough text to detect language, defaulting to 'eng'")
                return 'eng'
                
            detected = detect(text_sample)
            logger.info(f"Detected language: {detected}")
            
            # Map common ISO 639-1 to Tesseract 3-letter codes
            mapping = {
                'en': 'eng',
                'es': 'spa',
                'fr': 'fra',
                'de': 'deu',
                'it': 'ita',
                'pt': 'por',
                'ru': 'rus',
                'zh-cn': 'chi_sim',
                'zh-tw': 'chi_tra',
                'ja': 'jpn'
                # Add more as needed
            }
            
            return mapping.get(detected, 'eng') # Default/Fallback to eng if not in map (or if detected matches 3-letter, tesseract might handle common ones but let's be safe)
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to 'eng'")
            return 'eng'

    def _resolve_language(self, input_path: str, lang: str) -> str:
        """Helper to resolve 'auto' language."""
        if lang == 'auto':
            return self.detect_language(input_path)
        return lang
