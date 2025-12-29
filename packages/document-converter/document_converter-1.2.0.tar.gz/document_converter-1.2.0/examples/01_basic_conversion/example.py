#!/usr/bin/env python3
"""
Basic Conversion Example

Demonstrates simple single-file conversions between different formats.
"""
import sys
import os

# Add parent directory to path to import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from converter.engine import ConversionEngine
from converter.formats.txt_converter import TXTConverter
from converter.formats.markdown_converter import MarkdownConverter


def example_txt_to_html():
    """Convert a text file to HTML."""
    print("\n=== Example 1: TXT to HTML ===")
    
    # Create sample input file
    with open('sample.txt', 'w', encoding='utf-8') as f:
        f.write("""# Welcome to Document Converter

This is a sample text file that will be converted to HTML.

## Features

- Easy to use
- Fast conversions
- Multiple formats supported

Visit our website for more information!
""")
    
    # Setup engine and converter
    engine = ConversionEngine()
    engine.register_converter('txt', TXTConverter)
    
    # Convert
    success = engine.convert('sample.txt', 'sample.html')
    
    if success:
        print("✓ Conversion successful!")
        print(f"Output: {os.path.abspath('sample.html')}")
        
        # Show output
        with open('sample.html', 'r', encoding='utf-8') as f:
            print("\nOutput preview:")
            print("-" * 50)
            print(f.read()[:200] + "...")
    else:
        print("✗ Conversion failed!")


def example_markdown_to_html():
    """Convert Markdown to HTML."""
    print("\n=== Example 2: Markdown to HTML ===")
    
    # Create sample Markdown
    with open('sample.md', 'w', encoding='utf-8') as f:
        f.write("""# Document Converter

## Quick Start

Converting documents is easy:

```python
from converter.engine import ConversionEngine

engine = ConversionEngine()
engine.convert('input.pdf', 'output.txt')
```

## Supported Formats

- PDF
- DOCX  
- HTML
- Markdown
- TXT

**Ready to get started?** Download now!
""")
    
    # Setup and convert
    engine = ConversionEngine()
    engine.register_converter('md', MarkdownConverter)
    
    success = engine.convert('sample.md', 'sample_from_md.html')
    
    if success:
        print("✓ Markdown converted to HTML!")
        print(f"Output: {os.path.abspath('sample_from_md.html')}")
    else:
        print("✗ Conversion failed!")


def example_with_error_handling():
    """Example with proper error handling."""
    print("\n=== Example 3: With Error Handling ===")
    
    engine = ConversionEngine()
    engine.register_converter('txt', TXTConverter)
    
    try:
        # Try to convert a non-existent file
        success = engine.convert('nonexistent.txt', 'output.html')
        if not success:
            print("✗ Conversion returned False")
    except FileNotFoundError as e:
        print(f"✓ Caught expected error: {e}")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")


def cleanup():
    """Clean up generated files."""
    files = ['sample.txt', 'sample.html', 'sample.md', 'sample_from_md.html']
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    print("\n✓ Cleaned up generated files")


if __name__ == '__main__':
    print("=" * 60)
    print("BASIC CONVERSION EXAMPLES")
    print("=" * 60)
    
    try:
        example_txt_to_html()
        example_markdown_to_html()
        example_with_error_handling()
    finally:
        cleanup()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
