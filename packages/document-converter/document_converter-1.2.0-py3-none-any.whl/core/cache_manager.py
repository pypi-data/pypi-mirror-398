import os
import json
import shutil
import hashlib
import time
import logging
from functools import lru_cache
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages caching of conversion results to avoid redundant processing.
    Uses file content hash and conversion options to identify unique tasks.
    Implements two-tier caching: in-memory LRU cache + disk cache.
    """
    
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600 * 24, memory_cache_size: int = 128):
        """
        Initialize CacheManager.
        
        Args:
            cache_dir: Directory to store cached files and metadata.
            default_ttl: Default Time To Live in seconds (default: 24h).
            memory_cache_size: Maximum number of items in memory cache.
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata: Dict[str, Any] = {}
        self._memory_cache: Dict[str, str] = {}  # key -> cached_file_path
        self._memory_cache_size = memory_cache_size
        
        self._ensure_cache_dir()
        self._load_metadata()

    def _ensure_cache_dir(self):
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self):
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self):
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except FileNotFoundError:
            return ""

    def _generate_key(self, input_hash: str, options: Dict[str, Any]) -> str:
        """Generate a unique cache key based on input hash and options."""
        options_str = json.dumps(options, sort_keys=True)
        options_hash = hashlib.md5(options_str.encode()).hexdigest()
        return f"{input_hash}_{options_hash}"

    def get(self, input_path: str, options: Dict[str, Any] = None) -> Optional[str]:
        """
        Retrieve a cached file path if it exists and hasn't expired.
        
        Args:
            input_path: Path to the input file.
            options: Dictionary of conversion options.
            
        Returns:
            Path to the cached output file, or None if not found/expired.
        """
        if options is None:
            options = {}
            
        input_hash = self.get_file_hash(input_path)
        if not input_hash:
            return None
            
        key = self._generate_key(input_hash, options)
        
        # Check memory cache first (fastest)
        if key in self._memory_cache:
            cached_path = self._memory_cache[key]
            if os.path.exists(cached_path):
                return cached_path
            else:
                # Memory cache entry invalid
                del self._memory_cache[key]
        
        if key in self.metadata:
            entry = self.metadata[key]
            
            # Check expiration
            if time.time() > entry['expires_at']:
                self.delete(key)
                return None
                
            cached_path = self.cache_dir / entry['filename']
            if cached_path.exists():
                cached_path_str = str(cached_path)
                # Populate memory cache
                self._add_to_memory_cache(key, cached_path_str)
                return cached_path_str
            else:
                # File missing but metadata exists
                self.delete(key)
                
        return None

    def set(self, input_path: str, output_path: str, options: Dict[str, Any] = None, ttl: Optional[int] = None):
        """
        Cache a conversion result.
        
        Args:
            input_path: Path to original input file.
            output_path: Path to the generated output file.
            options: Conversion options used.
            ttl: Custom TTL in seconds.
        """
        if options is None:
            options = {}
            
        if not os.path.exists(output_path):
            return

        input_hash = self.get_file_hash(input_path)
        if not input_hash:
            return
            
        key = self._generate_key(input_hash, options)
        ttl = ttl if ttl is not None else self.default_ttl
        
        # Determine cached filename (preserve extension of output)
        ext = os.path.splitext(output_path)[1]
        cached_filename = f"{key}{ext}"
        cached_path = self.cache_dir / cached_filename
        
        # Copy file to cache
        try:
            shutil.copy2(output_path, cached_path)
            
            self.metadata[key] = {
                'filename': cached_filename,
                'created_at': time.time(),
                'expires_at': time.time() + ttl,
                'input_path': input_path
            }
            self._save_metadata()
            
            # Add to memory cache
            self._add_to_memory_cache(key, str(cached_path))
            
        except Exception as e:
            logger.error(f"Failed to cache file: {e}")

    def _add_to_memory_cache(self, key: str, path: str):
        """Add entry to memory cache with LRU eviction."""
        # Simple LRU: if cache is full, remove oldest entry
        if len(self._memory_cache) >= self._memory_cache_size:
            # Remove first (oldest) item
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
        
        # Move to end (mark as recently used)
        if key in self._memory_cache:
            del self._memory_cache[key]
        self._memory_cache[key] = path

    def delete(self, key: str):
        """Remove an entry from cache."""
        if key in self.metadata:
            entry = self.metadata[key]
            cached_path = self.cache_dir / entry['filename']
            if cached_path.exists():
                try:
                    os.remove(cached_path)
                except OSError as e:
                    logger.warning(f"Error deleting cached file {cached_path}: {e}")
            
            del self.metadata[key]
            self._save_metadata()

    def cleanup(self):
        """Remove all expired entries."""
        now = time.time()
        keys_to_delete = [
            k for k, v in self.metadata.items() 
            if now > v['expires_at']
        ]
        
        for key in keys_to_delete:
            self.delete(key)
            
        logger.info(f"Cleaned up {len(keys_to_delete)} expired cache entries.")

    def clear_all(self):
        """Clear entire cache."""
        try:
            shutil.rmtree(self.cache_dir)
            self._ensure_cache_dir()
            self.metadata = {}
            self._save_metadata()
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        count = len(self.metadata)
        total_size = 0
        
        for root, _, files in os.walk(self.cache_dir):
            for f in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
                    
        return {
            "items": count,
            "total_size_bytes": total_size
        }
