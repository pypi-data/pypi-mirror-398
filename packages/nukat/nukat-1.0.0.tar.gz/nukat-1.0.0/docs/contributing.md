# Contributing to Nukat

Thank you for your interest in contributing to Nukat! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and considerate of others. We want to maintain a welcoming environment for all contributors.

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/nukat.git
cd nukat
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,docs]"
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nukat --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::TestNukat::test_search_by_author
```

### Code Quality

We use several tools to maintain code quality:

#### Black (Code Formatting)

```bash
# Check formatting
black --check nukat tests

# Format code
black nukat tests
```

#### Ruff (Linting)

```bash
# Lint code
ruff check nukat tests

# Fix auto-fixable issues
ruff check --fix nukat tests
```

#### MyPy (Type Checking)

```bash
# Type check
mypy nukat
```

### Pre-commit Checks

Before committing, run:

```bash
# Format
black nukat tests

# Lint
ruff check nukat tests

# Type check
mypy nukat

# Test
pytest
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://github.com/psf/black) for formatting (line length: 100)
- Write docstrings for all public functions/classes (Google style)
- Use type hints where appropriate

### Example

```python
from typing import List, Dict, Optional


def search_records(
    query: str,
    limit: int = 20,
    year_from: Optional[int] = None
) -> List[Dict[str, str]]:
    """Search for catalog records.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        year_from: Minimum publication year filter
    
    Returns:
        List of record dictionaries containing bibliographic data
    
    Raises:
        NukatError: If the search request fails
    
    Example:
        >>> results = search_records("Python", limit=10)
        >>> len(results)
        10
    """
    # Implementation here
    pass
```

### Documentation

- Write clear docstrings using Google style
- Add examples in docstrings where helpful
- Update documentation in `docs/` when adding features
- Keep README.md up to date

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Use meaningful test names
- Mock external dependencies (HTTP requests)

Example test:

```python
def test_search_with_year_filter():
    """Test searching with year range filter."""
    client = Nukat()
    
    with patch.object(client.session, 'get') as mock_get:
        mock_get.return_value.content = b"<html>...</html>"
        
        results = client.search("Python", year_from=2020, year_to=2024)
        
        # Verify parameters
        call_args = mock_get.call_args
        assert 'year' in call_args[1]['params']
```

## Contributing Guidelines

### Adding a Feature

1. **Check existing issues** or create one to discuss the feature
2. **Write tests** for the new functionality
3. **Implement the feature** following coding standards
4. **Update documentation** in docstrings and `docs/`
5. **Run tests and quality checks**
6. **Submit a pull request**

### Fixing a Bug

1. **Create an issue** describing the bug (if not already exists)
2. **Write a test** that reproduces the bug
3. **Fix the bug**
4. **Verify the test passes**
5. **Submit a pull request** referencing the issue

### Improving Documentation

Documentation improvements are always welcome!

- Fix typos or unclear explanations
- Add examples
- Improve API documentation
- Translate content (if applicable)

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure all tests pass**: `pytest`
3. **Ensure code is formatted**: `black nukat tests`
4. **Ensure linting passes**: `ruff check nukat tests`
5. **Update documentation** if needed
6. **Write a clear PR description**:
   - What problem does it solve?
   - How does it solve it?
   - Any breaking changes?

### PR Title Format

Use conventional commit style:

- `feat: Add search by publication date`
- `fix: Handle missing author field gracefully`
- `docs: Add examples for advanced filtering`
- `test: Add tests for ISBN search`
- `refactor: Simplify result parsing logic`
- `chore: Update dependencies`

## Development Tips

### Debugging

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect raw HTML response
client = Nukat()
response = client.session.get(url, params=params)
print(response.content.decode('utf-8'))
```

### Testing Against Live API

```python
# tests/test_live.py (not committed)
from nukat import Nukat

def test_live_search():
    """Test against live NUKAT API."""
    client = Nukat()
    results = client.search("Python", limit=5)
    assert len(results) > 0
```

### Local Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Serve docs locally
mkdocs serve

# View at http://127.0.0.1:8000
```

## Project Structure

```
nukat/
├── nukat/              # Source code
│   ├── __init__.py     # Package initialization
│   ├── client.py       # Main Nukat client
│   └── main.py         # CLI entry point
├── tests/              # Test suite
│   ├── test_client.py  # Client tests
│   └── test_main.py    # CLI tests
├── docs/               # Documentation
│   ├── index.md
│   ├── getting-started/
│   ├── usage/
│   └── ...
├── .github/            # GitHub Actions
│   └── workflows/
│       └── ci.yml
├── pyproject.toml      # Project metadata and dependencies
├── mkdocs.yml          # Documentation config
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions will build and publish to PyPI

## Questions?

- 💬 [Open a discussion](https://github.com/kupolak/nukat/discussions)
- 🐛 [Report a bug](https://github.com/kupolak/nukat/issues)
- 📧 Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Nukat! 🎉
