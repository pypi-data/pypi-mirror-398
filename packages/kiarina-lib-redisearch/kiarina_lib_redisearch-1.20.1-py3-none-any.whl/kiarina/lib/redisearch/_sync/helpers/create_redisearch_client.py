import redis

from kiarina.lib.redisearch_schema import RedisearchSchema, RedisearchFieldDicts

from ..._settings import settings_manager
from ..models.redisearch_client import RedisearchClient


def create_redisearch_client(
    settings_key: str | None = None,
    *,
    field_dicts: RedisearchFieldDicts,
    redis: redis.Redis,
) -> RedisearchClient:
    settings = settings_manager.get_settings(settings_key)
    schema = RedisearchSchema.from_field_dicts(field_dicts)
    return RedisearchClient(settings, schema=schema, redis=redis)
