# Release v1.0.0 Script

This document provides instructions for creating the v1.0.0 release.

## Checklist

- [x] All code merged to main branch
- [x] All tests passing
- [x] Documentation complete
- [x] Examples tested
- [x] CHANGELOG.md created
- [x] RELEASE_NOTES.md created
- [x] Version updated in setup.py and pyproject.toml

## Creating the Git Tag

### Option 1: Using Git Command Line

```bash
# Make sure you're on the main branch
git checkout main

# Pull latest changes
git pull origin main

# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0

Document Converter v1.0.0 - First stable release

Features:
- Multi-format document conversion
- Batch processing with parallel workers
- Two-tier caching system
- Template rendering engine
- Comprehensive error handling
- 79% test coverage with 274 tests

See RELEASE_NOTES.md for full details."

# Push the tag to remote
git push origin v1.0.0
```

### Option 2: Using GitHub UI

1. Go to your repository on GitHub
2. Click on "Releases" in the right sidebar
3. Click "Draft a new release"
4. Fill in: 
- Tag version: `v1.0.0` 
- Release title: `Document Converter v1.0.0` 
- Description: Copy from RELEASE_NOTES.md
5. Attach build artifacts (optional)
6. Click "Publish release"

## Building the Package (Optional)

### Build Wheel and Source Distribution

```bash
# Install build tools
pip install build twine

# Buildpackage
python -m build

# This creates:
# - dist/document-converter-1.0.0.tar.gz (source)
# - dist/document_converter-1.0.0-py3-none-any.whl (wheel)
```

### Test Installation

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate # Linux/Mac
# OR
test_env\Scripts\activate # Windows

# Install from wheel
pip install dist/document_converter-1.0.0-py3-none-any.whl

#Test
python -c "from converter.engine import ConversionEngine; print('Success!')"

#Deactivate
deactivate
```

##Notes

- **Semantic Versioning**: v1.0.0 indicates first stable release
- **Tag Format**: Use `v` prefix (v1.0.0, not 1.0.0)
- **Annotated Tags**: Use `git tag -a` for better metadata
- **Release Notes**: Keep RELEASE_NOTES.md for each version
- **PyPI**: Publishing is optional for private projects
