import hashlib
import os
from typing import Optional

def check_file_exists(path: str) -> bool:
    """Checks if a file exists."""
    return os.path.exists(path) and os.path.isfile(path)

def check_file_size(path: str, max_size: int) -> bool:
    """
    Checks if a file size is within the limit.
    
    Args:
        path: Path to the file.
        max_size: Maximum allowed size in bytes.
        
    Returns:
        True if file size <= max_size, False otherwise.
    """
    if not check_file_exists(path):
        return False
    return os.path.getsize(path) <= max_size

def check_permissions(path: str, read: bool = True, write: bool = False) -> bool:
    """
    Checks file permissions.
    
    Args:
        path: Path to the file.
        read: Check for read permission.
        write: Check for write permission.
        
    Returns:
        True if permissions are sufficient, False otherwise.
    """
    if not os.path.exists(path):
        return False
        
    if read and not os.access(path, os.R_OK):
        return False
        
    if write and not os.access(path, os.W_OK):
        return False
        
    return True

def calculate_checksum(path: str, algorithm: str = 'sha256') -> str:
    """
    Calculates the checksum of a file.
    
    Args:
        path: Path to the file.
        algorithm: Hashing algorithm ('md5', 'sha256', etc.).
        
    Returns:
        Hex digest of the checksum.
    """
    if not check_file_exists(path):
        raise FileNotFoundError(f"File not found: {path}")
        
    hash_func = getattr(hashlib, algorithm)()
    with open(path, "rb") as f:
        # Read in chunks to avoid memory issues with large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
            
    return hash_func.hexdigest()

def validate_file_type(path: str, expected_mime: str) -> bool:
    """
    Validates the MIME type of a file using python-magic.
    
    Args:
        path: Path to the file.
        expected_mime: Expected MIME type (e.g., 'application/pdf').
        
    Returns:
        True if MIME type matches, False otherwise.
    """
    if not check_file_exists(path):
        return False
        
    try:
        import magic
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(path)
    except ImportError:
        # Fallback if libmagic is not installed/found
        # For now, we might want to log a warning or return True (permissive)
        # or False (strict). Let's be permissive but print a warning.
        print("Warning: libmagic not found. Skipping MIME validation.")
        return True
    except Exception as e:
        print(f"Error validating MIME type: {e}")
        return False
    
    # Simple check: exact match or starts with (e.g. 'image/' matches 'image/jpeg')
    return file_mime == expected_mime or file_mime.startswith(expected_mime)
