from pydantic import BaseModel

from kiarina.lib.redisearch_schema import RedisearchSchema


class InfoResult(BaseModel):
    """
    Model representing FT.INFO results
    """

    index_name: str
    """Index name"""

    num_docs: int
    """Number of documents"""

    num_terms: int
    """Number of terms"""

    num_records: int
    """Number of records"""

    index_schema: RedisearchSchema
    """Index schema"""
