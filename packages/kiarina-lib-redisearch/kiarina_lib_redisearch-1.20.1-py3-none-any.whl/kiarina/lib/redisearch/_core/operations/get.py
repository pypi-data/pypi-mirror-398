from typing import Awaitable, Literal, overload

from ..schemas.document import Document
from ..schemas.redisearch_context import RedisearchContext
from ..utils.unmarshal_mappings import unmarshal_mappings
from .get_key import get_key


@overload
def get(
    mode: Literal["sync"],
    ctx: RedisearchContext,
    id: str,
) -> Document | None: ...


@overload
def get(
    mode: Literal["async"],
    ctx: RedisearchContext,
    id: str,
) -> Awaitable[Document | None]: ...


def get(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
    id: str,
) -> Document | None | Awaitable[Document | None]:
    """
    Get a document from the index.
    """
    key = get_key(ctx, id)

    def _after(mapping: dict[bytes, bytes]) -> Document | None:
        if not mapping:
            return None

        unmarshaled = unmarshal_mappings(schema=ctx.schema, mapping=mapping)

        return Document(
            key=key,
            id=id,
            mapping=unmarshaled,
        )

    def _sync() -> Document | None:
        mapping = ctx.redis.hgetall(key)
        assert isinstance(mapping, dict)
        return _after(mapping)

    async def _async() -> Document | None:
        coro = ctx.redis_async.hgetall(key)
        assert not isinstance(coro, dict)
        mapping = await coro
        return _after(mapping)

    if mode == "sync":
        return _sync()
    else:
        return _async()
