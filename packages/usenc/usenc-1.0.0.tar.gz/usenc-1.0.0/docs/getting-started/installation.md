# Installation

## From PyPI

Install the latest stable version of CLI:

```bash
pipx install usenc
```

Or add the library to your project:

```bash
pip install usenc
```

## From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/crashoz/usenc.git
cd usenc
pip install -e .
```

## Development Installation

For development, install with dev dependencies:

```bash
pip install -e ".[dev]"
```

This includes:

- pytest - for running tests
- pytest-cov - for test coverage

## Documentation Dependencies

To build the documentation locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Then open http://127.0.0.1:8000 in your browser.

## Requirements

- Python 3.8 or higher

## Verify Installation

Test that the installation worked:

```bash
# Check CLI is available
usenc --help

# Try encoding something
echo "hello world" | usenc url
```

You should see `hello%20world` as output.
