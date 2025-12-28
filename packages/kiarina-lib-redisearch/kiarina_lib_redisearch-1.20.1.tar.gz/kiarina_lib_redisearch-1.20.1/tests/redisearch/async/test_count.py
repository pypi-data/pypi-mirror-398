from kiarina.lib.redisearch.asyncio import RedisearchClient


async def test_count(client: RedisearchClient):
    await client.reset_index()

    await client.set({"title": "This is a test document."}, id="test_id")

    count_result = await client.count()
    assert count_result.total == 1
