# Nukat Documentation

Welcome to the documentation for **Nukat** - a Python client for searching and retrieving records from the NUKAT library catalog.

## What is Nukat?

Nukat is a Python library that provides a simple and intuitive interface to search Poland's NUKAT union catalog of academic and research libraries. It supports both command-line and programmatic access.

## Key Features

- **Simple API**: Easy-to-use Python interface
- **CLI Tool**: Command-line interface for quick searches
- **Advanced Filters**: Filter by year, language, document type
- **Pagination Support**: Handle large result sets efficiently
- **Record Details**: Retrieve complete bibliographic information
- **Type Hints**: Full type annotation support
- **Well Tested**: Comprehensive test coverage

## Quick Example

```python
from nukat import Nukat

client = Nukat()
results = client.search("Python programming", limit=10)

for result in results:
    print(f"{result['title']} ({result.get('year', 'N/A')})")
```

## Getting Help

- Check the [Installation Guide](getting-started/installation.md) to get started
- Read the [Quick Start](getting-started/quickstart.md) for basic usage
- Explore the [API Reference](reference.md) for detailed documentation
- See [CLI Usage](usage/cli.md) for command-line examples

## About NUKAT

NUKAT (Narodowy Uniwersalny Katalog) is Poland's union catalog containing millions of bibliographic records from academic and research libraries. This client provides programmatic access to search and retrieve this valuable data.

**Official NUKAT catalog:** [katalog.nukat.edu.pl](https://katalog.nukat.edu.pl)

## Support

If you need help or want to report a bug:

- 🐛 [Report issues](https://github.com/kupolak/nukat/issues)
- 💬 [Start a discussion](https://github.com/kupolak/nukat/discussions)
- 📖 Read the documentation

## License

Nukat is released under the [MIT License](https://opensource.org/licenses/MIT).
