#!/usr/bin/env python3
"""
Batch Processing Example

Demonstrates converting multiple files in parallel with progress tracking.
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from converter.batch_processor import BatchProcessor
from converter.formats.txt_converter import TXTConverter


def setup_sample_files():
    """Create sample input files for batch processing."""
    os.makedirs('input', exist_ok=True)
    
    print("Creating 20 sample files...")
    for i in range(20):
        filename = f'input/document_{i:02d}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"""Document {i}

This is sample document number {i}.

## Content Section
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
This file will be processed in batch mode.

## Details
- File number: {i}
- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Purpose: Batch processing demonstration
""")
    print(f"✓ Created 20 files in './input/'")


def example_basic_batch():
    """Basic batch processing example."""
    print("\n=== Example 1: Basic Batch Processing ===")
    
    # Create processor with 4 workers
    processor = BatchProcessor(max_workers=4)
    processor.engine.register_converter('txt', TXTConverter)
    
    # Scan directory
    os.makedirs('output', exist_ok=True)
    count = processor.scan_directory(
        input_dir='input',
        output_dir='output',
        from_format='txt',
        to_format='html'
    )
    
    print(f"Found {count} files to convert")
    
    # Process
    start = time.time()
    report = processor.process_queue()
    duration = time.time() - start
    
    # Show results
    print(f"\n✓ Batch processing completed!")
    print(f"  Total: {report.total}")
    print(f"  Success: {report.success}")
    print(f"  Failed: {report.failed}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {report.total/duration:.1f} files/sec")


def example_with_progress():
    """Batch processing with progress indicator."""
    print("\n=== Example 2: With Progress Tracking ===")
    
    processor = BatchProcessor(max_workers=6)  # More workers
    processor.engine.register_converter('txt', TXTConverter)
    
    # Clear previous output
    import shutil
    if os.path.exists('output_progress'):
        shutil.rmtree('output_progress')
    os.makedirs('output_progress')
    
    # Scan
    count = processor.scan_directory('input', 'output_progress', from_format='txt')
    print(f"Processing {count} files...")
    
    # Progress callback
    progress_counter = [0]
    def show_progress():
        progress_counter[0] += 1
        percent = (progress_counter[0] / count) * 100
        bar_length = 40
        filled = int(bar_length * progress_counter[0] / count)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f'\rProgress: [{bar}] {percent:.0f}% ({progress_counter[0]}/{count})', 
              end='', flush=True)
    
    # Process with progress
    start = time.time()
    report = processor.process_queue(progress_callback=show_progress)
    duration = time.time() - start
    
    print(f"\n✓ Completed in {duration:.2f}s")


def example_high_performance():
    """High-performance batch processing."""
    print("\n=== Example 3: High Performance (8 workers) ===")
    
    # Use 8 workers for maximum speed
    processor = BatchProcessor(max_workers=8)
    processor.engine.register_converter('txt', TXTConverter)
    
    # Process to new output
    import shutil
    if os.path.exists('output_fast'):
        shutil.rmtree('output_fast')
    os.makedirs('output_fast')
    
    processor.scan_directory('input', 'output_fast', from_format='txt')
    
    start = time.time()
    report = processor.process_queue()
    duration = time.time() - start
    
    print(f"✓ High-speed processing:")
    print(f"  Workers: 8")
    print(f"  Files: {report.total}")
    print(f"  Time: {duration:.2f}s")
    print(f"  Speed: {report.total/duration:.1f} files/sec")


def cleanup():
    """Clean up generated files."""
    import shutil
    
    dirs = ['input', 'output', 'output_progress', 'output_fast']
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
    
    print("\n✓ Cleaned up all generated files")


if __name__ == '__main__':
    print("=" * 60)
    print("BATCH PROCESSING EXAMPLES")
    print("=" * 60)
    
    try:
        setup_sample_files()
        example_basic_batch()
        example_with_progress()
        example_high_performance()
    finally:
        cleanup()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
