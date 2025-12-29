import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class StyleProcessor:
    """
    Processor for handling style conversions between formats.
    Maps CSS styles to standard document styles (DOCX/ODT) and vice-versa.
    """

    # Common standard colors mapping (Example)
    COLOR_MAP = {
        'red': (255, 0, 0),
        'green': (0, 128, 0),
        'blue': (0, 0, 255),
        'black': (0, 0, 0),
        'white': (255, 255, 255)
    }

    # Font sizing map (approximate pt sizes)
    FONT_SIZE_MAP = {
        'h1': 24,
        'h2': 18,
        'h3': 14,
        'p': 11,
        'small': 9
    }

    def __init__(self):
        pass

    def css_to_rgb(self, css_color: str) -> Optional[Tuple[int, int, int]]:
        """
        Convert CSS color string to RGB tuple.
        Supports hex (#RRGGBB, #RGB) and basic named colors.
        """
        if not css_color:
            return None
        
        css_color = css_color.lower().strip()
        
        # Named colors
        if css_color in self.COLOR_MAP:
            return self.COLOR_MAP[css_color]
            
        # Hex colors
        if css_color.startswith('#'):
            hex_val = css_color.lstrip('#')
            try:
                if len(hex_val) == 6:
                    return tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
                elif len(hex_val) == 3:
                     return tuple(int(c*2, 16) for c in hex_val)
            except ValueError:
                pass
                
        return None

    def map_font_size(self, element_tag: str, base_size: int = 11) -> int:
        """
        Map HTML tag to font size in points.
        """
        return self.FONT_SIZE_MAP.get(element_tag.lower(), base_size)

    def get_style_properties(self, element: str) -> Dict[str, Any]:
        """
        Get standard style properties for a given structural element (e.g., 'h1', 'p').
        Returns a dict with 'font_size', 'bold', etc.
        """
        props = {}
        tag = element.lower()
        
        props['font_size'] = self.map_font_size(tag)
        
        if tag in ['h1', 'h2', 'h3', 'b', 'strong']:
            props['bold'] = True
            
        if tag in ['i', 'em']:
            props['italic'] = True
            
        return props
