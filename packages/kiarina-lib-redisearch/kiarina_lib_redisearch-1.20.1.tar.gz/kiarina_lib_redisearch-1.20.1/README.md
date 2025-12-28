# kiarina-lib-redisearch

A comprehensive Python client library for [RediSearch](https://redis.io/docs/interact/search-and-query/) with advanced configuration management, schema definition, and both full-text and vector search capabilities.

## Features

- **Full-Text Search**: Advanced text search with stemming, phonetic matching, and fuzzy search
- **Vector Search**: Similarity search using FLAT and HNSW algorithms with multiple distance metrics
- **Schema Management**: Type-safe schema definition with automatic migration support
- **Configuration Management**: Flexible configuration using `pydantic-settings-manager`
- **Sync & Async**: Support for both synchronous and asynchronous operations
- **Advanced Filtering**: Intuitive query builder with type-safe filter expressions
- **Index Management**: Complete index lifecycle management (create, migrate, reset, drop)
- **Type Safety**: Full type hints and Pydantic validation throughout

## Installation

```bash
pip install kiarina-lib-redisearch
```

## Quick Start

### Basic Usage (Sync)

```python
import redis
from kiarina.lib.redisearch import create_redisearch_client, settings_manager

# Define your schema (part of your application code)
schema = [
    {"type": "tag", "name": "category"},
    {"type": "text", "name": "title"},
    {"type": "numeric", "name": "price", "sortable": True},
    {"type": "vector", "name": "embedding", "algorithm": "FLAT", "dims": 1536}
]

# Configure settings (infrastructure configuration)
settings_manager.user_config = {
    "default": {
        "key_prefix": "products:",
        "index_name": "products_index"
    }
}

# Create Redis connection (decode_responses=False is required)
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=False)

# Create RediSearch client with schema
client = create_redisearch_client(
    "default",
    field_dicts=schema,
    redis=redis_client,
)

# Create index
client.create_index()

# Add documents
client.set({
    "category": "electronics",
    "title": "Wireless Headphones",
    "price": 99.99,
    "embedding": [0.1, 0.2, 0.3, ...]
}, id="product_1")

# Full-text search
results = client.find(
    filter=[["category", "==", "electronics"]],
    return_fields=["title", "price"]
)

# Vector similarity search
results = client.search(
    vector=[0.1, 0.2, 0.3, ...],
    limit=10
)
```

### Async Usage

```python
import redis.asyncio
from kiarina.lib.redisearch.asyncio import create_redisearch_client

schema = [
    {"type": "text", "name": "title"},
    {"type": "numeric", "name": "price", "sortable": True}
]

async def main():
    redis_client = redis.asyncio.Redis(host="localhost", port=6379, decode_responses=False)
    client = create_redisearch_client(field_dicts=schema, redis=redis_client)
    
    await client.create_index()
    await client.set({"title": "Example", "price": 99.99}, id="doc_1")
    results = await client.find()
```

## Schema Definition

Define your search schema with type-safe field definitions:

### Field Types

```python
# Tag field
{"type": "tag", "name": "category", "separator": ",", "sortable": True}

# Text field
{"type": "text", "name": "description", "weight": 2.0, "no_stem": False}

# Numeric field
{"type": "numeric", "name": "price", "sortable": True}

# Vector field (FLAT)
{
    "type": "vector",
    "name": "embedding",
    "algorithm": "FLAT",
    "dims": 1536,
    "datatype": "FLOAT32",
    "distance_metric": "COSINE"
}

# Vector field (HNSW)
{
    "type": "vector",
    "name": "embedding",
    "algorithm": "HNSW",
    "dims": 1536,
    "datatype": "FLOAT32",
    "distance_metric": "COSINE",
    "m": 16,
    "ef_construction": 200
}
```

## Configuration

### Environment Variables

```bash
export KIARINA_LIB_REDISEARCH_KEY_PREFIX="myapp:"
export KIARINA_LIB_REDISEARCH_INDEX_NAME="main_index"
export KIARINA_LIB_REDISEARCH_PROTECT_INDEX_DELETION="true"
```

### YAML Configuration

```yaml
# config.yaml
redisearch:
  development:
    key_prefix: "dev:"
    index_name: "dev_index"
    protect_index_deletion: false
  production:
    key_prefix: "prod:"
    index_name: "prod_index"
    protect_index_deletion: true
```

```python
import yaml
from kiarina.lib.redisearch import settings_manager

with open("config.yaml") as f:
    config = yaml.safe_load(f)
    settings_manager.user_config = config["redisearch"]

settings_manager.active_key = "production"
```

## API Reference

### Index Operations

```python
# Check if index exists
exists = client.exists_index()

# Create index
client.create_index()

# Drop index
client.drop_index(delete_documents=True)

# Reset index (drop and recreate)
client.reset_index()

# Migrate index (auto-detect schema changes)
client.migrate_index()

# Get index information
info = client.get_info()
```

### Document Operations

```python
# Set document
client.set({"title": "Example", "price": 99.99}, id="doc_1")

# Get document
doc = client.get("doc_1")

# Delete document
client.delete("doc_1")

# Get Redis key
key = client.get_key("doc_1")  # Returns "prefix:doc_1"
```

### Search Operations

```python
# Count documents
count_result = client.count(filter=[["category", "==", "electronics"]])

# Full-text search
results = client.find(
    filter=[["category", "==", "electronics"], ["price", "<", 500]],
    sort_by="price",
    sort_desc=False,
    offset=0,
    limit=20,
    return_fields=["title", "price"]
)

# Vector similarity search
results = client.search(
    vector=[0.1, 0.2, ...],
    filter=[["category", "==", "electronics"]],
    offset=0,
    limit=10,
    return_fields=["title", "distance"]
)
```

### Advanced Filtering

```python
import kiarina.lib.redisearch_filter as rf

# Using filter API
filter_expr = (
    (rf.Tag("category") == "electronics") &
    (rf.Numeric("price") < 500) &
    (rf.Text("title") % "*wireless*")
)
results = client.find(filter=filter_expr)

# Using condition lists
conditions = [
    ["category", "==", "electronics"],
    ["price", "<", 500],
    ["title", "like", "*wireless*"]
]
results = client.find(filter=conditions)
```

### Filter Operators

**Tag filters:**
- `==` or `in`: Match tags
- `!=` or `not in`: Exclude tags

**Numeric filters:**
- `==`, `!=`, `>`, `<`, `>=`, `<=`: Numeric comparisons

**Text filters:**
- `==`: Exact match
- `!=`: Not equal
- `%` or `like`: Pattern matching (wildcards, fuzzy search)

## Schema Migration

```python
# Update schema in code
new_schema = [
    {"type": "tag", "name": "category"},
    {"type": "text", "name": "title"},
    {"type": "numeric", "name": "rating", "sortable": True},  # New field
]

# Create client with new schema
client = create_redisearch_client(field_dicts=new_schema, redis=redis_client)

# Migrate (auto-detects changes and recreates index)
client.migrate_index()
```

## Testing

### Prerequisites

- Python 3.12+
- Redis with RediSearch module
- Docker (for running Redis in tests)

### Running Tests

```bash
# Start Redis with RediSearch
docker compose up -d redis

# Run all tests for this package
mise run package:test kiarina-lib-redisearch

# Run with coverage
mise run package:test kiarina-lib-redisearch --coverage
```

## Dependencies

- [redis](https://github.com/redis/redis-py) - Redis client for Python
- [numpy](https://numpy.org/) - Numerical computing (for vector operations)
- [pydantic](https://docs.pydantic.dev/) - Data validation and settings management
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - The main monorepo containing this package
- [RediSearch](https://redis.io/docs/interact/search-and-query/) - The search and query engine this library connects to
- [kiarina-lib-redis](../kiarina-lib-redis/) - Redis client library for basic Redis operations
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library used by this package
