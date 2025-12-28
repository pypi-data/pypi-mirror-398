from typing import Any, Awaitable, Literal, overload

import numpy as np
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
def search(
    mode: Literal["sync"],
    ctx: RedisearchContext,
    vector: list[float],
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
    offset: int | None = None,
    limit: int | None = None,
    return_fields: list[str] | None = None,
) -> SearchResult: ...


@overload
def search(
    mode: Literal["async"],
    ctx: RedisearchContext,
    vector: list[float],
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
    offset: int | None = None,
    limit: int | None = None,
    return_fields: list[str] | None = None,
) -> Awaitable[SearchResult]: ...


def search(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
    vector: list[float],
    filter: RedisearchFilter | RedisearchFilterConditions | None = None,
    offset: int | None = None,
    limit: int | None = None,
    return_fields: list[str] | None = None,
) -> SearchResult | Awaitable[SearchResult]:
    """
    Search documents using vector similarity search.
    """
    # filter_query
    if filter is not None:
        filter = create_redisearch_filter(filter=filter, schema=ctx.schema)

    filter_query = "*" if filter is None else str(filter)

    # vector_field_name
    vector_field_name = ctx.schema.vector_field.name

    # return_fields
    return_fields = return_fields or []

    if "distance" not in return_fields:
        return_fields.append("distance")

    # params
    params: dict[str, str | int | float | bytes] = {
        "vector": np.array(vector).astype(ctx.schema.vector_field.dtype).tobytes()
    }

    def _build_query(limit: int) -> Query:
        query = Query(
            f"({filter_query})=>[KNN {limit} @{vector_field_name} $vector AS distance]"
        )

        if return_fields:
            query = query.return_fields(*return_fields)
        else:
            query = query.no_content()

        query = query.sort_by("distance")
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
        query = _build_query(limit or count("sync", ctx, filter).total)
        result = ctx.redis.ft(ctx.settings.index_name).search(query, params)
        return _parse_search_result(result)

    async def _async() -> SearchResult:
        query = _build_query(limit or (await count("async", ctx, filter)).total)
        result = await ctx.redis_async.ft(ctx.settings.index_name).search(query, params)
        return _parse_search_result(result)

    if mode == "sync":
        return _sync()
    else:
        return _async()
