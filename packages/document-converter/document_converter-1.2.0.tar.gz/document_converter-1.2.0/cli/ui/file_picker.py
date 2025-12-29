"""
Interactive File Picker for CLI

Provides interactive file selection to avoid typing full paths.
Uses lazy loading for optional UI libraries (questionary, prompt-toolkit).
Falls back to basic text input if libraries are not available.
"""

import os
import logging
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


def list_files_in_directory(directory: str = ".", pattern: str = "*") -> List[Path]:
    """
    List files in a directory matching a pattern.
    
    Args:
        directory: Directory to list files from (default: current directory)
        pattern: Glob pattern to filter files (default: all files)
        
    Returns:
        List of Path objects for matching files
    """
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return []
    
    # Get all files matching pattern
    files = sorted([f for f in path.glob(pattern) if f.is_file()])
    return files


def pick_file_interactive(
    directory: str = ".",
    pattern: str = "*",
    prompt_text: str = "Select a file:"
) -> Optional[str]:
    """
    Interactive file picker with lazy-loaded UI library.
    
    Args:
        directory: Directory to list files from
        pattern: Glob pattern to filter files
        prompt_text: Prompt message to display
        
    Returns:
        Selected file path as string, or None if cancelled/failed
    """
    files = list_files_in_directory(directory, pattern)
    
    if not files:
        print(f"No files found in {directory} matching pattern '{pattern}'")
        return None
    
    # Try to use questionary for better UX
    try:
        from utils.lazy_loader import lazy_import
        questionary = lazy_import('questionary')
        
        # Create choices with file names
        choices = [str(f.name) for f in files]
        
        # Show interactive selection
        answer = questionary.select(
            prompt_text,
            choices=choices
        ).ask()
        
        if answer:
            # Find the full path
            for f in files:
                if f.name == answer:
                    return str(f)
        return None
        
    except ImportError:
        logger.debug("questionary not available, using fallback picker")
        return _pick_file_fallback(files, prompt_text)


def _pick_file_fallback(files: List[Path], prompt_text: str) -> Optional[str]:
    """
    Fallback file picker using basic text input.
    
    Args:
        files: List of file paths to choose from
        prompt_text: Prompt message to display
        
    Returns:
        Selected file path as string, or None if cancelled
    """
    print(f"\n{prompt_text}")
    print("-" * 50)
    
    # Display numbered list
    for idx, file_path in enumerate(files, 1):
        # Show file size
        size = file_path.stat().st_size
        size_str = _format_file_size(size)
        print(f"{idx}. {file_path.name} ({size_str})")
    
    print("-" * 50)
    print("Enter the number of your choice (or 'q' to quit): ", end="")
    
    try:
        choice = input().strip()
        
        if choice.lower() in ('q', 'quit', 'exit'):
            return None
        
        # Parse the number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return str(files[idx])
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(files)}")
                return None
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None
            
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return None


def _format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string like "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def pick_output_file(
    default_name: str = "output",
    default_ext: str = ".txt",
    prompt_text: str = "Enter output filename:"
) -> Optional[str]:
    """
    Prompt for output file name.
    
    Args:
        default_name: Default filename without extension
        default_ext: Default file extension
        prompt_text: Prompt message
        
    Returns:
        Output file path, or None if cancelled
    """
    try:
        from utils.lazy_loader import lazy_import
        questionary = lazy_import('questionary')
        
        default_full = f"{default_name}{default_ext}"
        answer = questionary.text(
            prompt_text,
            default=default_full
        ).ask()
        
        return answer if answer else None
        
    except ImportError:
        # Fallback to basic input
        default_full = f"{default_name}{default_ext}"
        print(f"\n{prompt_text}")
        print(f"Default: {default_full}")
        print("Press Enter to use default, or type a new name: ", end="")
        
        try:
            choice = input().strip()
            return choice if choice else default_full
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return None
