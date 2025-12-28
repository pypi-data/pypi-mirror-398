from kiarina.lib.redisearch import RedisearchClient


def test_get_set_delete(client: RedisearchClient):
    client.reset_index()

    id = "test_id"
    mapping = {"title": "This is a test document."}

    client.set(mapping, id=id)
    document = client.get(id)
    assert document is not None
    assert document.key == f"{client.ctx.settings.key_prefix}{id}"
    assert document.id == id
    assert document.mapping == mapping

    count_result = client.count()
    assert count_result.total == 1

    client.delete(id)
    assert client.get(id) is None
