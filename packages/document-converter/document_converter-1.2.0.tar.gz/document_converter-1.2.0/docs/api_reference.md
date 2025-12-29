# API Reference

Complete API reference for the Document Converter system.

## Table of Contents

- [Converter Engine](#converter-engine)
- [Batch Processor](#batch-processor)
- [Template Engine](#template-engine)
- [Cache Manager](#cache-manager)
- [Error Handler](#error-handler)
- [Transaction Manager](#transaction-manager)
- [Worker Pool](#worker-pool)
- [Format Converters](#format-converters)

---

## Converter Engine

**Module:** `converter.engine`

The `ConversionEngine` is the core component for document conversion.

### Class: `ConversionEngine`

Main interface for document conversions.

#### Constructor

```python
ConversionEngine(cache_manager: Optional[CacheManager] = None)
```

**Parameters:**
- `cache_manager` (Optional[CacheManager]): Cache manager instance for conversion caching

**Example:**
```python
from converter.engine import ConversionEngine
from core.cache_manager import CacheManager

# With caching
cache = CacheManager(cache_dir=".cache")
engine = ConversionEngine(cache_manager=cache)

# Without caching
engine = ConversionEngine()
```

#### Methods

##### `register_converter()`

Register a converter for a specific format.

```python
register_converter(format: str, converter_class: Type[BaseConverter]) -> None
```

**Parameters:**
- `format` (str): File format identifier (e.g., 'pdf', 'docx')
- `converter_class` (Type[BaseConverter]): Converter class to register

**Example:**
```python
from converter.formats.pdf_converter import PDFConverter

engine.register_converter('pdf', PDFConverter)
```

##### `convert()`

Convert a document from one format to another.

```python
convert(input_path: str, output_path: str, **kwargs) -> bool
```

**Parameters:**
- `input_path` (str): Path to input file
- `output_path` (str): Path to output file
- `**kwargs`: Additional converter-specific options

**Returns:**
- `bool`: True if conversion succeeded, False otherwise

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `ValueError`: If format is not supported

**Example:**
```python
success = engine.convert('document.pdf', 'document.docx')
if success:
    print("Conversion completed!")
```

---

## Batch Processor

**Module:** `converter.batch_processor`

Process multiple files in batch with parallel processing support.

### Class: `BatchProcessor`

Batch document processing with worker pool.

#### Constructor

```python
BatchProcessor(max_workers: int = 4)
```

**Parameters:**
- `max_workers` (int): Maximum number of parallel workers (default: 4)

**Example:**
```python
from converter.batch_processor import BatchProcessor

processor = BatchProcessor(max_workers=8)
```

#### Methods

##### `scan_directory()`

Scan directory and add files to processing queue.

```python
scan_directory(
    input_dir: str,
    output_dir: str,
    from_format: str,
    to_format: str = "pdf",
    recursive: bool = True,
    **task_options
) -> int
```

**Parameters:**
- `input_dir` (str): Input directory path
- `output_dir` (str): Output directory path
- `from_format` (str): Source format to convert from
- `to_format` (str): Target format (default: "pdf")
- `recursive` (bool): Scan subdirectories (default: True)
- `**task_options`: Additional options passed to converter

**Returns:**
- `int`: Number of files added to queue

**Example:**
```python
count = processor.scan_directory(
    './documents',
    './output',
    from_format='docx',
    to_format='pdf'
)
print(f"Added {count} files")
```

##### `process_queue()`

Process all queued conversion tasks.

```python
process_queue(progress_callback: Optional[Callable] = None) -> BatchProcessingReport
```

**Parameters:**
- `progress_callback` (Optional[Callable]): Callback function for progress updates

**Returns:**
- `BatchProcessingReport`: Report with success/failure counts

**Example:**
```python
def on_progress():
    print("Processing...")

report = processor.process_queue(progress_callback=on_progress)
print(f"Success: {report.success}, Failed: {report.failed}")
```

---

## Template Engine

**Module:** `converter.template_engine`

Custom template rendering engine with streaming support.

### Class: `TemplateEngine`

Template rendering with variables, loops, and conditionals.

#### Methods

##### `render()`

Render template with context data.

```python
render(template: str, context: Dict[str, Any]) -> str
```

**Parameters:**
- `template` (str): Template string
- `context` (Dict[str, Any]): Context dictionary

**Returns:**
- `str`: Rendered template

**Example:**
```python
from converter.template_engine import TemplateEngine

engine = TemplateEngine()
template = "Hello {{ name }}!"
result = engine.render(template, {"name": "World"})
# result: "Hello World!"
```

##### `render_stream()`

Render template as a stream of chunks (memory-efficient).

```python
render_stream(template: str, context: Dict[str, Any]) -> Generator[str, None, None]
```

**Parameters:**
- `template` (str): Template string
- `context` (Dict[str, Any]): Context dictionary

**Yields:**
- `str`: Template chunks

**Example:**
```python
template = "{% for i in items %}{{ i }}\n{% endfor %}"
context = {"items": range(100000)}

with open('output.txt', 'w') as f:
    for chunk in engine.render_stream(template, context):
        f.write(chunk)
```

**Template Syntax:**

Variables:
```
{{ variable_name }}
{{ object.property }}
```

Loops:
```
{% for item in items %}
    {{ item }}
{% endfor %}
```

Conditionals:
```
{% if condition %}
    Text if true
{% endif %}
```

---

## Cache Manager

**Module:** `core.cache_manager`

Manages conversion result caching with two-tier architecture.

### Class: `CacheManager`

Two-tier caching: in-memory LRU + disk persistence.

#### Constructor

```python
CacheManager(
    cache_dir: str = ".cache",
    default_ttl: int = 3600 * 24,
    memory_cache_size: int = 128
)
```

**Parameters:**
- `cache_dir` (str): Cache directory (default: ".cache")
- `default_ttl` (int): Time-to-live in seconds (default: 24 hours)
- `memory_cache_size` (int): In-memory cache size (default: 128)

**Example:**
```python
from core.cache_manager import CacheManager

cache = CacheManager(
    cache_dir="./my_cache",
    default_ttl=7200,  # 2 hours
    memory_cache_size=256
)
```

#### Methods

##### `get()`

Retrieve cached conversion result.

```python
get(input_path: str, options: Dict[str, Any] = None) -> Optional[str]
```

**Parameters:**
- `input_path` (str): Original input file path
- `options` (Dict[str, Any]): Conversion options used

**Returns:**
- `str | None`: Path to cached file, or None if not found

**Example:**
```python
cached_path = cache.get('document.pdf')
if cached_path:
    print(f"Cache hit: {cached_path}")
```

##### `set()`

Store conversion result in cache.

```python
set(
    input_path: str,
    output_path: str,
    options: Dict[str, Any] = None,
    ttl: Optional[int] = None
) -> None
```

**Parameters:**
- `input_path` (str): Original input file path
- `output_path` (str): Conversion result path
- `options` (Dict[str, Any]): Conversion options
- `ttl` (Optional[int]): Custom TTL in seconds

**Example:**
```python
cache.set('document.pdf', 'document.docx', ttl=3600)
```

##### `clear()`

Clear all cached entries.

```python
clear() -> None
```

##### `get_stats()`

Get cache statistics.

```python
get_stats() -> Dict[str, Any]
```

**Returns:**
- Dict with keys: `items`, `total_size_bytes`

---

## Error Handler

**Module:** `core.error_handler`

Centralized error handling with custom exceptions and recovery suggestions.

### Custom Exceptions

#### `DocumentConverterError`

Base exception for all converter errors.

```python
class DocumentConverterError(Exception)
```

#### `ConversionError`

Raised when conversion fails.

```python
class ConversionError(DocumentConverterError)
```

#### `FormatError`

Raised for unsupported or invalid formats.

```python
class FormatError(DocumentConverterError)
```

#### `ConfigurationError`

Raised for configuration issues.

```python
class ConfigurationError(DocumentConverterError)
```

#### `ResourceError`

Raised for resource access issues.

```python
class ResourceError(DocumentConverterError)
```

### Class: `ErrorHandler`

Error processing and reporting.

#### Methods

##### `handle()`

Process an exception and generate error report.

```python
handle(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
```

**Parameters:**
- `error` (Exception): Exception to handle
- `context` (Optional[Dict]): Additional context

**Returns:**
- Dict with keys: `type`, `message`, `suggestion`, `context`

**Example:**
```python
from core.error_handler import ErrorHandler, ConversionError

handler = ErrorHandler()

try:
    raise ConversionError("Failed to convert file")
except Exception as e:
    report = handler.handle(e)
    print(report['message'])
    print(f"Suggestion: {report['suggestion']}")
```

---

## Transaction Manager

**Module:** `core.transaction.py`

File system transaction management with automatic rollback.

### Class: `TransactionManager`

Context manager for safe file operations.

#### Usage

```python
with TransactionManager() as tm:
    tm.register_file('output.txt')
    # Perform file operations
    with open('output.txt', 'w') as f:
        f.write('data')
    # If exception occurs, file is deleted automatically
```

#### Methods

##### `register_file()`

Register a file for transaction tracking.

```python
register_file(file_path: str) -> None
```

**Parameters:**
- `file_path` (str): Path to file to track

**Example:**
```python
from core.transaction import TransactionManager

with TransactionManager() as tm:
    tm.register_file('important.txt')
    
    # If file exists, backup is created
    # If new file, will be deleted on rollback
    with open('important.txt', 'w') as f:
        f.write('Critical data')
    
    # Simulate error - file will be restored/removed
    raise ValueError("Error!")
```

---

## Worker Pool

**Module:** `core.worker_pool`

Parallel task execution with retries and metrics.

### Class: `WorkerPool`

Thread pool for parallel task processing.

#### Constructor

```python
WorkerPool(max_workers: int = 4)
```

**Parameters:**
- `max_workers` (int): Maximum concurrent workers

#### Methods

##### `submit()`

Submit a task for execution.

```python
submit(func: Callable, *args, **kwargs) -> Future
```

**Parameters:**
- `func` (Callable): Function to execute
- `*args`: Positional arguments
- `**kwargs`: Keyword arguments

**Returns:**
- `Future`: Future object for result retrieval

**Example:**
```python
from core.worker_pool import WorkerPool

def process_file(path):
    return f"Processed: {path}"

pool = WorkerPool(max_workers=4)
future = pool.submit(process_file, 'file.txt')
result = future.result()
pool.shutdown()
```

---

## Format Converters

### Base Converter

**Module:** `converter.base.converter_base`

All converters inherit from `BaseConverter`.

#### Methods to Implement

```python
class BaseConverter:
    def convert(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Convert document."""
        pass
    
    def validate_input(self, file_path: str) -> bool:
        """Validate input file."""
        pass
    
    def extract_metadata(self, file_path: str) -> dict:
        """Extract file metadata."""
        pass
```

### Available Converters

#### PDF Converter
- **Module:** `converter.formats.pdf_converter`
- **Class:** `PDFConverter`
- **Supports:** PDF → TXT, PDF → DOCX

#### DOCX Converter
- **Module:** `converter.formats.docx_converter`
- **Class:** `DOCXConverter`
- **Supports:** DOCX → PDF, DOCX → HTML, DOCX → MD

#### TXT Converter
- **Module:** `converter.formats.txt_converter`
- **Class:** `TXTConverter`
- **Supports:** TXT → HTML, TXT → PDF

#### Markdown Converter
- **Module:** `converter.formats.markdown_converter`
- **Class:** `MarkdownConverter`
- **Supports:** MD → HTML, MD → PDF

#### HTML Converter
- **Module:** `converter.formats.html_converter`
- **Class:** `HTMLConverter`
- **Supports:** HTML → PDF, HTML → DOCX

---

## Quick Start Examples

### Basic Conversion

```python
from converter.engine import ConversionEngine
from converter.formats.pdf_converter import PDFConverter

engine = ConversionEngine()
engine.register_converter('pdf', PDFConverter)
engine.convert('document.pdf', 'document.txt')
```

### Batch Processing with Cache

```python
from converter.batch_processor import BatchProcessor
from core.cache_manager import CacheManager

cache = CacheManager()
processor = BatchProcessor(max_workers=8)
processor.engine.cache_manager = cache

processor.scan_directory('./docs', './output', from_format='docx')
report = processor.process_queue()
```

### Template Rendering

```python
from converter.template_engine import TemplateEngine
import json

with open('data.json') as f:
    data = json.load(f)

engine = TemplateEngine()
with open('template.txt') as f:
    template = f.read()

result = engine.render(template, data)
print(result)
```

### Error Handling

```python
from core.error_handler import ErrorHandler, ConversionError

handler = ErrorHandler()

try:
    # Your conversion code
    pass
except Exception as e:
    report = handler.handle(e)
    print(f"Error: {report['message']}")
    print(f"Fix: {report['suggestion']}")
```

---

## See Also

- [User Guide](user_guide.md)
- [Configuration](configuration.md)
- [CLI Reference](cli_reference.md)
