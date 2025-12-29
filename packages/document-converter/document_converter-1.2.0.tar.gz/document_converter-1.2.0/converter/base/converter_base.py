from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import os

class BaseConverter(ABC):
    """
    Abstract base class for all document converters.
    Defines the standard interface that all converters must implement.
    """

    @abstractmethod
    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert the input file to the output format.
        
        Args:
            input_path: Path to the input file.
            output_path: Path where the converted file should be saved.
            **kwargs: Additional conversion options.
            
        Returns:
            True if conversion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def validate_input(self, input_path: str) -> bool:
        """
        Validate if the input file is valid for this converter.
        
        Args:
            input_path: Path to the input file.
            
        Returns:
            True if valid, False otherwise.
        """
        pass

    @abstractmethod
    def extract_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata from the input file.
        
        Args:
            input_path: Path to the input file.
            
        Returns:
            Dictionary containing metadata.
        """
        pass

    def _ensure_output_directory(self, output_path: str):
        """
        Helper method to ensure the output directory exists.
        """
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
