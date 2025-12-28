from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class RedisearchSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_REDISEARCH_")

    key_prefix: str = ""
    """
    Redis key prefix

    The prefix for keys of documents registered with Redisearch.
    Specify a string ending with a colon. e.g. "myapp:"
    """

    index_name: str = "default"
    """
    Redisearch index name

    Only alphanumeric characters, underscores, hyphens, and periods.
    The beginning consists solely of letters.
    """

    protect_index_deletion: bool = False
    """
    Protect index deletion

    When set to True, the delete_index operation is protected,
    preventing the index from being accidentally deleted.
    """


settings_manager = SettingsManager(RedisearchSettings, multi=True)
