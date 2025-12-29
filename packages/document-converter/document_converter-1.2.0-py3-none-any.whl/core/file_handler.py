import os
import chardet
from typing import Generator, Optional

class FileHandler:
    """
    Handles file operations including chunked reading/writing and encoding detection.
    """

    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """
        Detects the encoding of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Detected encoding string (e.g., 'utf-8', 'ascii'). 
            Defaults to 'utf-8' if detection fails or confidence is low.
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB for detection
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except Exception as e:
            # Log error ideally
            print(f"Error detecting encoding: {e}")
            return 'utf-8'

    @staticmethod
    def read_file_chunks(file_path: str, chunk_size: int = 8192) -> Generator[bytes, None, None]:
        """
        Reads a file in chunks to be memory efficient.
        
        Args:
            file_path: Path to the file.
            chunk_size: Size of each chunk in bytes.
            
        Yields:
            Bytes chunks from the file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @staticmethod
    def write_file_chunks(file_path: str, data_generator: Generator[bytes, None, None]) -> None:
        """
        Writes data from a generator to a file.
        
        Args:
            file_path: Path to the destination file.
            data_generator: Generator yielding bytes to write.
        """
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'wb') as f:
            for chunk in data_generator:
                f.write(chunk)
