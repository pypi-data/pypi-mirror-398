from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    """
    Redisearch Document
    """

    key: str = ""
    """
    Redis key

    {key_prefix}:{id} is the key
    """

    id: str = ""
    """Redisearch document ID"""

    score: float = 0.0
    """Redisearch document score"""

    mapping: dict[str, Any] = Field(default_factory=dict)
    """Redisearch document mapping"""
