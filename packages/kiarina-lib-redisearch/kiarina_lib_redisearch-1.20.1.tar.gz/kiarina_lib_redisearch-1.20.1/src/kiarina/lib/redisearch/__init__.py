import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._sync.helpers.create_redisearch_client import create_redisearch_client
    from ._sync.models.redisearch_client import RedisearchClient
    from ._settings import RedisearchSettings, settings_manager

__version__ = version("kiarina-lib-redisearch")

__all__ = [
    # ._sync.helpers
    "create_redisearch_client",
    # ._sync.models
    "RedisearchClient",
    # ._settings
    "RedisearchSettings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._sync.helpers
        "create_redisearch_client": "._sync.helpers.create_redisearch_client",
        # ._sync.models
        "RedisearchClient": "._sync.models.redisearch_client",
        # ._settings
        "RedisearchSettings": "._settings",
        "settings_manager": "._settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
