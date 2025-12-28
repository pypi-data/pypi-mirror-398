import pytest

import kiarina.utils.file as kf
from kiarina.lib.redisearch import RedisearchClient


@pytest.fixture
def fields():
    return [
        {"type": "tag", "name": "id"},
        {"type": "text", "name": "title"},
        {"type": "vector", "name": "embedding", "algorithm": "FLAT", "dims": 3072},
    ]


@pytest.fixture
def data_rows(data_dir):
    return kf.read_json_list(
        data_dir / "small" / "id_title_content_embedding_3row_apple_car_dog.json"
    )


@pytest.fixture
def data_query(data_dir):
    return kf.read_json_dict(
        data_dir / "small" / "query_embedding_tell_me_about_dogs_not_apples.json"
    )


def test_search(client: RedisearchClient, data_rows, data_query):
    client.reset_index()

    for row in data_rows:
        client.set(row)

    # The simplest search
    result = client.search(
        vector=data_query["embedding"],
    )

    assert result.total == 3
    assert all(doc.id in ("1", "2", "3") for doc in result.documents)
    assert result.documents[0].id == "3"
    assert result.documents[1].id == "1"
    assert result.documents[2].id == "2"

    # Return the id field included in the document's mapping
    result = client.search(
        vector=data_query["embedding"],
        return_fields=["id"],
    )

    assert result.total == 3
    assert "id" in result.documents[0].mapping
    assert ":" not in result.documents[0].mapping["id"]

    # After narrowing down the parent set, perform vector search
    result = client.search(
        vector=data_query["embedding"],
        filter=[
            ["id", "in", ("1", "3")],
        ],
    )

    assert result.total == 2
    assert all(doc.id in ("1", "3") for doc in result.documents)

    # Offset and limit
    result = client.search(
        vector=data_query["embedding"],
        offset=1,
        limit=2,
    )

    assert result.total == 2
    assert len(result.documents) == 1
    assert result.documents[0].id == "1"
