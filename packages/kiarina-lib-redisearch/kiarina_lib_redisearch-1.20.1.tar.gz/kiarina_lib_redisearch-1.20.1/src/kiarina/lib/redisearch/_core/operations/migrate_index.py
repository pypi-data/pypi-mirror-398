import logging
from typing import Any, Awaitable, Literal, overload

from kiarina.lib.redisearch_schema import RedisearchSchema

from ..schemas.redisearch_context import RedisearchContext
from .create_index import create_index
from .drop_index import drop_index
from .exists_index import exists_index
from .get_info import get_info

logger = logging.getLogger(__name__)


@overload
def migrate_index(
    mode: Literal["sync"],
    ctx: RedisearchContext,
) -> bool: ...


@overload
def migrate_index(
    mode: Literal["async"],
    ctx: RedisearchContext,
) -> Awaitable[bool]: ...


def migrate_index(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
) -> bool | Awaitable[bool]:
    """
    Reset the search index.
    """

    def _log_create_new_index() -> None:
        logger.info("Createing new index '%s'", ctx.settings.index_name)

    def _log_no_schema_changes() -> None:
        logger.info("No schema changes detected, migration not needed.")

    def _log_migration_needed(diffs: dict[str, tuple[Any, Any]]) -> None:
        logger.info("Schema changes detected, migration needed:")

        for path, (old, new) in diffs.items():
            logger.info(" - %s: %r -> %r", path, old, new)

    def _log_delete_index() -> None:
        logger.info(
            "Deleting existing index '%s', data will be re-indexed",
            ctx.settings.index_name,
        )

    def _sync() -> bool:
        if not exists_index(mode="sync", ctx=ctx):
            _log_create_new_index()
            create_index(mode="sync", ctx=ctx)
            return True

        info_result = get_info(mode="sync", ctx=ctx)
        diffs = _check_schema_changes(current=info_result.index_schema, new=ctx.schema)

        if not diffs:
            _log_no_schema_changes()
            return False

        _log_migration_needed(diffs)

        _log_delete_index()
        drop_index(mode="sync", ctx=ctx, delete_documents=False)

        _log_create_new_index()
        create_index(mode="sync", ctx=ctx)
        return True

    async def _async() -> bool:
        if not await exists_index(mode="async", ctx=ctx):
            _log_create_new_index()
            await create_index(mode="async", ctx=ctx)
            return True

        info_result = await get_info(mode="async", ctx=ctx)
        diffs = _check_schema_changes(current=info_result.index_schema, new=ctx.schema)

        if not diffs:
            _log_no_schema_changes()
            return False

        _log_migration_needed(diffs)

        _log_delete_index()
        await drop_index(mode="async", ctx=ctx, delete_documents=False)

        _log_create_new_index()
        await create_index(mode="async", ctx=ctx)
        return True

    if mode == "sync":
        return _sync()
    else:
        return _async()


def _check_schema_changes(
    current: RedisearchSchema,
    new: RedisearchSchema,
) -> dict[str, tuple[Any, Any]]:
    if current == new:
        return {}

    return _diff_dict(
        current.model_dump(),
        new.model_dump(),
    )


def _diff_dict(
    d1: dict[str, Any], d2: dict[str, Any], prefix: str = ""
) -> dict[str, tuple[Any, Any]]:
    diffs: dict[str, tuple[Any, Any]] = {}

    keys = set(d1.keys()) | set(d2.keys())

    for k in keys:
        v1, v2 = d1.get(k), d2.get(k)
        path = f"{prefix}.{k}" if prefix else k

        # Nested dict
        if isinstance(v1, dict) and isinstance(v2, dict):
            nested_diff = _diff_dict(v1, v2, prefix=path)
            diffs.update(nested_diff)

        # Nested list
        elif isinstance(v1, list) and isinstance(v2, list):
            max_len = max(len(v1), len(v2))

            for i in range(max_len):
                p = f"{path}[{i}]"

                try:
                    item1, item2 = v1[i], v2[i]
                except IndexError:
                    diffs[p] = (
                        v1[i] if i < len(v1) else None,
                        v2[i] if i < len(v2) else None,
                    )
                    continue

                if isinstance(item1, dict) and isinstance(item2, dict):
                    nested_diff = _diff_dict(item1, item2, prefix=p)
                    diffs.update(nested_diff)

                elif item1 != item2:
                    diffs[p] = (item1, item2)

        # Different values
        elif v1 != v2:
            diffs[path] = (v1, v2)

    return diffs
