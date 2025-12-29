# Changelog

All notable changes to the Document Converter project will be documented in this file.


## [1.2.0] - 2025-12-26

### Added

#### Performance Improvements
- **Lazy Loading**: Deferred imports of heavy dependencies (PyPDF2, docx) for 3-5x faster CLI startup
  - `PyPDF2` loaded only when converting PDFs
  - `docx` library loaded only when processing DOCX files
  - Implemented `lazy_import()` utility with memoization
  - Added comprehensive unit tests for lazy loading behavior

#### CLI Enhancements
- **Interactive File Picker** (`--choose` flag)
  - Browse and select files via interactive menu using `questionary`
  - Shows file sizes and supported formats
  - Fallback to text input if `questionary` unavailable
  - Integrated into `convert` command and interactive mode

- **Drag & Drop Support**
  - Multi-file input via variadic `input_paths` argument
  - Handles paths with spaces automatically
  - Batch processing when multiple files dropped
  - Path normalization to absolute paths
  - Works seamlessly on Windows with .exe

- **Source File Deletion Flags**
  - `--delete`: Automatically remove source files after successful conversion
  - `--confirm-delete`: Prompt user before deletion
  - Safe deletion: Only removes files after verified success
  - Integrated into both `convert` and `batch` commands
  - Interactive mode prompts for deletion after each conversion

- **Dry-Run Mode** (`--dry-run` flag)
  - Simulate conversions without writing files
  - Useful for testing and UI previews
  - Format detection still runs to validate inputs
  - Hooks are called for integration testing

- **Terminal State Management**
  - Improved terminal cleanup on exit (fixes "garbled screen" on restart)
  - Proper cursor and buffer restoration after interactive mode
  - `ui.reset_terminal()` utility for clean state recovery
  - Wrapped main loop in `try/finally` for guaranteed cleanup

#### Engine Features
- **Post-Conversion Hooks**
  - `on_success(input_path, output_path)` callback after successful conversion
  - `on_failure(input_path, output_path, error)` callback on conversion failure
  - Enables custom actions like auto-deletion, notifications, metrics
  - Works with dry-run mode for testing

#### Windows Integration
- **Context Menu Support**
  - Right-click integration for supported file formats (PDF, DOCX, TXT, HTML, MD, ODT)
  - Automated installer script (`tools/windows/install_context_menu.bat`)
  - Registry template with format-specific entries
  - Interactive conversion when triggered from context menu
  - Complete documentation in `docs/windows_context_menu.md`

#### Build & Deployment
- **Nuitka Build Script**
  - Alternative compilation using Nuitka for better performance
  - Script: `tools/build_nuitka.bat`
  - Auto-fallback to PyInstaller for Windows Store Python
  - Documentation: `docs/build_nuitka.md`
  - Comparison guide (Nuitka vs PyInstaller)

- **CI/CD Workflow**
  - GitHub Actions workflow (`.github/workflows/build_and_smoke.yml`)
  - Automated unit & integration tests on push/PR
  - Windows executable build and smoke testing
  - Artifact upload for releases
  - Supports manual dispatch

#### Testing
- Added comprehensive test suites:
  - `tests/unit/test_pdf_converter_lazy.py` - Lazy loading verification
  - `tests/unit/test_lazy_loader.py` - Lazy import utility tests
  - `tests/unit/test_file_picker.py` - Interactive file picker tests
  - `tests/unit/test_arg_parsing.py` - CLI argument parsing tests
  - `tests/unit/test_engine_hooks.py` - Hook system tests
  - `tests/unit/test_ui_reset.py` - Terminal reset functionality
  - `tests/integration/test_cli_delete_flag.py` - Delete flag integration tests

### Changed
- **CLI Signature Changes** (Breaking for programmatic use)
  - `convert` command: `input_path` → `input_paths` (variadic, accepts multiple files)
  - `convert` command: `output_path` argument → `--output` option
  - Backwards compatible via command-line, but programmatic callers may need updates

- **ConversionEngine API**
  - Added optional `on_success` and `on_failure` parameters to `__init__()`
  - Added `dry_run` parameter to `convert()` method
  - Fully backwards compatible (all new parameters are optional)

### Fixed
- Path handling improvements for Windows
  - Properly handles filenames with spaces
  - Normalizes relative and absolute paths
  - Better error messages for path-related issues

- Terminal/console stability
  - Fixed "garbled screen" bug after exiting .exe on Windows
  - Proper terminal state restoration with cleanup handlers
  - Buffer flushing and cursor position restoration

### Documentation
- Updated `docs/user_guide.md` with v1.2.0 feature documentation
- Created `docs/windows_context_menu.md` for Windows integration
- Created `docs/build_nuitka.md` for Nuitka build instructions
- Enhanced `README.md` with drag & drop examples

### Migration Guide

**For CLI Users:**
- No breaking changes - all previous commands still work
- New flags are optional enhancements

**For Python API Users:**
```python
# OLD (still works)
engine.convert('input.pdf', 'output.txt')

# NEW with hooks
engine = ConversionEngine(
    on_success=lambda inp, out: print(f"✓ {inp} → {out}"),
    on_failure=lambda inp, out, err: print(f"✗ {err}")
)
engine.convert('input.pdf', 'output.txt')

# NEW with dry-run
engine.convert('input.pdf', 'output.txt', dry_run=True)
```

**For Windows .exe Users:**
- Recompile executable to get new features: `python -m PyInstaller --clean document-converter.spec`


## [1.1.2] - 2025-12-16

### Fixed

#### Format Conversion Improvements
- **Critical**: Implemented missing .docx export for MD, HTML, TXT and ODT formats
  - Refactored `MarkdownConverter` to delegate .docx output to `DOCXWriter`
  - Refactored `HTMLConverter` to delegate .docx output to `DOCXWriter`
  - Refactored `TXTConverter` to use real `DOCXWriter` instead of creating text files with .docx extension
  - Added `ODTConverter` support for .docx via intermediate HTML conversion
  - All text-based formats can now export to Microsoft Word format correctly

#### PDF Conversion Fixes
- **Critical**: Implemented real TXT to PDF conversion and prevented corrupt output
  - Refactored `TXTConverter` to delegate .pdf output to `TextToPDFConverter`
  - Prevented `TXTConverter` from writing raw text content to non-text extensions
  - Fixed issue where `convert input.txt output.pdf` created corrupt files
  - Fixed corrupt PDF output for TXT, HTML, and ODT inputs

#### Cross-Format Conversion Support
- Implemented missing conversion paths:
  - HTML to PDF/DOCX/ODT
  - Markdown to TXT/ODT
  - ODT to PDF
- Ensured robust cross-format conversion support across all formats

#### Encoding and Character Support
- **Critical**: Detected input encodings and enforced UTF-8 for all text-based formats
  - Auto-detection of input encoding (preferring UTF-8) with normalization
  - Forced UTF-8 in writers to prevent corruption of accented characters (e.g. "ñ", "á", "ü")
  - Updated encoding handling in:
    - `MarkdownConverter`
    - `HTMLConverter`
    - `DOCXWriter`
    - `ODTWriter`
    - `TXTConverter`
  - Added encoding verification test file (`repro_encoding.txt`)

#### Dependencies
- Fixed missing dependencies in `requirements.txt` for improved format support


## [1.1.1] - 2025-12-15 (Hotfix)

### Fixed
- **Critical**: Initialized converter registry in CLI commands (previously causing 'No converter registered' errors in execution)
- Fixed `AttributeError` in `info` command by adding `_get_converter` compatibility alias
- Restored `batch` command functionality by integrating centralized registry
- Fixed silent failures in interactive batch mode (PDF/DOCX support restored)

### Changed
- **Engine API**: Added `get_converter(format)` public method and `get_supported_formats()`
- **Registry**: Centralized converter registration logic in new `core.registry` module
- Refactored CLI to use `register_all_converters()` for consistency

### Migration Guide
If you are using `ConversionEngine` directly in your code (not via CLI), you must now explicitly register converters:
```python
from converter.engine import ConversionEngine
from core.registry import register_all_converters

engine = ConversionEngine()
register_all_converters(engine)  # New requirement in 1.1.1+
```


## [1.1.0] - 2024-12-12

### Added

#### User Experience Improvements
- **Interactive CLI Mode** - User-friendly menu-driven interface for standalone executable
  - Menu with 6 options: convert, batch, info, cache-stats, cache-clear, exit
  - Spanish language prompts for better accessibility
  - Input validation with helpful error messages
  - Automatic file existence checking
  - Progress indicators for batch operations
  - Confirmation dialogs for destructive operations
  
- **Format Information Display** - Clear conversion capabilities in interactive mode
  - Shows all supported format conversions with arrows (→)
  - PDF → TXT, DOCX conversions with OCR support noted
  - DOCX → PDF, HTML, Markdown, TXT
  - TXT → HTML, PDF
  - MD → HTML, PDF
  - HTML → PDF, DOCX
  - ODT → PDF, DOCX, HTML, TXT
  
- **Professional Asset Organization**
  - Created `assets/` folder for resources
  - Moved `icon.ico` to `assets/icon.ico`
  - Custom icon integrated into executable

#### Executable Enhancements
- Dual-mode execution: Interactive (double-click) + CLI (command-line)
- Auto-detection of execution mode based on arguments
- Custom icon embedded in executable
- Enhanced distribution README with both usage modes

### Changed
- Executable now defaults to interactive mode when launched without arguments
- Improved user experience for non-technical users
- Better error messages in Spanish for interactive mode

### Fixed
- Console window no longer closes immediately on double-click
- Clear screen management for better visual experience

## [1.0.0] - 2024-12-11

### Added

#### Core Features
- **Conversion Engine** - Central orchestration for document conversions
  - Format detection and converter registration
  - Support for multiple document formats (PDF, DOCX, TXT, HTML, Markdown, ODT)
  - Pluggable converter architecture
  
- **Batch Processor** - Parallel batch processing
  - Multi-worker parallel processing with configurable worker count
  - Directory scanning with recursive support
  - Progress callbacks for UI integration
  - Detailed reporting (success/failure counts)

- **Template Engine** - Custom template rendering
  - Variable interpolation (`{{ variable }}`)
  - Loop support (`{% for item in items %}`)
  - Conditional rendering (`{% if condition %}`)
  - Streaming support for large datasets
  - Memory-efficient chunk-based rendering

- **Two-Tier Caching System**
  - In-memory LRU cache (128 items default, configurable)
  - Persistent disk cache with TTL expiration
  - Cache hit rates >90% in typical workloads
  - Cache statistics and monitoring
  - Sub-millisecond memory cache lookups

- **Error Handling Framework**
  - Custom exception hierarchy (DocumentConverterError base)
  - Specific exceptions: ConversionError, FormatError, ConfigurationError, ResourceError
  - ErrorHandler with actionable recovery suggestions
  - Structured error reports with context tracking

- **Transaction Manager**
  - Automatic rollback on conversion failures
  - File backup and restoration
  - Context manager interface for safe operations
  - Support for multiple file types in single transaction

- **Worker Pool** - Parallel task execution
  - Thread-based parallel processing
  - Configurable worker count
  - Future-based result retrieval
  - Graceful shutdown handling

#### Format Converters
- **TXT Converter** - Plain text to HTML/PDF
- **Markdown Converter** - Markdown to HTML/PDF
- **HTML Converter** - HTML to PDF/DOCX
- **PDF Converter** - PDF to TXT/DOCX (with OCR support)
- **DOCX Converter** - DOCX to PDF/HTML/Markdown
- **ODT Converter** - OpenDocument to other formats

#### Processors
- **Image Processor** - Image extraction and embedding
- **OCR Processor** - Optical character recognition for scanned documents
- **Style Processor** - Style preservation during conversion
- **Table Processor** - Table structure preservation

#### CLI Interface
- `convert` - Single file conversion command
- `batch` - Batch processing command with parallel workers
- `cache-stats` - Display cache statistics
- `cache-clear` - Clear conversion cache
- Progress bars for long-running operations

#### Utilities
- **Format Detector** - Magic byte and extension-based format detection
- **Metadata Extractor** - Document metadata extraction
- **Path Manager** - Cross-platform path handling
- **Validation** - File existence, size, permissions, checksum validation
- **File Handler** - Safe file operations
- **Task Queue** - Priority-based task scheduling
- **Progress Tracker** - Progress monitoring and stats

### Documentation
- Comprehensive API Reference (700+ lines)
- User Guide with tutorials and use cases (500+ lines)
- Developer Guide with architecture and contribution guidelines (700+ lines)
- 5 complete working examples:
  - Basic conversion
  - Batch processing
  - Template rendering
  - Cache usage
  - Error handling
- Sphinx documentation setup with ReadTheDocs theme

### Testing
- **Test Coverage: 79%** (target: >80%)
- 274 total tests across all categories
- **Unit Tests** - 230+ tests for individual components
- **Integration Tests** - End-to-end workflow tests
- **Performance Tests** 
  - Speed benchmarks (cache speedup measurements)
  - Memory usage profiling
- **Stress Tests**
  - 50MB file handling
  - 500+ file batch processing
  - 100K item template rendering
  - Memory leak detection

### Performance
- **Batch Processing**: 50-200 files/sec (depending on file size and worker count)
- **Cache Speedup**: Up to 138x faster for cached conversions
- **Memory Cache**: <1ms average lookup time
- **Disk Cache**: <100ms average lookup time
- **Template Rendering**: 100K items in <5 seconds
- **Memory Efficiency**: Streaming reduces peak memory by >90%

### Infrastructure
- Git workflow with feature branches
- Automated testing with pytest
- Code coverage reporting
- Black/isort/flake8/mypy code quality tools
- Requirements split: runtime + dev dependencies

## [Unreleased]

### Planned
- Additional format converters (RTF, EPUB)
- Cloud storage integration (S3, Azure, etc...)
- Web API / REST interface
- Docker containerization
- Async/await support for I/O operations

---

## Release Notes

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for detailed release information.