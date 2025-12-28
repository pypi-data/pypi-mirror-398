from typing import Any, Awaitable, Literal, overload

from redis.commands.search.query import Query
from redis.commands.search.result import Result

from kiarina.lib.redisearch_filter import (
    RedisearchFilter,
    RedisearchFilterConditions,
    create_redisearch_filter,
)

from ..schemas.redisearch_context import RedisearchContext
from ..views.search_result import SearchResult
from .count import count
from .parse_search_result import parse_search_result


@overload
def find(
    mode: Literal["sync"],
    ctx: RedisearchContext,
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
    sort_by: str | None = None,
    sort_desc: bool = False,
    offset: int | None = None,
    limit: int | None = None,
    return_fields: list[str] | None = None,
) -> SearchResult: ...


@overload
def find(
    mode: Literal["async"],
    ctx: RedisearchContext,
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
    sort_by: str | None = None,
    sort_desc: bool = False,
    offset: int | None = None,
    limit: int | None = None,
    return_fields: list[str] | None = None,
) -> Awaitable[SearchResult]: ...


def find(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
    sort_by: str | None = None,
    sort_desc: bool = False,
    offset: int | None = None,
    limit: int | None = None,
    return_fields: list[str] | None = None,
) -> SearchResult | Awaitable[SearchResult]:
    """
    Find documents matching the filter criteria.

    Args:
        limit (int | None):
            Number of documents to retrieve. If None, retrieves all documents
        return_fields (list[str] | None):
            Fields to return. If None, returns no content, only IDs.
    """
    if filter is not None:
        filter = create_redisearch_filter(filter=filter, schema=ctx.schema)

    filter_query = "*" if filter is None else str(filter)

    def _build_query(limit: int) -> Query:
        query = Query(filter_query)

        if return_fields:
            query = query.return_fields(*return_fields)
        else:
            query = query.no_content()

        if sort_by:
            query = query.sort_by(sort_by, asc=not sort_desc)

        query = query.paging(offset or 0, limit)
        return query

    def _parse_search_result(result: Any) -> SearchResult:
        assert isinstance(result, Result)
        return parse_search_result(
            key_prefix=ctx.settings.key_prefix,
            schema=ctx.schema,
            return_fields=return_fields,
            result=result,
        )

    def _sync() -> SearchResult:
        query = _build_query(limit or count(mode="sync", ctx=ctx, filter=filter).total)
        result = ctx.redis.ft(ctx.settings.index_name).search(query)
        return _parse_search_result(result)

    async def _async() -> SearchResult:
        query = _build_query(
            limit or (await count(mode="async", ctx=ctx, filter=filter)).total
        )
        result = await ctx.redis_async.ft(ctx.settings.index_name).search(query)
        return _parse_search_result(result)

    if mode == "sync":
        return _sync()
    else:
        return _async()
