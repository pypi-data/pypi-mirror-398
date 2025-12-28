import logging
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._async.helpers.create_d1_client import create_d1_client
    from ._async.models.d1_client import D1Client
    from ._settings import D1Settings, settings_manager

__all__ = [
    # ._async.helpers
    "create_d1_client",
    # ._async.models
    "D1Client",
    # .settings
    "D1Settings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._async.helpers
        "create_d1_client": "._async.helpers.create_d1_client",
        # ._async.models
        "D1Client": "._async.models.d1_client",
        # .settings
        "D1Settings": ".settings",
        "settings_manager": ".settings",
    }

    parent = __name__.rsplit(".", 1)[0]
    globals()[name] = getattr(import_module(module_map[name], parent), name)
    return globals()[name]
