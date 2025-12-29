# Example Scripts

This directory contains practical example scripts demonstrating how to use the Document Converter library.

## Available Examples

### 1. Basic Conversion (`01_basic_conversion/`)
Simple single-file conversion examples for different formats.

### 2. Batch Processing (`02_batch_processing/`)
Convert multiple files in parallel with progress tracking.

### 3. Template Rendering (`03_template_rendering/`)
Generate documents from templates and data.

### 4. Cache Usage (`04_cache_usage/`)
Speed up conversions with intelligent caching.

### 5. Error Handling (`05_error_handling/`)
Robust error handling with recovery suggestions.

### 6. Custom Converter (`06_custom_converter/`)
Create your own format converter.

## Running Examples

Each example directory contains:
- `example.py` - The main script
- `README.md` - Detailed explanation
- Sample input files (if applicable)

To run an example:

```bash
cd examples/01_basic_conversion
python example.py
```

## Requirements

Make sure you have installed the library dependencies:

```bash
pip install -r ../requirements.txt
```

## Learning Path

We recommend following the examples in order:
1. Start with basic conversion to understand the core concepts
2. Move to batch processing for handling multiple files
3. Learn templates for document generation
4. Add caching for performance
5. Implement error handling for production use
6. Create custom converters to extend functionality

## Need Help?

- Check the [User Guide](../docs/user_guide.md)
- Review the [API Reference](../docs/api_reference.md)
- See [Developer Guide](../docs/development.md) for extending the library
