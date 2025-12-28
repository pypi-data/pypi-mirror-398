from typing import Any, TypeAlias

RedisearchFilterConditions: TypeAlias = list[list[Any]]
"""
RedisearchFilter に変換可能なリスト

Examples:
    >>> [
    ...     ["color", "in", ["blue", "red"]],
    ...     ["price", "<", 1000],
    ...     ["title", "like", "*hello*"]
    ... ]

Tag conditions:
    - ["color", "==", "blue"]
    - ["color", "!=", "blue"]
    - ["color", "in", ["blue", "red"]]
    - ["color", "not in", ["blue", "red"]]

Numeric conditions:
    - ["price", "==", 1000]
    - ["price", "!=", 1000]
    - ["price", ">", 1000]
    - ["price", "<", 1000]
    - ["price", ">=", 1000]
    - ["price", "<=", 1000]

Text conditions:
    - ["title", "==", "hello"]
    - ["title", "!=", "hello"]
    - ["title", "like", "*hello*"]
"""
