from typing import Any

from redis import Redis

from kiarina.lib.redisearch_filter import RedisearchFilter, RedisearchFilterConditions
from kiarina.lib.redisearch_schema import RedisearchSchema

from ..._core.schemas.redisearch_context import RedisearchContext
from ..._core.operations.count import count
from ..._core.operations.create_index import create_index
from ..._core.operations.delete import delete
from ..._core.operations.drop_index import drop_index
from ..._core.operations.exists_index import exists_index
from ..._core.operations.find import find
from ..._core.operations.get import get
from ..._core.operations.get_info import get_info
from ..._core.operations.get_key import get_key
from ..._core.operations.migrate_index import migrate_index
from ..._core.operations.reset_index import reset_index
from ..._core.operations.search import search
from ..._core.operations.set import set
from ..._core.schemas.document import Document
from ..._core.views.info_result import InfoResult
from ..._core.views.search_result import SearchResult
from ..._settings import RedisearchSettings


class RedisearchClient:
    """
    Redisearch client
    """

    def __init__(
        self,
        settings: RedisearchSettings,
        *,
        schema: RedisearchSchema,
        redis: Redis,
    ) -> None:
        if redis.get_encoder().decode_responses:
            # As the vector field in Redisearch is expected to be handled as bytes in redis-py,
            raise ValueError("Redis client must have decode_responses=False")

        self.ctx: RedisearchContext = RedisearchContext(
            settings=settings,
            schema=schema,
            _redis=redis,
        )

    # --------------------------------------------------
    # Index operations
    # --------------------------------------------------

    def exists_index(self) -> bool:
        """
        Check if the index exists.
        """
        return exists_index("sync", self.ctx)

    def create_index(self) -> None:
        """
        Create the search index.
        """
        create_index("sync", self.ctx)

    def drop_index(self, *, delete_documents: bool = False) -> bool:
        """
        Delete the index.
        """
        return drop_index("sync", self.ctx, delete_documents=delete_documents)

    def reset_index(self) -> None:
        """
        Reset the search index.
        """
        reset_index("sync", self.ctx)

    def migrate_index(self) -> None:
        """
        Migrate the search index.
        """
        migrate_index("sync", self.ctx)

    def get_info(self) -> InfoResult:
        """
        Get index information using FT.INFO command.
        """
        return get_info("sync", self.ctx)

    # --------------------------------------------------
    # Data operations
    # --------------------------------------------------

    def set(self, mapping: dict[str, Any], *, id: str | None = None) -> None:
        """
        Set a hash value.

        If no id is specified, the mapping must contain an "id" field.
        """
        set("sync", self.ctx, mapping, id=id)

    def delete(self, id: str) -> None:
        """
        Delete a document from the index.
        """
        delete("sync", self.ctx, id)

    def get(self, id: str) -> Document | None:
        """
        Get a document from the index.
        """
        return get("sync", self.ctx, id)

    # --------------------------------------------------
    # Search operations
    # --------------------------------------------------

    def count(
        self,
        *,
        filter: RedisearchFilter | RedisearchFilterConditions | None = None,
    ) -> SearchResult:
        """
        Count documents matching the filter.
        """
        return count("sync", self.ctx, filter=filter)

    def find(
        self,
        *,
        filter: RedisearchFilter | RedisearchFilterConditions | None = None,
        sort_by: str | None = None,
        sort_desc: bool = False,
        offset: int | None = None,
        limit: int | None = None,
        return_fields: list[str] | None = None,
    ) -> SearchResult:
        """
        Find documents matching the filter criteria.
        """
        return find(
            "sync",
            self.ctx,
            filter=filter,
            sort_by=sort_by,
            sort_desc=sort_desc,
            offset=offset,
            limit=limit,
            return_fields=return_fields,
        )

    def search(
        self,
        *,
        vector: list[float],
        filter: RedisearchFilter | RedisearchFilterConditions | None = None,
        offset: int | None = None,
        limit: int | None = None,
        return_fields: list[str] | None = None,
    ) -> SearchResult:
        """
        Search documents using vector similarity search.
        """
        return search(
            "sync",
            self.ctx,
            vector=vector,
            filter=filter,
            offset=offset,
            limit=limit,
            return_fields=return_fields,
        )

    # --------------------------------------------------
    # Utilities
    # --------------------------------------------------

    def get_key(self, id: str) -> str:
        """
        Get the Redis key for a given Redisearch ID.
        """
        return get_key(self.ctx, id)
