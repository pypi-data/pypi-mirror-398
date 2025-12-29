# Batch Processing Example

This example shows how to convert multiple files in parallel.

## What This Example Shows

- Setting up BatchProcessor with multiple workers
- Scanning directories for files to convert
- Processing files in parallel
- Tracking progress with callbacks
- Performance optimization with worker count

## Files

- `example.py` - Batch processing demonstrations

## Examples Included

### Example 1: Basic Batch
Converts 20 files using 4 parallel workers.

### Example 2: With Progress Tracking
Shows a progress bar during conversion.

### Example 3: High Performance
Uses 8 workers for maximum throughput.

## Running the Example

```bash
cd examples/02_batch_processing
python example.py
```

## Expected Output

The script will:
1. Create 20 sample text files
2. Convert them in parallel (3 different ways)
3. Show performance metrics
4. Clean up generated files

## Key Concepts

### Creating a Batch Processor

```python
processor = BatchProcessor(max_workers=4)
processor.engine.register_converter('txt', TXTConverter)
```

The `max_workers` parameter controls parallelism:
- CPU-bound: use `os.cpu_count()`
- I/O-bound: use `os.cpu_count() * 2`

### Scanning Directories

```python
count = processor.scan_directory(
    input_dir='documents',
    output_dir='output',
    from_format='txt',
    to_format='html',
    recursive=True  # Include subdirectories
)
```

### Processing with Progress

```python
def show_progress():
    print(".", end="", flush=True)

report = processor.process_queue(progress_callback=show_progress)
```

The callback is called after each file is processed.

### Analyzing Results

```python
print(f"Success: {report.success}")
print(f"Failed: {report.failed}")
print(f"Total: {report.total}")
```

## Performance Tips

1. **Adjust worker count** based on your workload:
   - More workers = faster for I/O-bound tasks
   - Too many workers = overhead and diminishing returns

2. **Monitor throughput**:
   - Typical: 50-100 files/sec for small files
   - Large files: 5-10 files/sec

3. **Use progress callbacks** sparingly:
   - Frequent callbacks can slow processing
   - Update UI every N files instead of every file

## Next Steps

- Try with your own files
- Experiment with different worker counts
- Add caching (see `04_cache_usage/`)
- Implement error handling for failed conversions
