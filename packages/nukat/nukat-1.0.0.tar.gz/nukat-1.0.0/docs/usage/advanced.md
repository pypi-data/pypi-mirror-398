# Advanced Features

Advanced usage patterns and techniques for power users.

## Custom Session Configuration

Customize the HTTP session for special requirements:

```python
from nukat import Nukat
import requests

client = Nukat()

# Add custom headers
client.session.headers.update({
    'User-Agent': 'MyApp/1.0',
    'Accept-Language': 'en-US,en;q=0.9'
})

# Configure retries
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
client.session.mount("https://", adapter)
```

## Parallel Searches

Perform multiple searches concurrently:

```python
from concurrent.futures import ThreadPoolExecutor
from nukat import Nukat

def parallel_search(queries, max_workers=5):
    """Execute multiple searches in parallel."""
    client = Nukat()
    
    def search_one(query):
        return query, client.search(query, limit=10)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = dict(executor.map(lambda q: search_one(q), queries))
    
    return results

# Usage
queries = ["Python", "JavaScript", "Rust", "Go"]
all_results = parallel_search(queries)

for query, results in all_results.items():
    print(f"{query}: {len(results)} results")
```

## Custom Result Parsing

Access raw HTML if needed:

```python
from nukat import Nukat
from bs4 import BeautifulSoup

client = Nukat()

# Make raw request
url = f"{client.BASE_URL}{client.SEARCH_PATH}"
params = client._build_search_params("Python", limit=20)
response = client.session.get(url, params=params, timeout=client.timeout)

# Parse custom data
soup = BeautifulSoup(response.content, 'lxml')
# Custom parsing logic here
```

## Bulk Record Retrieval

Efficiently fetch many records:

```python
from nukat import Nukat
import time

def bulk_fetch_records(record_ids, delay=0.5):
    """Fetch multiple records with rate limiting."""
    client = Nukat()
    results = []
    
    for i, record_id in enumerate(record_ids):
        print(f"Fetching {i+1}/{len(record_ids)}: {record_id}")
        
        try:
            details = client.get_record_details(record_id)
            if details:
                results.append(details)
        except Exception as e:
            print(f"  Error: {e}")
        
        # Rate limiting
        if i < len(record_ids) - 1:
            time.sleep(delay)
    
    return results

# Usage
ids = [f"{i}" for i in range(1000, 1100)]
records = bulk_fetch_records(ids)
```

## Advanced Filtering

### Complex Year Ranges

```python
from nukat import Nukat

client = Nukat()

# Decades
def search_by_decade(query, decade):
    """Search within a decade."""
    year_from = decade
    year_to = decade + 9
    return client.search(query, year_from=year_from, year_to=year_to)

# 2000s
results_2000s = search_by_decade("Python", 2000)

# 2010s
results_2010s = search_by_decade("Python", 2010)

# 2020s
results_2020s = search_by_decade("Python", 2020)
```

### Multiple Language Search

```python
def search_multiple_languages(query, languages):
    """Search across multiple languages."""
    client = Nukat()
    all_results = []
    
    for lang in languages:
        results = client.search(query, language=lang)
        # Add language marker
        for result in results:
            result['search_language'] = lang
        all_results.extend(results)
    
    return all_results

# Search in English and Polish
results = search_multiple_languages("Python", ["eng", "pol"])
```

## Result Aggregation

### Statistics

```python
from collections import Counter
from nukat import Nukat

def analyze_results(query):
    """Analyze search results statistics."""
    client = Nukat()
    results = client.search_all(query, max_results=500)
    
    # Publication years
    years = [r.get('year') for r in results if r.get('year')]
    year_counts = Counter(years)
    
    # Languages
    langs = [r.get('language') for r in results if r.get('language')]
    lang_counts = Counter(langs)
    
    # Publishers
    pubs = [r.get('publisher') for r in results if r.get('publisher')]
    pub_counts = Counter(pubs)
    
    return {
        'total': len(results),
        'years': year_counts.most_common(10),
        'languages': lang_counts.most_common(5),
        'publishers': pub_counts.most_common(10)
    }

# Usage
stats = analyze_results("machine learning")
print(f"Total results: {stats['total']}")
print(f"\nTop years: {stats['years']}")
print(f"Top languages: {stats['languages']}")
```

### Deduplication

```python
def deduplicate_results(results):
    """Remove duplicate results by title and author."""
    seen = set()
    unique = []
    
    for result in results:
        key = (
            result.get('title', '').lower(),
            result.get('author', '').lower()
        )
        if key not in seen:
            seen.add(key)
            unique.append(result)
    
    return unique

# Usage
results = client.search("Python")
unique_results = deduplicate_results(results)
```

## Data Export

### JSON Export

```python
import json
from nukat import Nukat

def export_to_json(query, filename):
    """Export results to JSON."""
    client = Nukat()
    results = client.search_all(query, max_results=1000)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(results)} results to {filename}")

export_to_json("Python programming", "results.json")
```

### Excel Export

```python
import pandas as pd
from nukat import Nukat

def export_to_excel(query, filename):
    """Export results to Excel."""
    client = Nukat()
    results = client.search_all(query, max_results=1000)
    
    df = pd.DataFrame(results)
    df.to_excel(filename, index=False)
    
    print(f"Exported {len(results)} results to {filename}")

# Requires: pip install pandas openpyxl
export_to_excel("Python", "results.xlsx")
```

## Caching

### Simple Cache

```python
from functools import lru_cache
from nukat import Nukat

class CachedNukat(Nukat):
    """Nukat client with caching."""
    
    @lru_cache(maxsize=100)
    def search_cached(self, query, limit=20):
        """Cached search."""
        return tuple(self.search(query, limit=limit))

# Usage
client = CachedNukat()

# First call: fetches from server
results1 = client.search_cached("Python")

# Second call: returns cached results
results2 = client.search_cached("Python")
```

### Persistent Cache

```python
import json
import hashlib
from pathlib import Path
from nukat import Nukat

class PersistentCachedNukat(Nukat):
    """Nukat client with disk-based cache."""
    
    def __init__(self, cache_dir="cache", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _cache_key(self, query, **kwargs):
        """Generate cache key."""
        data = f"{query}{kwargs}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def search_cached(self, query, **kwargs):
        """Search with disk cache."""
        key = self._cache_key(query, **kwargs)
        cache_file = self.cache_dir / f"{key}.json"
        
        # Check cache
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Fetch and cache
        results = self.search(query, **kwargs)
        with open(cache_file, 'w') as f:
            json.dump(results, f)
        
        return results

# Usage
client = PersistentCachedNukat()
results = client.search_cached("Python")
```

## Integration Examples

### Django Integration

```python
# models.py
from django.db import models
from nukat import Nukat

class SearchResult(models.Model):
    query = models.CharField(max_length=200)
    record_id = models.CharField(max_length=50)
    title = models.TextField()
    author = models.TextField(blank=True)
    year = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# views.py
from django.http import JsonResponse
from nukat import Nukat

def search_view(request):
    query = request.GET.get('q', '')
    client = Nukat()
    results = client.search(query, limit=20)
    
    # Save to database
    for result in results:
        SearchResult.objects.create(
            query=query,
            record_id=result.get('id', ''),
            title=result.get('title', ''),
            author=result.get('author', ''),
            year=result.get('year', '')
        )
    
    return JsonResponse({'results': results})
```

### Flask API

```python
from flask import Flask, request, jsonify
from nukat import Nukat, NukatError

app = Flask(__name__)
client = Nukat()

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    
    try:
        results = client.search(query, limit=limit)
        return jsonify({'success': True, 'results': results})
    except NukatError as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/record/<record_id>')
def get_record(record_id):
    try:
        details = client.get_record_details(record_id)
        return jsonify({'success': True, 'record': details})
    except NukatError as e:
        return jsonify({'success': False, 'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True)
```

## Performance Tips

1. **Batch requests**: Group multiple operations together
2. **Use limits**: Don't fetch more than needed
3. **Cache results**: Avoid repeated searches
4. **Connection pooling**: Reuse client instances
5. **Parallel execution**: Use threading for independent searches

## Next Steps

- Review the [API reference](../reference.md) for complete method documentation
- Check [examples](https://github.com/kupolak/nukat/tree/main/examples) in the repository
- Read about [contributing](../contributing.md) to the project
