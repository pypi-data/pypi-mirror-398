import logging
from typing import List, Dict, Type
from converter.base.converter_base import BaseConverter
# Import all converters
from converter.formats.txt_converter import TXTConverter
from converter.formats.markdown_converter import MarkdownConverter
from converter.formats.html_converter import HTMLConverter
from converter.formats.pdf_converter import PDFConverter
from converter.formats.docx_converter import DOCXConverter
from converter.formats.odt_converter import ODTConverter

logger = logging.getLogger(__name__)

def register_all_converters(engine) -> None:
    """
    Registers all available converters to the provided ConversionEngine instance.
    
    Args:
        engine: The ConversionEngine instance to register converters with.
    """
    converters = {
        'txt': TXTConverter,
        'md': MarkdownConverter,
        'html': HTMLConverter,
        'pdf': PDFConverter,
        'docx': DOCXConverter,
        'odt': ODTConverter
    }
    
    for format_name, converter_class in converters.items():
        engine.register_converter(format_name, converter_class)
        logger.debug(f"Registered {format_name} converter via registry")

def get_supported_formats() -> List[str]:
    """
    Returns a list of supported format extensions.
    
    Returns:
        List[str]: List of supported formats (e.g., ['txt', 'md', ...])
    """
    return ['txt', 'md', 'html', 'pdf', 'docx', 'odt']
