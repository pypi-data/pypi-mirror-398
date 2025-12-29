#!/usr/bin/env python3
"""
Cache Usage Example

Demonstrates using caching to speed up repeated conversions.
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from converter.engine import ConversionEngine
from converter.formats.txt_converter import TXTConverter
from core.cache_manager import CacheManager


def create_sample_file():
    """Create a sample file for conversion."""
    with open('sample.txt', 'w', encoding='utf-8') as f:
        f.write("""# Performance Test Document

This document is used to demonstrate caching speedup.

""" + "Lorem ipsum dolor sit amet.\n" * 100)  # Make it reasonably sized


def example_without_cache():
    """Conversion without caching."""
    print("\n=== Example 1: Without Cache ===")
    
    create_sample_file()
    
    engine = ConversionEngine()  # No cache
    engine.register_converter('txt', TXTConverter)
    
    # Time 3 conversions
    times = []
    for i in range(3):
        start = time.time()
        engine.convert('sample.txt', f'output_{i}.html')
        duration = time.time() - start
        times.append(duration)
        print(f"  Conversion {i+1}: {duration:.4f}s")
    
    avg = sum(times) / len(times)
    print(f"  Average: {avg:.4f}s")
    
    # Cleanup
    for i in range(3):
        if os.path.exists(f'output_{i}.html'):
            os.remove(f'output_{i}.html')
    
    return avg


def example_with_cache():
    """Conversion with caching enabled."""
    print("\n=== Example 2: With Cache ===")
    
    create_sample_file()
    
    # Create cache
    cache = CacheManager(cache_dir='.demo_cache')
    engine = ConversionEngine(cache_manager=cache)
    engine.register_converter('txt', TXTConverter)
    
    # Time 3 conversions (2nd and 3rd should be fast)
    times = []
    for i in range(3):
        start = time.time()
        engine.convert('sample.txt', f'cached_{i}.html')
        duration = time.time() - start
        times.append(duration)
        status = "cache miss" if i ==0 else "cache HIT"
        print(f"  Conversion {i+1}: {duration:.4f}s ({status})")
    
    avg = sum(times) / len(times)
    print(f"  Average: {avg:.4f}s")
    
    # Show speedup
    if times[0] > 0:
        speedup = times[0] / times[2]
        print(f"  Speedup: {speedup:.1f}x faster with cache!")
    
    # Cleanup
    for i in range(3):
        if os.path.exists(f'cached_{i}.html'):
            os.remove(f'cached_{i}.html')
    import shutil
    if os.path.exists('.demo_cache'):
        shutil.rmtree('.demo_cache')
    
    return avg


def example_cache_stats():
    """Display cache statistics."""
    print("\n=== Example 3: Cache Statistics ===")
    
    create_sample_file()
    
    cache = CacheManager(cache_dir='.stats_cache')
    engine = ConversionEngine(cache_manager=cache)
    engine.register_converter('txt', TXTConverter)
    
    # Do some conversions
    for i in range(5):
        engine.convert('sample.txt', f'test_{i}.html')
    
    # Get stats
    stats = cache.get_stats()
    print(f"  Cache items: {stats['items']}")
    print(f"  Total size: {stats['total_size_bytes']:,} bytes")
    
    # Cleanup
    for i in range(5):
        if os.path.exists(f'test_{i}.html'):
            os.remove(f'test_{i}.html')
    import shutil
    if os.path.exists('.stats_cache'):
        shutil.rmtree('.stats_cache')


def example_cache_ttl():
    """Demonstrate TTL (time-to-live) expiration."""
    print("\n=== Example 4: Cache TTL ===")
    
    create_sample_file()
    
    # Create cache with 2-second TTL
    cache = CacheManager(cache_dir='.ttl_cache', default_ttl=2)
    engine = ConversionEngine(cache_manager=cache)
    engine.register_converter('txt', TXTConverter)
    
    # First conversion
    print("  First conversion...")
    engine.convert('sample.txt', 'ttl_output1.html')
    
    # Immediate second conversion (should hit cache)
    print("  Immediate retry (should be cached)...")
    start = time.time()
    engine.convert('sample.txt', 'ttl_output2.html')
    duration = time.time() - start
    print(f"    Time: {duration:.4f}s (cache hit)")
    
    # Wait for TTL to expire
    print("  Waiting 2.5 seconds for TTL expiration...")
    time.sleep(2.5)
    
    # Third conversion (cache expired, should be slower)
    print("  After TTL expiration...")
    # Clear memory cache to force disk check
    cache._memory_cache.clear()
    start = time.time()
    engine.convert('sample.txt', 'ttl_output3.html')
    duration = time.time() - start
    print(f"    Time: {duration:.4f}s (cache expired, re-converted)")
    
    # Cleanup
    for i in range(1, 4):
        if os.path.exists(f'ttl_output{i}.html'):
            os.remove(f'ttl_output{i}.html')
    import shutil
    if os.path.exists('.ttl_cache'):
        shutil.rmtree('.ttl_cache')


def cleanup():
    """Clean up generated files."""
    if os.path.exists('sample.txt'):
        os.remove('sample.txt')
    print("\n✓ Cleaned up files")


if __name__ == '__main__':
    print("=" * 60)
    print("CACHE USAGE EXAMPLES")
    print("=" * 60)
    
    try:
        time_no_cache = example_without_cache()
        time_with_cache = example_with_cache()
        example_cache_stats()
        example_cache_ttl()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        speedup = time_no_cache / time_with_cache if time_with_cache > 0 else 0
        print(f"Average without cache: {time_no_cache:.4f}s")
        print(f"Average with cache: {time_with_cache:.4f}s")
        print(f"Overall speedup: {speedup:.1f}x")
        
    finally:
        cleanup()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
