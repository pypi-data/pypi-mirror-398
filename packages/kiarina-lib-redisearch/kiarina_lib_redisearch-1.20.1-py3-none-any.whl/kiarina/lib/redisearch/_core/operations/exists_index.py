from typing import Awaitable, Literal, overload

from ..schemas.redisearch_context import RedisearchContext
from .get_info import get_info


@overload
def exists_index(
    mode: Literal["sync"],
    ctx: RedisearchContext,
) -> bool: ...


@overload
def exists_index(
    mode: Literal["async"],
    ctx: RedisearchContext,
) -> Awaitable[bool]: ...


def exists_index(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
) -> bool | Awaitable[bool]:
    """
    Check if the index exists.
    """

    def _handle_exception(e: Exception) -> bool:
        # <= Redis 7
        if str(e) == "Unknown index name":
            return False
        # Redis 8
        elif "no such index" in str(e):
            return False

        raise

    def _sync() -> bool:
        try:
            get_info(mode="sync", ctx=ctx)
            return True
        except Exception as e:
            return _handle_exception(e)

    async def _async() -> bool:
        try:
            await get_info(mode="async", ctx=ctx)
            return True
        except Exception as e:
            return _handle_exception(e)

    if mode == "sync":
        return _sync()
    else:
        return _async()
