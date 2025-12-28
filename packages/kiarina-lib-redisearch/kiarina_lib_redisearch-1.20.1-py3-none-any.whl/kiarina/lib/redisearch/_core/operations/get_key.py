from ..schemas.redisearch_context import RedisearchContext


def get_key(ctx: RedisearchContext, id: str) -> str:
    """
    Get the Redis key for a given Redisearch ID.
    """
    return f"{ctx.settings.key_prefix}{id}"
