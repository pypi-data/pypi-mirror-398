# Nukat

<p align="center">
  <img src="nukat-logo.png" alt="NUKAT Logo" width="400">
</p>

[![CI](https://github.com/kupolak/nukat/actions/workflows/ci.yml/badge.svg)](https://github.com/kupolak/nukat/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/nukat.svg)](https://pypi.org/project/nukat/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python client for the NUKAT library catalog.

## Installation

```bash
pip install nukat
```

## Usage

### Command line

```bash
nukat "Python programming"
nukat "Ireneusz Kania" --all
nukat 48685 --id
```

### Python

```python
from nukat import Nukat

client = Nukat()
results = client.search("Python programming")

for result in results:
    print(result['title'], result.get('author'))
```

## Search options

```python
# Basic search
client.search("Python", limit=50)

# Search all pages
client.search_all("Ireneusz Kania")

# Filters
client.search("AI", year_from=2020, year_to=2024, language="eng")

# Convenience methods
client.search_by_author("Kowalski Jan")
client.search_by_title("Python in practice")
client.search_by_isbn("978-83-246-1234-5")

# Get full record
client.get_record_details("48685")
```

## Development

```bash
git clone https://github.com/kupolak/nukat.git
cd nukat
pip install -e ".[dev]"
pytest
```

## License

MIT
