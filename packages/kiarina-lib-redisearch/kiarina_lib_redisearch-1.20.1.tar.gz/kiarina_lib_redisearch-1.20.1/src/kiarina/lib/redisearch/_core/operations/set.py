from typing import Any, Awaitable, Literal, overload

from ..schemas.redisearch_context import RedisearchContext
from ..utils.marshal_mappings import marshal_mappings
from .get_key import get_key


@overload
def set(
    mode: Literal["sync"],
    ctx: RedisearchContext,
    mapping: dict[str, Any],
    *,
    id: str | None = None,
) -> None: ...


@overload
def set(
    mode: Literal["async"],
    ctx: RedisearchContext,
    mapping: dict[str, Any],
    *,
    id: str | None = None,
) -> Awaitable[None]: ...


def set(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
    mapping: dict[str, Any],
    *,
    id: str | None = None,
) -> None | Awaitable[None]:
    """
    Set a document in the index.

    Fields not present in the schema are saved as they are.
    Fields present in the schema are converted to the appropriate type and stored.
    """
    if id is None:
        if "id" not in mapping:
            raise ValueError(
                'Either "id" parameter or "id" field in mapping must be provided.'
            )

        id = str(mapping.get("id"))

    key = get_key(ctx, id)

    mapping = marshal_mappings(schema=ctx.schema, mapping=mapping)

    def _sync() -> None:
        ctx.redis.hset(key, mapping=mapping)

    async def _async() -> None:
        coro = ctx.redis_async.hset(key, mapping=mapping)
        assert not isinstance(coro, int)
        await coro

    if mode == "sync":
        _sync()
        return None
    else:
        return _async()
