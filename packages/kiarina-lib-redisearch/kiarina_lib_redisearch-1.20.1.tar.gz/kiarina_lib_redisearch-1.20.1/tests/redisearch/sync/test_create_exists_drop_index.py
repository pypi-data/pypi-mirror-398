from kiarina.lib.redisearch import RedisearchClient


def test_create_exists_drop_index(client: RedisearchClient):
    # Clean up before test
    client.drop_index()
    assert not client.exists_index()

    # Create index
    client.create_index()
    assert client.exists_index()

    # Drop index
    client.drop_index()
    assert not client.exists_index()
