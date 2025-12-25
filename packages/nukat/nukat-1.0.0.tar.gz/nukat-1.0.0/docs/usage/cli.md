# CLI Usage

The Nukat command-line interface provides quick access to catalog searches without writing Python code.

## Basic Usage

```bash
nukat [QUERY] [OPTIONS]
```

## Search Commands

### Simple Search

Search with default settings (first 10 results):

```bash
nukat "Python programming"
```

### Limit Results

Specify the number of results to return:

```bash
# Get 5 results
nukat "Python" --limit 5

# Get 50 results
nukat "artificial intelligence" --limit 50

# Maximum 100 results per search
nukat "data science" --limit 100
```

### Get All Results

Retrieve all matching results (uses pagination):

```bash
nukat "popular topic" --all
```

!!! warning
    The `--all` flag may take a while for queries with many results.

## Record Details

Get detailed information for a specific record by its ID (biblionumber):

```bash
nukat 48685 --id
```

## Search Examples

### By Author

```bash
nukat "Kowalski Jan"
nukat "Shakespeare William" --limit 20
```

### By Title

```bash
nukat "Introduction to Python" --limit 10
```

### Recent Publications

While the CLI doesn't directly support year filtering, you can add year terms to your query:

```bash
nukat "Python 2024"
nukat "artificial intelligence 2023"
```

## Output Format

### Search Results

Each result displays:

```
1. Book Title Here
   ID: 12345
   Author: Smith, John (1970-)
   Year: 2023
   URL: https://katalog.nukat.edu.pl/...

2. Another Book Title
   ID: 67890
   Author: Doe, Jane
   Year: 2022
   URL: https://katalog.nukat.edu.pl/...
```

### Record Details

When using `--id`, full record information is displayed:

```
Title: Complete Book Title
Author: Smith, John (1970-)
Year: 2023
Publisher: Publisher Name
Place: City
Document type: Text
Language: eng
Isbn: 978-0-123456-78-9
Url: https://katalog.nukat.edu.pl/...
```

## Help

View all available options:

```bash
nukat --help
```

Output:
```
usage: nukat [-h] [--all] [--limit LIMIT] [--id] query [query ...]

Client for searching NUKAT catalog

positional arguments:
  query          Search query or record ID (with --id)

optional arguments:
  -h, --help     show this help message and exit
  --all          Fetch all results
  --limit LIMIT  Number of results to display (default: 10)
  --id           Fetch record details by ID (biblionumber)
```

## Practical Examples

### Research Workflow

```bash
# 1. Initial broad search
nukat "quantum computing" --limit 5

# 2. Found interesting result with ID 12345, get details
nukat 12345 --id

# 3. Search for more by same author
nukat "Author Name" --limit 20

# 4. Get comprehensive results on topic
nukat "quantum computing" --all
```

### Finding Specific Books

```bash
# By ISBN (if known)
nukat "978-83-246-1234-5"

# By exact title phrase
nukat "Introduction to Machine Learning"

# By author and topic
nukat "Smith Python programming"
```

## Tips

1. **Use quotes** for multi-word queries:
   ```bash
   nukat "machine learning"  # Better
   nukat machine learning    # Might work differently
   ```

2. **Start with small limits** to preview results:
   ```bash
   nukat "broad topic" --limit 5
   ```

3. **Save output to file**:
   ```bash
   nukat "Python" --limit 50 > results.txt
   ```

4. **Combine with other tools**:
   ```bash
   # Count results
   nukat "Python" --all | grep "^[0-9]" | wc -l
   
   # Extract IDs
   nukat "Python" --limit 10 | grep "ID:" | cut -d: -f2
   ```

## Troubleshooting

### No results found

```bash
$ nukat "very specific query"
Searching: very specific query (first 10 results)

No results found.
```

Try broadening your search terms.

### Connection errors

```bash
Error: Connection timeout
```

Check your internet connection or try again later.

### Too many results

```bash
nukat "python" --all
Searching: python (all results)
This may take a moment...
```

The `--all` flag retrieves every result. This might take time for common terms.

## Next Steps

- Learn about the [Python API](api.md) for more control
- Explore [advanced features](advanced.md)
- Check the [API reference](../reference.md) for programmatic use
