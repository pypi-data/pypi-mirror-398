# Cache Usage Example

This example demonstrates performance improvements using caching.

## What This Example Shows

- Converting without cache (baseline)
- Using cache for speedup
- Cache statistics and monitoring
- TTL (time-to-live) expiration

## Files

- `example.py` - Cache demonstrations

## Examples Included

### Example 1: Without Cache
Baseline performance without caching.

### Example 2: With Cache
Shows dramatic speedup on repeated conversions.

### Example 3: Cache Statistics
Display cache metrics.

### Example 4: Cache TTL
Demonstrate time-based cache expiration.

## Running the Example

```bash
cd examples/04_cache_usage
python example.py
```

## Expected Output

The script will:
1. Convert a file 3 times without cache
2. Convert 3 times with cache (2nd and 3rd are fast)
3. Show cache statistics
4. Demonstrate TTL expiration
5. Display overall speedup comparison

## Key Concepts

### Creating Cache Manager

```python
from core.cache_manager import CacheManager

cache = CacheManager(
    cache_dir=".cache",
    default_ttl=3600,  # 1 hour
    memory_cache_size=128
)
```

### Using Cache with Engine

```python
engine = ConversionEngine(cache_manager=cache)
```

The engine will automatically:
- Check cache before converting
- Store results in cache after converting
- Use cache for identical files

### Two-Tier Caching

The cache has two layers:

1. **Memory Cache (LRU)**:
   - Very fast (~0.3ms lookup)
   - Limited size (default 128 items)
   - Lost when program exits

2. **Disk Cache**:
   - Persistent across sessions
   - Unlimited size (limited by disk)
   - Slower (~100ms lookup) but still fast

### TTL (Time-To-Live)

```python
cache = CacheManager(default_ttl=3600)  # 1 hour
```

After TTL expires, cached items are re-converted.

### Cache Statistics

```python
stats = cache.get_stats()
print(f"Items: {stats['items']}")
print(f"Size: {stats['total_size_bytes']} bytes")
```

## Performance Benchmarks

Typical speedup results:
- **First conversion**: Normal speed (baseline)
- **Memory cache hit**: 100-500x faster
- **Disk cache hit**: 10-50x faster

## When to Use Caching

✅ **Use caching when:**
- Processing the same files multiple times
- Running in production with repeated requests
- Batch processing with possible duplicates
- Development/testing (speeds up iterations)

❌ **Skip caching when:**
- Files are always unique (never repeated)
- Files change frequently
- Disk space is limited
- Cache overhead > conversion time

## Cache Management

### Clear Cache

```python
cache.clear()
```

### Custom TTL Per File

```python
cache.set(input_path, output_path, ttl=7200)  # 2 hours
```

### Disable Cache

```python
engine = ConversionEngine()  # No cache_manager
```

## Next Steps

- Combine with batch processing for maximum performance
- Tune `memory_cache_size` based on your workload
- Adjust TTL based on how often files change
- Monitor cache hit rate in production
