"""
Lazy Import Utility

This module provides utilities for lazy importing of modules to improve startup performance.
Instead of importing all dependencies at module load time, imports are deferred until they're
actually needed.

Example usage in converters:
    
    from utils.lazy_loader import lazy_import
    
    def convert(self, input_path, output_path):
        # Module is only imported when this function is called
        markdown = lazy_import('markdown')
        html = markdown.markdown(text)
        ...
"""

import importlib
import sys
from typing import Any


def lazy_import(module_name: str) -> Any:
    """
    Lazily import a module on demand and memoize it in sys.modules.
    
    This function defers the actual import until it's called, which can significantly
    improve startup time when dealing with many optional dependencies. Once imported,
    the module is cached in sys.modules for subsequent calls.
    
    Args:
        module_name: Fully qualified module name (e.g., 'markdown', 'bs4.BeautifulSoup')
    
    Returns:
        The imported module object
        
    Raises:
        ImportError: If the module cannot be imported
        
    Example:
        >>> # Import only when needed
        >>> def process_markdown():
        ...     markdown = lazy_import('markdown')
        ...     return markdown.markdown("# Hello")
        
        >>> # Module is cached after first import
        >>> md1 = lazy_import('markdown')
        >>> md2 = lazy_import('markdown')  # Same object, no re-import
        >>> assert md1 is md2
    """
    # Check if module is already imported
    if module_name in sys.modules:
        return sys.modules[module_name]
    
    # Import the module - this will automatically add it to sys.modules
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        raise ImportError(
            f"Failed to lazy import module '{module_name}'. "
            f"Ensure the module is installed: {e}"
        ) from e
