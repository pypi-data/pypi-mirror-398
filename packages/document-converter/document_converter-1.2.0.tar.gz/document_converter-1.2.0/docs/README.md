# Building Documentation

This project uses Sphinx for generating documentation.

## Prerequisites

Install documentation requirements:

```bash
pip install -r requirements-dev.txt
```

The following packages are needed:
- sphinx
- sphinx-rtd-theme  
- m2r2 (Markdown support)

## Building HTML Documentation

From the `docs/` directory:

```bash
cd docs
sphinx-build -b html . _build/html
```

Or using the Makefile (if available):

```bash
make html
```

The generated documentation will be in `docs/_build/html/`.

Open `docs/_build/html/index.html` in your browser to view.

## Building Other Formats

### PDF

```bash
sphinx-build -b latexpdf . _build/latex
```

### Man Pages

```bash
sphinx-build -b man . _build/man
```

## Cleaning Build Files

```bash
rm -rf _build
```

## Auto-documentation

Sphinx is configured to automatically generate API documentation from Python docstrings using `sphinx.ext.autodoc`.

To regenerate API documentation:

```bash
sphinx-apidoc -f -o docs/api ../converter ../core
```

## Viewing Locally

After building, you can serve the docs locally:

```bash
cd _build/html
python -m http.server 8000
```

Visit http://localhost:8000 in your browser.

## Documentation Structure

- `index.rst` - Main entry point
- `api_reference.md` - Manual API reference
- `conf.py` - Sphinx configuration
- `api/` - Auto-generated API docs
- `_build/` - Generated documentation (git-ignored)

## Writing Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """Function description.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong

    Example:
        >>> example_function("test", 42)
        True
    """
    pass
```

## Publishing

Documentation can be published to:
- GitHub Pages
- Read the Docs
- Self-hosted server

Configure in `.readthedocs.yaml` for Read the Docs integration.
