import pytest

from kiarina.lib.redisearch.asyncio import RedisearchClient


@pytest.fixture
def fields():
    return [
        {"type": "tag", "name": "id"},
        {"type": "text", "name": "title"},
        {"type": "numeric", "name": "timestamp", "sortable": True},
    ]


async def test_find(client: RedisearchClient):
    await client.reset_index()

    # Insert test data
    await client.set({"id": "1", "title": "Hello world", "timestamp": 1620000000})
    await client.set({"id": "2", "title": "Hello Redis", "timestamp": 1620000001})
    await client.set({"id": "3", "title": "Goodbye world", "timestamp": 1620000002})

    # Basic find without filters
    result = await client.find()
    assert result.total == 3
    assert all(doc.id in ("1", "2", "3") for doc in result.documents)

    # Retrieve the field value
    result = await client.find(return_fields=["title"])
    assert result.total == 3
    assert all("title" in doc.mapping for doc in result.documents)

    # Sort by timestamp descending
    result = await client.find(sort_by="timestamp", sort_desc=True)
    assert result.total == 3
    assert result.documents[0].id == "3"
    assert result.documents[1].id == "2"
    assert result.documents[2].id == "1"

    # Retrieve filtered results sorted
    result = await client.find(
        filter=[["id", "in", ("1", "3")]],
        sort_by="timestamp",
        sort_desc=True,
    )
    assert result.total == 2
    assert result.documents[0].id == "3"
    assert result.documents[1].id == "1"

    # offset and limit
    result = await client.find(sort_by="timestamp", offset=1, limit=1)
    assert result.total == 3
    assert len(result.documents) == 1
    assert result.documents[0].id == "2"
