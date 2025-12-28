import logging
from typing import Awaitable, Literal, overload

from ..schemas.redisearch_context import RedisearchContext
from .create_index import create_index
from .drop_index import drop_index
from .exists_index import exists_index

logger = logging.getLogger(__name__)


@overload
def reset_index(
    mode: Literal["sync"],
    ctx: RedisearchContext,
) -> None: ...


@overload
def reset_index(
    mode: Literal["async"],
    ctx: RedisearchContext,
) -> Awaitable[None]: ...


def reset_index(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
) -> None | Awaitable[None]:
    """
    Reset the search index.
    """

    def _log_delete_index() -> None:
        logger.info("Deleting existing index '%s'", ctx.settings.index_name)

    def _log_create_index() -> None:
        logger.info("Creating new index '%s'", ctx.settings.index_name)

    def _sync() -> None:
        if exists_index(mode="sync", ctx=ctx):
            _log_delete_index()
            drop_index(mode="sync", ctx=ctx, delete_documents=True)

        _log_create_index()
        create_index(mode="sync", ctx=ctx)

    async def _async() -> None:
        if await exists_index(mode="async", ctx=ctx):
            _log_delete_index()
            await drop_index(mode="async", ctx=ctx, delete_documents=True)

        _log_create_index()
        await create_index(mode="async", ctx=ctx)

    if mode == "sync":
        _sync()
        return None
    else:
        return _async()
