# Document Converter v1.2.0 Release Notes

**Release Date:** December 26, 2025

## 🎉 What's New

Version 1.2.0 brings major usability improvements for Windows users, enhanced CLI workflows, and powerful new automation features!

---

## 🌟 Highlights

### ⚡ 3-5x Faster Startup
Lazy loading of heavy dependencies (PyPDF2, docx) means the CLI starts almost instantly. Libraries are only loaded when actually needed.

### 🖱️ Windows Context Menu Integration
Right-click any PDF, DOCX, TXT, HTML, MD, or ODT file and select **"Convert with DocumentConverter"** to convert it instantly. No command line required!

### 📂 Drag & Drop Support
Drop multiple files onto `document-converter.exe` and they're automatically converted. Perfect for batch operations without typing commands.

### 🧹 Smart File Deletion
New `--delete` and `--confirm-delete` flags let you automatically clean up source files after successful conversions - with safety checks.

### 🧪 Dry-Run Testing
Preview what would happen with `--dry-run` before actually converting files. Great for testing automation scripts.

---

## 🆕 New Features

### CLI Enhancements

| Feature | Flag | Description |
|---------|------|-------------|
| **Interactive Picker** | `--choose` | Browse files via interactive menu |
| **Drag & Drop** | *(automatic)* | Drop files onto .exe for instant conversion |
| **Auto-Delete Source** | `--delete` | Remove source files after success |
| **Confirm Delete** | `--confirm-delete` | Prompt before deleting |
| **Dry-Run** | `--dry-run` | Simulate conversion without writing |

### Engine Improvements

**Post-Conversion Hooks:**
```python
def celebrate(input_path, output_path):
    print(f"✨ Converted {input_path}!")
    os.remove(input_path)  # Auto-cleanup

engine = ConversionEngine(on_success=celebrate)
```

**Dry-Run API:**
```python
# Test if conversion would work
result = engine.convert('test.pdf', 'out.txt', dry_run=True)
# Returns True without writing file
```

### Windows Integration

- **Context menu** for right-click conversions
- **Registry installer** (`tools/windows/install_context_menu.bat`)
- **Format filtering** - only shows for supported files
- **Interactive mode** when triggered from Explorer

### Build Tools

- **Nuitka build script** for faster .exe compilation
- **GitHub Actions CI/CD** for automated testing
- **Smoke tests** for executable validation

---

## 📚 Usage Examples

### Interactive File Picker
```bash
document-converter.exe convert --choose
# Browse files via menu, no typing needed!
```

### Drag & Drop Batch Conversion
```bash
# Just drag 5 files onto the .exe
# Or run:
document-converter.exe convert file1.txt file2.docx file3.pdf --format pdf
```

### Auto-Delete After Conversion
```bash
# Delete source immediately
document-converter.exe convert scan.pdf output.txt --delete

# Ask before deleting
document-converter.exe convert doc.docx result.pdf --confirm-delete
```

### Test Before Converting
```bash
document-converter.exe convert bigfile.pdf output.txt --dry-run
# Output: "[DRY-RUN] Would convert bigfile.pdf to output.txt"
```

---

## 🔄 Upgrade Guide

### For CLI Users
✅ **No breaking changes** - all existing commands work exactly as before.

Just recompile to get new features:
```bash
python -m PyInstaller --clean document-converter.spec
```

### For Python API Users
All changes are backwards compatible (new parameters are optional):

**Before:**
```python
engine.convert('input.pdf', 'output.txt')
```

**After (with new features):**
```python
# Still works exactly the same
engine.convert('input.pdf', 'output.txt')

# Or use new features
engine = ConversionEngine(
    on_success=lambda i, o: print(f"✓ Done: {o}")
)
engine.convert('input.pdf', 'output.txt', dry_run=True)
```

### Windows Context Menu
New feature - requires installation:
```bash
cd tools\windows
.\install_context_menu.bat  # Run as Administrator
```

---

## 🐛 Bug Fixes

- **Path handling**: Properly handles filenames with spaces
- **Path normalization**: Converts relative paths to absolute automatically
- **Terminal stability**: Fixed "garbled screen" bug after exiting .exe on Windows
- **Better error messages** for path-related issues

---

## 📖 Documentation Updates

- **User guide** expanded with all new CLI flags
- **Windows context menu guide** (`docs/windows_context_menu.md`)
- **Nuitka build guide** (`docs/build_nuitka.md`)
- **Migration guide** in CHANGELOG.md

---

## 🔬 Testing

Added 7 new test files with 60+ new tests:
- Lazy loading verification (`test_lazy_loader.py`, `test_pdf_converter_lazy.py`)
- File picker integration
- Argument parsing
- Hook system
- Delete flag behavior
- Terminal UI reset

All tests passing ✅

---

## 🙏 Credits

Special thanks to all contributors who helped make this release possible!

---

## 📥 Installation

### From Source
```bash
git clone https://github.com/MikeAMSDev/document-converter
cd document-converter
pip install -r requirements.txt
```

### Build Executable
```bash
# PyInstaller (fast build)
python -m PyInstaller --clean document-converter.spec

# Nuitka (faster runtime)
tools\build_nuitka.bat
```

---

## 🔗 Links

- [Full Changelog](CHANGELOG.md)
- [User Guide](docs/user_guide.md)
- [GitHub Repository](https://github.com/MikeAMSDev/document-converter)
- [Issue Tracker](https://github.com/MikeAMSDev/document-converter/issues)

---

**Enjoy v1.2.0! 🚀**
