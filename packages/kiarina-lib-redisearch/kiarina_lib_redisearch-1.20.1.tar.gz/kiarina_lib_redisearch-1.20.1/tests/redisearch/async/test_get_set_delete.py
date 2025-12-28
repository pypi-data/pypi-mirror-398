from kiarina.lib.redisearch.asyncio import RedisearchClient


async def test_get_set_delete(client: RedisearchClient):
    await client.reset_index()

    id = "test_id"
    mapping = {"title": "This is a test document."}

    await client.set(mapping, id=id)
    document = await client.get(id)
    assert document is not None
    assert document.key == f"{client.ctx.settings.key_prefix}{id}"
    assert document.id == id
    assert document.mapping == mapping

    count_result = await client.count()
    assert count_result.total == 1

    await client.delete(id)
    assert await client.get(id) is None
