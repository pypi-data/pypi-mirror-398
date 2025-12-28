import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._async.helpers.get_redis import get_redis
    from ._settings import RedisSettings, settings_manager

__all__ = [
    # ._async.helpers
    "get_redis",
    # ._settings
    "RedisSettings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._async.helpers
        "get_redis": "._async.helpers.get_redis",
        # ._settings
        "RedisSettings": "._settings",
        "settings_manager": "._settings",
    }

    parent = __name__.rsplit(".", 1)[0]
    globals()[name] = getattr(import_module(module_map[name], parent), name)
    return globals()[name]
