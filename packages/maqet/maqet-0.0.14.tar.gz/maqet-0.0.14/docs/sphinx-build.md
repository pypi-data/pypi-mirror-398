# Building Sphinx Documentation

This directory contains Sphinx configuration for generating API documentation from MAQET's Python docstrings.

## Quick Start

### Install Dependencies

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Or install dev dependencies (includes docs)
pip install -e ".[dev]"
```

### Build HTML Documentation

```bash
cd docs
make html
```

Documentation will be generated in `docs/_build/html/`. Open `docs/_build/html/index.html` in a browser.

### Clean Build Artifacts

```bash
cd docs
make clean
```

## Documentation Structure

### Configuration

- `conf.py` - Sphinx configuration
  - autodoc extension for auto-generating from docstrings
  - napoleon extension for Google-style docstrings
  - myst_parser for markdown support
  - alabaster theme (default)

### Source Files

- `index.rst` - Main documentation page
- `api/index.rst` - Core API reference
- `api/types.rst` - Type definitions
- `api/exceptions.rst` - Exception hierarchy
- `api/modules.rst` - Additional modules
- `examples.rst` - Configuration examples

### Existing Markdown Docs

The Sphinx setup integrates with existing markdown documentation:

- User guides (user-guide/)
- Development guides (development/)
- Architecture docs (architecture/)
- Migration guides (MIGRATION*.md)

## Customization

### Theme

To use RTD theme instead of alabaster, edit `conf.py`:

```python
html_theme = "sphinx_rtd_theme"
```

### Adding New Modules

Add new autodoc directives to `api/modules.rst`:

```rst
New Module
----------

.. automodule:: maqet.new_module
   :members:
   :undoc-members:
   :show-inheritance:
```

## Troubleshooting

### Module Import Errors

If Sphinx cannot import modules:

```bash
# Ensure maqet is installed in development mode
pip install -e .
```

### Missing Dependencies

```bash
# Reinstall documentation dependencies
pip install -e ".[docs]"
```

### Build Warnings

Clean build artifacts and rebuild:

```bash
make clean
make html
```

## See Also

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [autodoc Extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
- [Napoleon Extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [MyST Parser](https://myst-parser.readthedocs.io/)
