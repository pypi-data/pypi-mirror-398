from typing import Any, TypeAlias

RedisearchFieldDicts: TypeAlias = list[dict[str, Any]]
"""
Redisearch index schema field dictionaries

Example:
>>> schema = [
>>>     {"type": "tag", "name": "category"},
>>>     {"type": "text", "name": "title"},
>>>     {"type": "numeric", "name": "price", "sortable": True},
>>>     {"type": "vector", "name": "embedding", "algorithm": "FLAT", "dims": 1536}
>>> ]
"""
