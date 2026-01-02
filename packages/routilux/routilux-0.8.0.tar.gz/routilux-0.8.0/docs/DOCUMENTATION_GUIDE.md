# Documentation Guide

This guide explains how to build and maintain the Sphinx documentation for routilux.

## Quick Start

### Building Documentation

1. Install documentation dependencies:
   ```bash
   pip install -e ".[docs]"
   # or
   pip install -r requirements-docs.txt
   ```

2. Build HTML documentation:
   ```bash
   cd docs
   make html
   ```

3. View the documentation:
   ```bash
   # Open docs/build/html/index.html in your browser
   ```

## Documentation Structure

```
docs/
├── Makefile              # Makefile for building docs
├── make.bat              # Windows batch file for building docs
├── README.md             # Documentation build instructions
└── source/               # Source files for documentation
    ├── conf.py           # Sphinx configuration
    ├── index.rst         # Main documentation index
    ├── introduction.rst  # Introduction and overview
    ├── installation.rst  # Installation guide
    ├── quickstart.rst    # Quick start guide
    ├── changelog.rst     # Version changelog
    ├── user_guide/       # User guides
    │   ├── index.rst
    │   ├── routines.rst
    │   ├── flows.rst
    │   ├── connections.rst
    │   ├── state_management.rst
    │   ├── error_handling.rst
    │   └── serialization.rst
    ├── api_reference/    # API documentation
    │   ├── index.rst
    │   ├── flow.rst
    │   ├── routine.rst
    │   ├── event.rst
    │   ├── slot.rst
    │   ├── connection.rst
    │   ├── job_state.rst
    │   ├── error_handler.rst
    │   └── execution_tracker.rst
    └── examples/         # Usage examples
        ├── index.rst
        ├── basic_example.rst
        ├── data_processing.rst
        ├── error_handling_example.rst
        └── state_management_example.rst
```

## Building Documentation

### HTML (Default)

```bash
cd docs
make html
```

Output: `docs/build/html/index.html`

### Other Formats

```bash
# PDF (requires LaTeX)
make latexpdf

# EPUB
make epub

# Single HTML file
make singlehtml

# All formats
make all
```

### Clean Build

```bash
make clean
```

## Writing Documentation

### RST Format

Documentation is written in reStructuredText (RST). Key syntax:

- **Headers**: Use `=` for section titles, `-` for subsections
- **Code blocks**: Use `.. code-block:: python` or `::`
- **Links**: Use `:doc:` for internal links, `:ref:` for references
- **API docs**: Use `.. automodule::` for auto-generated API docs

### Adding New Documentation

1. Create a new `.rst` file in the appropriate directory
2. Add it to the relevant `index.rst` using `.. toctree::`
3. Rebuild: `make html`

### Updating API Documentation

API documentation is auto-generated from docstrings. To update:

1. Ensure docstrings are up to date in source code
2. Rebuild: `make html`

The autodoc extension extracts:
- Module docstrings
- Class docstrings
- Method/function docstrings
- Type hints

## Examples

Examples are located in `examples/` and referenced in documentation using:

```rst
.. literalinclude:: ../../../examples/basic_example.py
   :language: python
   :linenos:
```

## Configuration

Sphinx configuration is in `docs/source/conf.py`. Key settings:

- **Extensions**: autodoc, napoleon, viewcode, etc.
- **Theme**: sphinx_rtd_theme (Read the Docs theme)
- **Autodoc**: Auto-generates API docs from docstrings
- **Napoleon**: Supports Google/NumPy style docstrings

## Publishing

### Read the Docs

The project includes `.readthedocs.yml` for Read the Docs integration.

1. Connect repository to Read the Docs
2. Configure build settings (already in `.readthedocs.yml`)
3. Documentation will auto-build on commits

### Manual Publishing

1. Build documentation: `make html`
2. Upload `docs/build/html/` to your web server

## Best Practices

1. **Keep docstrings up to date**: API docs are auto-generated
2. **Use examples**: Include practical examples in documentation
3. **Cross-reference**: Link related sections using `:doc:` and `:ref:`
4. **Version control**: Keep documentation in sync with code
5. **Test examples**: Ensure all code examples work correctly

## Troubleshooting

### Import Errors

If you see import errors when building:

1. Ensure Routilux is installed: `pip install -e .`
2. Check `autodoc_mock_imports` in `conf.py`
3. Install missing dependencies

### Missing Modules

If modules aren't documented:

1. Check `sys.path` in `conf.py`
2. Verify module structure
3. Check autodoc settings

### Build Errors

If build fails:

1. Check RST syntax: `make clean && make html`
2. Verify all referenced files exist
3. Check for circular references in toctree

