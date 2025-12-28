from kiarina.lib.redisearch import RedisearchClient


def test_reset_index(client: RedisearchClient):
    client.reset_index()

    assert client.get("test_id") is None
    client.set({"title": "This is a test document."}, id="test_id")
