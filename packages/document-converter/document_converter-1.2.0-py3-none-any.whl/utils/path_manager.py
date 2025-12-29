import os
import re
from typing import Optional

class PathManager:
    """
    Utilities for managing file system paths safely.
    """

    @staticmethod
    def resolve_path(path: str, base_dir: Optional[str] = None) -> str:
        """
        Resolves a path to an absolute path.
        
        Args:
            path: The path to resolve.
            base_dir: Optional base directory to resolve relative paths against.
            
        Returns:
            Absolute path.
        """
        if base_dir:
            path = os.path.join(base_dir, path)
        return os.path.abspath(path)

    @staticmethod
    def ensure_directory(path: str) -> None:
        """
        Ensures that a directory exists, creating it if necessary.
        
        Args:
            path: Path to the directory.
        """
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitizes a filename by removing unsafe characters.
        
        Args:
            filename: The filename to sanitize.
            
        Returns:
            Sanitized filename.
        """
        # Remove null bytes
        filename = filename.replace('\0', '')
        
        # Remove leading/trailing dots and spaces first
        filename = filename.strip(' .')
        
        # Replace unsafe characters with underscore
        # Allow alphanumeric, dot, dash, underscore
        filename = re.sub(r'[^\w\-\.]', '_', filename)
        
        return filename or "unnamed_file"

    @staticmethod
    def clean_path(path: str) -> str:
        """
        Normalizes a path, removing redundant separators and up-level references.
        
        Args:
            path: The path to clean.
            
        Returns:
            Normalized path.
        """
        return os.path.normpath(path)

    @staticmethod
    def is_safe_path(path: str, base_dir: str) -> bool:
        """
        Checks if a path is safe (i.e., contained within the base directory).
        Prevents directory traversal attacks.
        
        Args:
            path: The path to check.
            base_dir: The trusted base directory.
            
        Returns:
            True if the path is safe, False otherwise.
        """
        resolved_path = os.path.abspath(path)
        resolved_base = os.path.abspath(base_dir)
        
        return os.path.commonpath([resolved_base, resolved_path]) == resolved_base
