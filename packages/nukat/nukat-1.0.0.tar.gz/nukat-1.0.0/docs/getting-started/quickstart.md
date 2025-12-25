# Quick Start

This guide will help you get started with Nukat in just a few minutes.

## Basic Search

The simplest way to search the NUKAT catalog:

```python
from nukat import Nukat

client = Nukat()
results = client.search("Python programming")

for result in results:
    print(result['title'])
```

## Command Line Usage

Nukat includes a CLI tool for quick searches:

```bash
# Basic search (returns first 10 results)
nukat "Python programming"

# Get more results
nukat "Python programming" --limit 50

# Get all results
nukat "Python programming" --all
```

## Search with Filters

Filter results by publication year, language, etc.:

```python
from nukat import Nukat

client = Nukat()

# Search for recent English books about Python
results = client.search(
    query="Python",
    year_from=2020,
    year_to=2024,
    language="eng",
    limit=20
)

for result in results:
    print(f"{result['title']} ({result.get('year')})")
```

## Convenience Methods

Use specialized search methods for common queries:

```python
# Search by author
results = client.search_by_author("Smith John")

# Search by title
results = client.search_by_title("Introduction to Python")

# Search by ISBN
results = client.search_by_isbn("978-0-123456-78-9")

# Search by subject
results = client.search_by_subject("Computer Science")
```

## Get Record Details

Retrieve full details for a specific record:

```python
# Using Python API
details = client.get_record_details("48685")
print(details)

# Using CLI
nukat 48685 --id
```

## Working with Results

Search results are returned as dictionaries:

```python
results = client.search("Python", limit=5)

for result in results:
    # Available fields
    title = result.get('title')
    author = result.get('author')
    year = result.get('year')
    publisher = result.get('publisher')
    place = result.get('place')
    doc_type = result.get('document_type')
    language = result.get('language')
    url = result.get('url')
    record_id = result.get('id')  # biblionumber
    
    print(f"{title} by {author} ({year})")
```

## Pagination

Handle large result sets with pagination:

```python
# Get all results (automatically handles pagination)
all_results = client.search_all("popular query")
print(f"Found {len(all_results)} total results")

# Limit total results
results = client.search_all("popular query", max_results=500)
```

## Error Handling

Handle potential errors gracefully:

```python
from nukat import Nukat, NukatError

client = Nukat()

try:
    results = client.search("test query")
    if not results:
        print("No results found")
    else:
        for result in results:
            print(result['title'])
except NukatError as e:
    print(f"Error: {e}")
```

## Complete Example

Here's a complete example putting it all together:

```python
from nukat import Nukat, NukatError

def search_recent_books(topic, min_year=2020):
    """Search for recent books on a topic."""
    client = Nukat()
    
    try:
        results = client.search(
            query=topic,
            year_from=min_year,
            document_type="BK",  # Books only
            limit=50
        )
        
        if not results:
            print(f"No results found for '{topic}'")
            return
        
        print(f"Found {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'N/A')
            author = result.get('author', 'N/A')
            year = result.get('year', 'N/A')
            
            print(f"{i}. {title}")
            print(f"   Author: {author}")
            print(f"   Year: {year}")
            print(f"   ID: {result.get('id')}")
            print()
            
    except NukatError as e:
        print(f"Error occurred: {e}")

# Run the example
search_recent_books("artificial intelligence")
```

## Next Steps

- Learn more about [CLI usage](../usage/cli.md)
- Explore the [Python API](../usage/api.md) in depth
- Check out [advanced features](../usage/advanced.md)
- Read the [API Reference](../reference.md) for complete documentation
