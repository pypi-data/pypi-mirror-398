from typing import Awaitable, Literal, overload

from redis.commands.search.index_definition import IndexDefinition, IndexType

from ..schemas.redisearch_context import RedisearchContext


@overload
def create_index(
    mode: Literal["sync"],
    ctx: RedisearchContext,
) -> None: ...


@overload
def create_index(
    mode: Literal["async"],
    ctx: RedisearchContext,
) -> Awaitable[None]: ...


def create_index(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
) -> None | Awaitable[None]:
    """
    Create the index.
    """
    fields = ctx.schema.to_fields()

    definition = IndexDefinition(  # type: ignore[no-untyped-call]
        prefix=[ctx.settings.key_prefix],
        index_type=IndexType.HASH,
    )

    def _sync() -> None:
        ctx.redis.ft(ctx.settings.index_name).create_index(
            fields=fields,
            definition=definition,
        )

    async def _async() -> None:
        await ctx.redis_async.ft(ctx.settings.index_name).create_index(
            fields=fields,
            definition=definition,
        )

    if mode == "sync":
        _sync()
        return None
    else:
        return _async()
