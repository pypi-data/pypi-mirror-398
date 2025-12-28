from kiarina.lib.redisearch.asyncio import RedisearchClient


async def test_reset_index(client: RedisearchClient):
    await client.reset_index()

    assert await client.get("test_id") is None
    await client.set({"title": "This is a test document."}, id="test_id")
