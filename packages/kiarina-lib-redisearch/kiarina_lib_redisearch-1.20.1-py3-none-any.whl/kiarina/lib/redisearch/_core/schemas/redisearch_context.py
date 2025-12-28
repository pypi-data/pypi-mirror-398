from dataclasses import dataclass

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from kiarina.lib.redisearch_schema import RedisearchSchema

from ..._settings import RedisearchSettings


@dataclass
class RedisearchContext:
    settings: RedisearchSettings
    schema: RedisearchSchema
    _redis: Redis | None = None
    _redis_async: AsyncRedis | None = None

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def redis(self) -> Redis:
        if self._redis is None:
            raise ValueError("Redis client is not set in RedisearchContext")

        return self._redis

    @redis.setter
    def redis(self, value: Redis) -> None:
        self._redis = value

    @property
    def redis_async(self) -> AsyncRedis:
        if self._redis_async is None:
            raise ValueError("Async Redis client is not set in RedisearchContext")

        return self._redis_async

    @redis_async.setter
    def redis_async(self, value: AsyncRedis) -> None:
        self._redis_async = value
