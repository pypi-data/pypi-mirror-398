from kiarina.lib.redisearch.asyncio import RedisearchClient, RedisearchSettings
from kiarina.lib.redisearch_schema import RedisearchSchema


async def test_migrate(key_prefix, index_name, redis):
    fields: list[dict] = []

    def _create_client() -> RedisearchClient:
        return RedisearchClient(
            RedisearchSettings(
                key_prefix=key_prefix,
                index_name=index_name,
            ),
            schema=RedisearchSchema.from_field_dicts(fields),
            redis=redis,
        )

    # 1. Create index
    fields.extend(
        [
            {"type": "tag", "name": "user_id"},
            {"type": "tag", "name": "category", "multiple": True},
            {"type": "vector", "name": "embedding", "algorithm": "FLAT", "dims": 3072},
        ]
    )

    client1 = _create_client()
    await client1.drop_index()
    await client1.migrate_index()
    await client1.set(
        {
            "user_id": "test_user_id",
            "category": ["tech", "art"],
            "embedding": [1.0] * 3072,
        },
        id="test_id",
    )

    info_result1 = await client1.get_info()
    assert info_result1.index_schema == client1.ctx.schema

    # 2. Add field and migrate
    fields.extend(
        [
            {"type": "numeric", "name": "timestamp", "sortable": True},
        ]
    )

    client2 = _create_client()
    await client2.migrate_index()

    info_result2 = await client2.get_info()
    assert info_result2.index_schema == client2.ctx.schema

    # 3. Remove field and migrate
    fields.pop()

    client3 = _create_client()
    await client3.migrate_index()

    info_result3 = await client3.get_info()
    assert info_result3.index_schema == client3.ctx.schema

    # 4. Update field and migrate
    fields[-1]["dims"] = 1536

    client4 = _create_client()
    await client4.migrate_index()
    info_result4 = await client4.get_info()
    assert info_result4.index_schema == client4.ctx.schema

    # 5. No changes
    client5 = _create_client()
    await client5.migrate_index()
    info_result5 = await client5.get_info()
    assert info_result5.index_schema == client5.ctx.schema

    # 6. Confirm that the document has not been deleted
    assert await client5.get("test_id") is not None
