from pydantic import BaseModel, Field

from ..schemas.document import Document


class SearchResult(BaseModel):
    """
    Model representing FT.SEARCH results
    """

    total: int = 0
    """
    Total number of results

    For searches not using KNN (RedisearchClient.find):
        This indicates the total number of documents matching the query,
        regardless of the limit parameter.

    For vector search using KNN (RedisearchClient.search):
        When using KNN, the total in FT.SEARCH depends on the value of k.
        If limit is not specified,
        the number of records in the population after filtering will be total.
        When a limit is specified, k becomes equal to the limit,
        so the value of total is less than or equal to the limit.
    """

    duration: float = 0.0
    """The execution time of the query in milliseconds"""

    documents: list[Document] = Field(default_factory=list)
    """List of documents"""
