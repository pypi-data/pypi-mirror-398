from typing import Awaitable, Literal, overload

from ..schemas.redisearch_context import RedisearchContext


@overload
def drop_index(
    mode: Literal["sync"],
    ctx: RedisearchContext,
    *,
    delete_documents: bool = False,
) -> bool: ...


@overload
def drop_index(
    mode: Literal["async"],
    ctx: RedisearchContext,
    *,
    delete_documents: bool = False,
) -> Awaitable[bool]: ...


def drop_index(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
    *,
    delete_documents: bool = False,
) -> bool | Awaitable[bool]:
    """
    Delete the index.
    """

    def _sync() -> bool:
        if ctx.settings.protect_index_deletion:
            return False

        try:
            ctx.redis.ft(ctx.settings.index_name).dropindex(delete_documents)
            return True
        except Exception:
            return False

    async def _async() -> bool:
        if ctx.settings.protect_index_deletion:
            return False

        try:
            await ctx.redis_async.ft(ctx.settings.index_name).dropindex(
                delete_documents
            )
            return True
        except Exception:
            return False

    if mode == "sync":
        return _sync()
    else:
        return _async()
