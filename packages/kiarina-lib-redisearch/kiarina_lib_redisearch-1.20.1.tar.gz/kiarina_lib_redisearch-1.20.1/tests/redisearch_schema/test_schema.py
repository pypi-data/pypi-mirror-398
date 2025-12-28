import pytest

from kiarina.lib.redisearch_schema import RedisearchSchema


def test_redisearch_schema():
    schema = RedisearchSchema.model_validate(
        {
            "fields": [
                {
                    "type": "tag",
                    "name": "type",
                },
                {
                    "type": "text",
                    "name": "title",
                },
                {
                    "type": "numeric",
                    "name": "timestamp",
                    "sortable": True,
                },
                {
                    "type": "vector",
                    "algorithm": "FLAT",
                    "name": "embeddings",
                    "dims": 3072,
                },
            ]
        }
    )
    assert len(schema.to_fields()) == 4


def test_redisearch_schema_invalid_field_names():
    with pytest.raises(ValueError):
        RedisearchSchema.model_validate(
            {
                "fields": [
                    {
                        "type": "tag",
                        "name": "id",
                    },
                    {
                        "type": "text",
                        "name": "payload",
                    },
                ]
            }
        )
