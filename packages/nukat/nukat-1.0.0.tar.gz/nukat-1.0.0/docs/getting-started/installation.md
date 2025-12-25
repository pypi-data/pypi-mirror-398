# Installation

## Requirements

Nukat requires Python 3.8 or higher.

## Install from PyPI

Once published, you can install Nukat using pip:

```bash
pip install nukat
```

## Install from Source

### For Users

To install the latest version from GitHub:

```bash
pip install git+https://github.com/kupolak/nukat.git
```

### For Developers

If you want to contribute or modify the code:

1. **Clone the repository**

```bash
git clone https://github.com/kupolak/nukat.git
cd nukat
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode**

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with all development dependencies including:
- pytest (testing)
- pytest-cov (coverage)
- black (code formatting)
- ruff (linting)
- mypy (type checking)

## Install Documentation Tools

To build and serve the documentation locally:

```bash
pip install -e ".[docs]"
```

## Verify Installation

Check that Nukat is installed correctly:

```bash
# Check version
python -c "import nukat; print(nukat.__version__)"

# Try the CLI
nukat --help
```

## Dependencies

Nukat depends on:

- **requests** (>= 2.31.0) - HTTP library
- **beautifulsoup4** (>= 4.12.0) - HTML parsing
- **lxml** (>= 4.9.0) - XML/HTML parser

These are automatically installed when you install Nukat.

## Troubleshooting

### ImportError: No module named 'nukat'

Make sure you've installed the package:

```bash
pip install nukat
```

### lxml installation fails

On some systems, lxml requires additional build tools. Try:

```bash
# Ubuntu/Debian
sudo apt-get install libxml2-dev libxslt1-dev python3-dev

# macOS
brew install libxml2 libxslt

# Then install nukat again
pip install nukat
```

### Python version too old

Nukat requires Python 3.8+. Check your version:

```bash
python --version
```

If needed, install a newer Python version from [python.org](https://www.python.org/downloads/).

## Next Steps

Now that you have Nukat installed, check out the [Quick Start Guide](quickstart.md) to learn how to use it!
