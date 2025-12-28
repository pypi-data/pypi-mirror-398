from kiarina.lib.redisearch import RedisearchClient


def test_count(client: RedisearchClient):
    client.reset_index()

    client.set({"title": "This is a test document."}, id="test_id")

    count_result = client.count()
    assert count_result.total == 1
