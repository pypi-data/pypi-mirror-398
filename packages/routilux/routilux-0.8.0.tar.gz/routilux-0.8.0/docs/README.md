# Documentation

This directory contains the Sphinx documentation for routilux.

## Building the Documentation

### Prerequisites

Install the documentation dependencies:

```bash
pip install -e ".[docs]"
```

Or install Sphinx directly:

```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
```

### Building HTML Documentation

From the project root:

```bash
cd docs
make html
```

Or using sphinx-build directly:

```bash
sphinx-build -b html source build/html
```

The generated HTML documentation will be in `docs/build/html/`.

### Viewing the Documentation

Open `docs/build/html/index.html` in your browser.

### Building Other Formats

```bash
# PDF
make latexpdf

# EPUB
make epub

# Single HTML file
make singlehtml
```

## Documentation Structure

- `source/introduction.rst` - Introduction and overview
- `source/installation.rst` - Installation instructions
- `source/quickstart.rst` - Quick start guide
- `source/user_guide/` - Detailed user guides
- `source/api_reference/` - Complete API documentation
- `source/examples/` - Usage examples
- `source/changelog.rst` - Version changelog

## Updating Documentation

1. Edit the relevant `.rst` files in `source/`
2. Rebuild the documentation: `make html`
3. Check the output in `build/html/`

## Auto-generating API Documentation

The API documentation is auto-generated from docstrings using Sphinx's autodoc extension. To update:

1. Ensure docstrings are up to date in the source code
2. Rebuild: `make html`

The autodoc extension will automatically extract documentation from:
- Module docstrings
- Class docstrings
- Method/function docstrings
- Type hints

