import logging
import os
from typing import List, Dict, Any
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

class ImageProcessor:
    """
    Processor for extracting images from documents.
    """

    def extract_images_from_pdf(self, pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF file.

        Args:
            pdf_path: Path to the PDF file.
            output_dir: Directory to save extracted images.

        Returns:
            List of dictionaries containing image metadata (page, name, path).
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return []

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        extracted_images = []

        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                # Try high-level API first (PyPDF2 >= 2.0.0)
                try:
                    if hasattr(page, 'images') and page.images:
                         for image in page.images:
                            image_name = image.name
                            image_path = os.path.join(output_dir, f"page_{page_num + 1}_{image_name}")
                            
                            with open(image_path, "wb") as fp:
                                fp.write(image.data)
                            
                            extracted_images.append({
                                "page": page_num + 1,
                                "name": image_name,
                                "path": image_path
                            })
                            logger.info(f"Extracted image (high-level): {image_path}")
                         continue # processed this page
                except Exception as e:
                    logger.warning(f"High-level image extraction failed for page {page_num + 1}: {e}")

                # Fallback to manual XObject extraction
                if '/XObject' in page['/Resources']:
                    xObject = page['/Resources']['/XObject'].get_object()

                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            image = xObject[obj]
                            try:
                                width = image.get('/Width')
                                height = image.get('/Height')
                                data = image.get_data()
                                
                                # Determine Mode
                                mode = "RGB"
                                color_space = image.get('/ColorSpace')
                                if color_space == '/DeviceCMYK':
                                    mode = "CMYK"
                                elif color_space == '/DeviceGray':
                                    mode = "L"
                                
                                # Filter Handling
                                filters = image.get('/Filter', [])
                                if '/FlateDecode' in filters or '/FlateDecode' == filters:
                                    # Raw pixel data
                                    if width and height:
                                        from PIL import Image
                                        img = Image.frombytes(mode, (width, height), data)
                                        image_name = f"{obj[1:]}.png"
                                        image_path = os.path.join(output_dir, f"page_{page_num + 1}_{image_name}")
                                        img.save(image_path)
                                        
                                        extracted_images.append({
                                            "page": page_num + 1,
                                            "name": image_name,
                                            "path": image_path
                                        })
                                        logger.info(f"Extracted image (manual-pillow): {image_path}")
                                        continue
                                
                                # Default / DCTDecode -> Just dump stream
                                extension = "jpg"
                                if '/JPXDecode' in filters:
                                    extension = "jp2"
                                
                                image_name = f"{obj[1:]}.{extension}"
                                image_path = os.path.join(output_dir, f"page_{page_num + 1}_{image_name}")
                                
                                with open(image_path, "wb") as fp:
                                    fp.write(data)
                                
                                extracted_images.append({
                                    "page": page_num + 1,
                                    "name": image_name,
                                    "path": image_path
                                })
                                logger.info(f"Extracted image (manual-raw): {image_path}")

                            except Exception as e:
                                logger.warning(f"Failed to save image {obj}: {e}")
                
                # Also try the high-level API as fallback or complement
                # (Some versions of PyPDF2 might expose .images differently)


        except Exception as e:
            logger.error(f"Error extracting images from PDF: {e}")

        return extracted_images

    def process_image(self, image_path: str, output_path: str, operations: Dict[str, Any]) -> bool:
        """
        Process an image with specified operations (resize, convert, optimize).
        
        Args:
            image_path: Path to the input image.
            output_path: Path to the output image.
            operations: Dictionary of operations (e.g., {'resize': (800, 600), 'format': 'PNG', 'quality': 85}).
            
        Returns:
            True if successful, False otherwise.
        """
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return False

        try:
            from PIL import Image
        except ImportError:
            logger.error("Pillow not installed. Cannot process images.")
            return False

        try:
            with Image.open(image_path) as img:
                # Resize
                if 'resize' in operations:
                    size = operations['resize']
                    # Use LANCZOS for high quality downsampling
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    logger.info(f"Resized image to {size}")

                # Format conversion (implicitly handled by save, but check explicit arg)
                format = operations.get('format', None)
                if not format:
                    # Infer from output path or keep original
                    ext = os.path.splitext(output_path)[1].lower()
                    if ext in ['.jpg', '.jpeg']: format = 'JPEG'
                    elif ext == '.png': format = 'PNG'
                    elif ext == '.webp': format = 'WEBP'
                
                # Quality/Optimization
                save_kwargs = {}
                if 'quality' in operations:
                    save_kwargs['quality'] = operations['quality']
                
                if 'optimize' in operations and operations['optimize']:
                    save_kwargs['optimize'] = True

                # Convert mode if necessary (e.g. RGBA to JPEG needs RGB)
                if format == 'JPEG' and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                img.save(output_path, format=format, **save_kwargs)
                logger.info(f"Processed image saved to {output_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            return False

    def convert_image_format(self, input_path: str, output_path: str, format: str = None) -> bool:
        """Helper to convert image format."""
        return self.process_image(input_path, output_path, {'format': format} if format else {})

    def resize_image(self, input_path: str, output_path: str, width: int, height: int) -> bool:
        """Helper to resize image."""
        return self.process_image(input_path, output_path, {'resize': (width, height)})

    def optimize_image(self, input_path: str, output_path: str, quality: int = 85) -> bool:
        """Helper to optimize image."""
        return self.process_image(input_path, output_path, {'optimize': True, 'quality': quality})

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode an image file to a base64 string.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Base64 encoded string of the image, or empty string if failure.
        """
        import base64
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image not found for encoding: {image_path}")
                return ""
                
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
            return encoded_string
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            return ""

