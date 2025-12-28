from typing import Awaitable, Literal, overload

from redis.commands.search.query import Query

from kiarina.lib.redisearch_filter import (
    RedisearchFilter,
    RedisearchFilterConditions,
    create_redisearch_filter,
)

from ..schemas.redisearch_context import RedisearchContext
from ..views.search_result import SearchResult


@overload
def count(
    mode: Literal["sync"],
    ctx: RedisearchContext,
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
) -> SearchResult: ...


@overload
def count(
    mode: Literal["async"],
    ctx: RedisearchContext,
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
) -> Awaitable[SearchResult]: ...


def count(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
) -> SearchResult | Awaitable[SearchResult]:
    """
    Count documents matching the filter.
    """
    if filter is not None:
        filter = create_redisearch_filter(filter=filter, schema=ctx.schema)

    filter_query = "*" if filter is None else str(filter)
    query = Query(filter_query).no_content().paging(0, 0)

    def _sync() -> SearchResult:
        result = ctx.redis.ft(ctx.settings.index_name).search(query)
        return SearchResult(total=result.total, duration=result.duration)  # pyright: ignore[reportAttributeAccessIssue]

    async def _async() -> SearchResult:
        result = await ctx.redis_async.ft(ctx.settings.index_name).search(query)
        return SearchResult(total=result.total, duration=result.duration)  # pyright: ignore[reportAttributeAccessIssue]

    if mode == "sync":
        return _sync()
    else:
        return _async()
