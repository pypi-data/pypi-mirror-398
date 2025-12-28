from kiarina.lib.redisearch.asyncio import RedisearchClient


async def test_create_exists_drop_index(client: RedisearchClient):
    # Clean up before test
    await client.drop_index()
    assert not await client.exists_index()

    # Create index
    await client.create_index()
    assert await client.exists_index()

    # Drop index
    await client.drop_index()
    assert not await client.exists_index()
