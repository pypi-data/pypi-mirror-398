from typing import Awaitable, Literal, overload

from ..schemas.redisearch_context import RedisearchContext
from .get_key import get_key


@overload
def delete(
    mode: Literal["sync"],
    ctx: RedisearchContext,
    id: str,
) -> None: ...


@overload
def delete(
    mode: Literal["async"],
    ctx: RedisearchContext,
    id: str,
) -> Awaitable[None]: ...


def delete(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
    id: str,
) -> None | Awaitable[None]:
    """
    Delete a document from the index.
    """
    key = get_key(ctx, id)

    def _sync() -> None:
        ctx.redis.delete(key)

    async def _async() -> None:
        await ctx.redis_async.delete(key)

    if mode == "sync":
        _sync()
        return None
    else:
        return _async()
