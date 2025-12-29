# User Guide

Welcome to the Document Converter user guide! This guide will walk you through common use cases and provide step-by-step tutorials.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Conversions](#basic-conversions)
3. [Batch Processing](#batch-processing)
4. [Working with Templates](#working-with-templates)
5. [Using the CLI](#using-the-cli)
6. [Advanced Features](#advanced-features)
7. [Common Use Cases](#common-use-cases)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Quick Test

Verify your installation:

```bash
python -c "from converter.engine import ConversionEngine; print('Installation successful!')"
```

---

## Basic Conversions

### Converting a Single Document

**Example 1: PDF to Text**

```python
from converter.engine import ConversionEngine
from converter.formats.pdf_converter import PDFConverter

# Create engine and register converter
engine = ConversionEngine()
engine.register_converter('pdf', PDFConverter)

# Convert
success = engine.convert('document.pdf', 'document.txt')
if success:
    print("Conversion completed!")
```

**Example 2: DOCX to PDF**

```python
from converter.engine import ConversionEngine
from converter.formats.docx_converter import DOCXConverter

engine = ConversionEngine()
engine.register_converter('docx', DOCXConverter)

engine.convert('report.docx', 'report.pdf')
```

**Example 3: Markdown to HTML**

```python
from converter.engine import ConversionEngine
from converter.formats.markdown_converter import MarkdownConverter

engine = ConversionEngine()
engine.register_converter('md', MarkdownConverter)

engine.convert('README.md', 'README.html')
```

### With Caching (Faster Repeated Conversions)

```python
from converter.engine import ConversionEngine
from converter.formats.pdf_converter import PDFConverter
from core.cache_manager import CacheManager

# Setup cache
cache = CacheManager(cache_dir=".my_cache", default_ttl=7200)  # 2 hours TTL

# Create engine with cache
engine = ConversionEngine(cache_manager=cache)
engine.register_converter('pdf', PDFConverter)

# First conversion (slow)
engine.convert('large_doc.pdf', 'large_doc.txt')

# Second conversion (fast - from cache!)
engine.convert('large_doc.pdf', 'large_doc_copy.txt')
```

---

## Batch Processing

### Convert All Files in a Directory

**Example: Convert all DOCX files to PDF**

```python
from converter.batch_processor import BatchProcessor
from converter.formats.docx_converter import DOCXConverter

# Create processor
processor = BatchProcessor(max_workers=4)
processor.engine.register_converter('docx', DOCXConverter)

# Scan directory
count = processor.scan_directory(
    input_dir='./documents',
    output_dir='./output_pdfs',
    from_format='docx',
    to_format='pdf',
    recursive=True  # Include subdirectories
)

print(f"Found {count} files to convert")

# Process with progress callback
def show_progress():
    print(".", end="", flush=True)

report = processor.process_queue(progress_callback=show_progress)

print(f"\nCompleted: {report.success} succeeded, {report.failed} failed")
```

### With Custom Options

```python
processor = BatchProcessor(max_workers=8)  # More workers for speed
processor.engine.register_converter('pdf', PDFConverter)

# Pass custom options
processor.scan_directory(
    './input',
    './output',
    from_format='pdf',
    to_format='txt',
    recursive=True,
    extract_images=True,  # Custom converter option
    ocr=True              # Enable OCR for scanned PDFs
)

report = processor.process_queue()
```

### Parallel Processing with Progress Bar

```python
from converter.batch_processor import BatchProcessor
from tqdm import tqdm

processor = BatchProcessor(max_workers=8)
processor.engine.register_converter('docx', DOCXConverter)

count = processor.scan_directory('./docs', './output', from_format='docx')

with tqdm(total=count, desc="Converting") as pbar:
    def update_progress():
        pbar.update(1)
    
    report = processor.process_queue(progress_callback=update_progress)

print(f"Done! Success: {report.success}/{report.total}")
```

---

## Working with Templates

### Basic Template Rendering

**Example: Generate a report**

```python
from converter.template_engine import TemplateEngine

engine = TemplateEngine()

template = """
Report: {{ title }}
Date: {{ date }}

Summary:
{{ summary }}

Details:
{% for item in items %}
- {{ item.name }}: {{ item.value }}
{% endfor %}
"""

context = {
    "title": "Monthly Sales Report",
    "date": "2024-12-10",
    "summary": "Sales increased by 15%",
    "items": [
        {"name": "Q1", "value": "$100k"},
        {"name": "Q2", "value": "$120k"},
        {"name": "Q3", "value": "$115k"}
    ]
}

result = engine.render(template, context)
print(result)
```

### Using Pre-built Templates

```python
from converter.template_engine import TemplateEngine
import json

engine = TemplateEngine()

# Load template
with open('templates/report.txt', 'r') as f:
    template = f.read()

# Load data from JSON
with open('data/sales_data.json', 'r') as f:
    data = json.load(f)

# Render
result = engine.render(template, data)

# Save output
with open('output/report.txt', 'w') as f:
    f.write(result)
```

### Streaming Large Templates

For very large datasets, use streaming to avoid memory issues:

```python
from converter.template_engine import TemplateEngine

engine = TemplateEngine()

template = "{% for item in items %}{{ item }}\n{% endfor %}"
context = {"items": range(100000)}  # Large dataset

# Stream to file
with open('large_output.txt', 'w') as f:
    for chunk in engine.render_stream(template, context):
        f.write(chunk)
```

---

## Using the CLI

### Convert Command

```bash
# Basic conversion
python -m cli.main convert input.pdf output.txt

# With format specification
python -m cli.main convert input.docx output.pdf --format pdf

# Using templates
python -m cli.main convert --template templates/letter.txt --data data.json output.txt
```

### Batch Command

```bash
# Convert all files in directory
python -m cli.main batch ./documents ./output --from-format docx --to-format pdf

# With parallel workers
python -m cli.main batch ./input ./output --from-format txt --workers 8

# Non-recursive (current directory only)
python -m cli.main batch ./docs ./output --from-format md --no-recursive
```

### Cache Commands

```bash
# View cache statistics
python -m cli.main cache-stats

# Clear cache
python -m cli.main cache-clear
```

### New in v1.2.0: Enhanced CLI Flags

#### Interactive File Picker (`--choose`)

Launch an interactive file selector when you don't want to specify paths manually:

```bash
# Interactive mode - pick files via menu
python -m cli.main convert --choose

# Or use from executable
document-converter.exe convert --choose
```

**Features:**
- Browse files in current directory
- Select input and output files via menu
- Shows file sizes and supported formats
- Falls back to text input if `questionary` is unavailable

#### Drag & Drop Support

Drop multiple files onto the executable or pass them as arguments:

```bash
# Single file
document-converter.exe convert file.docx --output result.pdf

# Multiple files (batch conversion)
document-converter.exe convert file1.txt file2.docx file3.pdf --format pdf

# Windows drag & drop: Just drag files onto document-converter.exe
# They will be automatically converted to the prompted format
```

**Notes:**
- Paths with spaces are automatically handled
- Output files are created in the same directory as inputs
- Use `--format` to specify target format for batch operations

#### Source File Deletion (`--delete`, `--confirm-delete`)

Automatically remove source files after successful conversion:

```bash
# Delete source file immediately after conversion
document-converter.exe convert file.pdf output.txt --delete

# Ask for confirmation before deleting
document-converter.exe convert file.pdf output.txt --confirm-delete

# Delete source files in batch mode
document-converter.exe batch ./input ./output --from-format docx --delete
```

**Safety:**
- Files are only deleted after **successful** conversion
- `--confirm-delete` prompts `(yes/no)` before deletion
- Batch mode shows summary of deleted files
- Failed conversions never delete source files

#### Dry-Run Mode (`--dry-run`)

Simulate conversions without writing files - perfect for testing:

```bash
# Test if conversion would work
document-converter.exe convert test.pdf output.txt --dry-run
# Output: "[DRY-RUN] Would convert test.pdf to output.txt"

# Preview batch operations
document-converter.exe convert *.txt --format pdf --dry-run
# Shows what would be converted without creating files
```

**Use Cases:**
- Verify file formats are detected correctly
- Test conversion paths before actual processing
- Preview batch operations
- UI/automation testing

#### Windows Context Menu Integration

Right-click on supported files and convert them directly:

**Installation:**
```bash
# Navigate to tools/windows
cd tools\windows

# Run installer as Administrator
.\install_context_menu.bat
```

**Supported Formats:**
- PDF, DOCX, TXT, HTML, MD, ODT

**Usage:**
1. Right-click on a supported file
2. Select "Convert with DocumentConverter"
3. Choose output format interactively
4. File is converted in the same directory

See [Windows Context Menu Guide](windows_context_menu.md) for details.

#### Complete CLI Reference

```bash
# Convert Command Options
document-converter.exe convert [INPUT_PATHS...] [OPTIONS]

Options:
  --output, -o PATH       Output path (for single file)
  --choose, -c            Interactive file picker
  --format, -f TEXT       Target format
  --template, -t PATH     Template file path
  --ocr / --no-ocr        Enable OCR for scanned PDFs
  --lang TEXT             OCR language (default: auto)
  --verbose, -v           Enable debug logging
  --delete                Delete source after success
  --confirm-delete        Ask before deleting source
  --dry-run               Simulate without writing files
  --help                  Show help message
```


## Advanced Features

### Error Handling with Suggestions

```python
from converter.engine import ConversionEngine
from core.error_handler import ErrorHandler, ConversionError

handler = ErrorHandler()
engine = ConversionEngine()

try:
    engine.convert('document.xyz', 'output.txt')
except Exception as e:
    report = handler.handle(e)
    
    print(f"Error: {report['message']}")
    print(f"Type: {report['type']}")
    print(f"Suggestion: {report['suggestion']}")
```

### Transaction Safety (Auto-Rollback)

```python
from core.transaction import TransactionManager

with TransactionManager() as tm:
    # Register files that will be modified
    tm.register_file('important.txt')
    tm.register_file('data.json')
    
    # Perform operations
    with open('important.txt', 'w') as f:
        f.write('Critical data')
    
    with open('data.json', 'w') as f:
        f.write('{"status": "processing"}')
    
    # If an error occurs here, both files are automatically restored!
    # raise ValueError("Something went wrong")
    
# On success: changes are committed
# On error: files are automatically rolled back to original state
```

### Custom Converter Registration

```python
from converter.base.converter_base import BaseConverter
from converter.engine import ConversionEngine

class MyCustomConverter(BaseConverter):
    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        # Your custom conversion logic
        with open(input_path, 'r') as f_in:
            content = f_in.read()
        
        # Process content
        processed = content.upper()  # Example transformation
        
        with open(output_path, 'w') as f_out:
            f_out.write(processed)
        
        return True
    
    def validate_input(self, file_path: str) -> bool:
        return file_path.endswith('.txt')
    
    def extract_metadata(self, file_path: str) -> dict:
        return {"type": "custom", "converter": "MyCustomConverter"}

# Register and use
engine = ConversionEngine()
engine.register_converter('txt', MyCustomConverter)
engine.convert('input.txt', 'output.txt')
```

---

## Common Use Cases

### Use Case 1: Digital Archive Migration

**Scenario:** Migrate 1000+ legacy documents from DOCX to PDF for long-term archival.

```python
from converter.batch_processor import BatchProcessor
from converter.formats.docx_converter import DOCXConverter
from core.cache_manager import CacheManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Use cache to resume if interrupted
cache = CacheManager(cache_dir=".archive_cache", default_ttl=86400)  # 24h

# Batch processor with high parallelism
processor = BatchProcessor(max_workers=8)
processor.engine.cache_manager = cache
processor.engine.register_converter('docx', DOCXConverter)

# Scan archive
count = processor.scan_directory(
    './legacy_archive',
    './pdf_archive',
    from_format='docx',
    to_format='pdf',
    recursive=True
)

print(f"Processing {count} documents...")

# Process with error tracking
report = processor.process_queue()

# Review failures
if report.failed > 0:
    print(f"\nFailed conversions ({report.failed}):")
    for failure in report.failures:
        print(f"  - {failure['task']['input_path']}: {failure['error']}")
```

### Use Case 2: Automated Report Generation

**Scenario:** Generate weekly reports from templates and database data.

```python
from converter.template_engine import TemplateEngine
import json
from datetime import datetime

def generate_weekly_report():
    engine = TemplateEngine()
    
    # Load template
    with open('templates/weekly_report.txt', 'r') as f:
        template = f.read()
    
    # Fetch data (example: from database)
    data = {
        "week": datetime.now().strftime("%Y-W%W"),
        "generated_at": datetime.now().isoformat(),
        "metrics": [
            {"name": "Sales", "value": "$45,000", "change": "+12%"},
            {"name": "Users", "value": "1,234", "change": "+5%"},
            {"name": "Engagement", "value": "78%", "change": "+3%"}
        ],
        "highlights": [
            "Launched new feature X",
            "Resolved 45 support tickets",
            "Published 3 blog posts"
        ]
    }
    
    # Render
    report = engine.render(template, data)
    
    # Save
    filename = f"reports/weekly_{data['week']}.txt"
    with open(filename, 'w') as f:
        f.write(report)
    
    print(f"Report generated: {filename}")

# Run weekly
generate_weekly_report()
```

### Use Case 3: Bulk Document Cleanup

**Scenario:** Convert messy HTML files to clean Markdown for documentation.

```python
from converter.batch_processor import BatchProcessor
from converter.formats.html_converter import HTMLConverter

processor = BatchProcessor(max_workers=6)
processor.engine.register_converter('html', HTMLConverter)

# Convert HTML docs to Markdown
processor.scan_directory(
    './old_docs_html',
    './clean_docs_md',
    from_format='html',
    to_format='md',
    recursive=True,
    clean_html=True,  # Remove unnecessary tags
    preserve_links=True
)

report = processor.process_queue()
print(f"Cleaned {report.success} documents")
```

---

## Troubleshooting

### Problem: "No converter registered for format"

**Solution:** Register the converter before use:

```python
from converter.formats.pdf_converter import PDFConverter

engine.register_converter('pdf', PDFConverter)
```

### Problem: "FileNotFoundError"

**Solution:** Check file paths are absolute or relative to working directory:

```python
import os

input_path = os.path.abspath('document.pdf')
engine.convert(input_path, 'output.txt')
```

### Problem: Slow batch processing

**Solutions:**
1. Increase worker count: `BatchProcessor(max_workers=8)`
2. Enable caching: `engine.cache_manager = CacheManager()`
3. Process smaller batches

### Problem: Out of memory with large templates

**Solution:** Use streaming:

```python
# Instead of:
result = engine.render(template, huge_data)

# Use:
with open('output.txt', 'w') as f:
    for chunk in engine.render_stream(template, huge_data):
        f.write(chunk)
```

### Problem: Conversion fails silently

**Solution:** Enable logging and use error handler:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from core.error_handler import ErrorHandler

handler = ErrorHandler()
try:
    engine.convert('input', 'output')
except Exception as e:
    report = handler.handle(e)
    print(report['suggestion'])
```

### Getting Help

1. Check the [API Reference](api_reference.md)
2. Review example code in `examples/` directory
3. Enable debug logging to see detailed error messages
4. Check [GitHub Issues](https://github.com/your-repo/issues)

---

## Next Steps

- Read the [API Reference](api_reference.md) for detailed method documentation
- Explore [CLI Reference](cli_reference.md) for command-line usage
- Check [Configuration Guide](configuration.md) for advanced settings
- Review example scripts in the `examples/` directory

## Tips & Best Practices

1. **Always use caching** for repeated conversions
2. **Use batch processing** for multiple files instead of loops
3. **Enable transaction safety** for critical operations
4. **Monitor memory** when processing very large files
5. **Validate input files** before conversion
6. **Use error handlers** for production code
7. **Keep converters registered** to avoid re-registration overhead

Happy converting! 🚀
