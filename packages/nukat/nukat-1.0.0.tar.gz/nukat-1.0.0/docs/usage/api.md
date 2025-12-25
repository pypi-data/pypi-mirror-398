# Python API

Complete guide to using Nukat programmatically in your Python projects.

## Client Initialization

```python
from nukat import Nukat

# Default timeout (30 seconds)
client = Nukat()

# Custom timeout
client = Nukat(timeout=60)
```

## Basic Search

The `search()` method is the foundation of Nukat:

```python
results = client.search(
    query="Python programming",
    limit=20,
    offset=0
)

for result in results:
    print(result['title'])
```

### Parameters

- `query` (str): Search terms
- `limit` (int): Results per page (default: 20, max: 100)
- `offset` (int): Starting position (default: 0)
- `year_from` (int, optional): Minimum publication year
- `year_to` (int, optional): Maximum publication year
- `language` (str, optional): Language code (e.g., "eng", "pol")
- `document_type` (str, optional): Document type code (e.g., "BK" for books)
- `index` (str, optional): Search index type
- `sort_by` (str, optional): Sort order

## Convenience Methods

### Search by Author

```python
results = client.search_by_author("Smith John")

# Equivalent to:
results = client.search("Smith John", index="au")
```

### Search by Title

```python
results = client.search_by_title("Introduction to Python")

# Equivalent to:
results = client.search("Introduction to Python", index="ti")
```

### Search by ISBN

```python
results = client.search_by_isbn("978-0-123456-78-9")

# Equivalent to:
results = client.search("978-0-123456-78-9", index="nb")
```

### Search by Subject

```python
results = client.search_by_subject("Computer Science")

# Equivalent to:
results = client.search("Computer Science", index="su")
```

## Advanced Search

### Filter by Year Range

```python
# Books from 2020-2024
results = client.search(
    query="artificial intelligence",
    year_from=2020,
    year_to=2024
)
```

### Filter by Language

```python
# English publications only
results = client.search(
    query="Python",
    language="eng"
)

# Polish publications
results = client.search(
    query="Python",
    language="pol"
)
```

### Filter by Document Type

```python
# Books only
results = client.search(
    query="Python",
    document_type="BK"
)
```

### Combine Filters

```python
# Recent English books about Python
results = client.search(
    query="Python programming",
    year_from=2020,
    year_to=2024,
    language="eng",
    document_type="BK",
    limit=50
)
```

## Pagination

### Manual Pagination

```python
# First page (results 0-19)
page1 = client.search("Python", limit=20, offset=0)

# Second page (results 20-39)
page2 = client.search("Python", limit=20, offset=20)

# Third page (results 40-59)
page3 = client.search("Python", limit=20, offset=40)
```

### Automatic Pagination

Use `search_all()` to automatically retrieve all results:

```python
# Get all results (might take time)
all_results = client.search_all("popular topic")
print(f"Total: {len(all_results)} results")

# Limit total results
results = client.search_all("popular topic", max_results=500)
```

## Record Details

Get complete information for a specific record:

```python
record_id = "48685"
details = client.get_record_details(record_id)

print(details['title'])
print(details['author'])
print(details.get('isbn', 'No ISBN'))
```

## Result Structure

### Search Results

Each search result is a dictionary:

```python
{
    'id': '12345',              # Biblionumber (unique ID)
    'title': 'Book Title',
    'author': 'Author Name',
    'year': '2023',
    'publisher': 'Publisher Name',
    'place': 'City',
    'document_type': 'Text',
    'language': 'eng',
    'url': 'https://katalog.nukat.edu.pl/...'
}
```

Not all fields are always present. Use `.get()` for optional fields:

```python
for result in results:
    title = result['title']              # Always present
    author = result.get('author', 'N/A') # May be missing
    year = result.get('year', 'Unknown')
```

### Record Details

Detailed records contain more information:

```python
{
    'title': 'Complete Title',
    'author': 'Author Name (1970-)',
    'year': '2023',
    'publisher': 'Publisher',
    'place': 'City',
    'isbn': '978-0-123456-78-9',
    'pages': '350',
    'edition': '2nd ed.',
    'series': 'Series Name',
    'notes': 'Additional information',
    'subjects': ['Topic 1', 'Topic 2'],
    'document_type': 'Text',
    'language': 'eng',
    'url': 'https://katalog.nukat.edu.pl/...'
}
```

## Error Handling

Handle errors with try-except:

```python
from nukat import Nukat, NukatError

client = Nukat()

try:
    results = client.search("test query")
except NukatError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Common Errors

```python
# Connection timeout
from nukat import Nukat, NukatError

client = Nukat(timeout=5)  # Short timeout

try:
    results = client.search("query")
except NukatError as e:
    # Handle timeout or connection errors
    print(f"Failed to connect: {e}")
```

## Complete Examples

### Example 1: Recent Publications

```python
from nukat import Nukat

def find_recent_books(topic, since_year=2020):
    """Find recent books on a topic."""
    client = Nukat()
    
    results = client.search(
        query=topic,
        year_from=since_year,
        document_type="BK",
        limit=50
    )
    
    return sorted(results, key=lambda x: x.get('year', ''), reverse=True)

# Usage
books = find_recent_books("machine learning", since_year=2022)
for book in books:
    print(f"{book['title']} ({book.get('year')})")
```

### Example 2: Author Bibliography

```python
def get_author_works(author_name):
    """Get all works by an author."""
    client = Nukat()
    results = client.search_by_author(author_name)
    
    # Group by year
    by_year = {}
    for result in results:
        year = result.get('year', 'Unknown')
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(result)
    
    return by_year

# Usage
works = get_author_works("Kowalski Jan")
for year in sorted(works.keys(), reverse=True):
    print(f"\n{year}:")
    for work in works[year]:
        print(f"  - {work['title']}")
```

### Example 3: Export to CSV

```python
import csv
from nukat import Nukat

def export_search_to_csv(query, filename):
    """Export search results to CSV."""
    client = Nukat()
    results = client.search_all(query, max_results=1000)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'title', 'author', 'year', 'publisher', 'language']
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"Exported {len(results)} results to {filename}")

# Usage
export_search_to_csv("Python programming", "python_books.csv")
```

### Example 4: Fetch Multiple Records

```python
def fetch_records(record_ids):
    """Fetch details for multiple records."""
    client = Nukat()
    records = []
    
    for record_id in record_ids:
        try:
            details = client.get_record_details(record_id)
            if details:
                records.append(details)
        except NukatError:
            print(f"Failed to fetch record {record_id}")
    
    return records

# Usage
ids = ["48685", "12345", "67890"]
records = fetch_records(ids)
```

## Best Practices

1. **Reuse the client instance**:
   ```python
   client = Nukat()  # Create once
   
   # Use multiple times
   results1 = client.search("query1")
   results2 = client.search("query2")
   ```

2. **Handle missing fields gracefully**:
   ```python
   author = result.get('author', 'Unknown Author')
   ```

3. **Limit results for performance**:
   ```python
   # Good: specific limit
   results = client.search("query", limit=20)
   
   # Careful: might return thousands
   results = client.search_all("common term")
   ```

4. **Use appropriate timeouts**:
   ```python
   # For slow connections
   client = Nukat(timeout=60)
   ```

5. **Cache results when appropriate**:
   ```python
   # Avoid repeated searches for same query
   cache = {}
   
   def search_cached(query):
       if query not in cache:
           cache[query] = client.search(query)
       return cache[query]
   ```

## Next Steps

- Explore [advanced features](advanced.md)
- Check the [complete API reference](../reference.md)
- See [CLI usage](cli.md) for command-line interface
