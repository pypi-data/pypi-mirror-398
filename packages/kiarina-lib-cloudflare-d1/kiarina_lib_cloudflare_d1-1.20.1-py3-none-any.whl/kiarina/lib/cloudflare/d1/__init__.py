import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._sync.helpers.create_d1_client import create_d1_client
    from ._sync.models.d1_client import D1Client
    from ._settings import D1Settings, settings_manager

__version__ = version("kiarina-lib-cloudflare-d1")

__all__ = [
    # ._sync.helpers
    "create_d1_client",
    # ._sync.models
    "D1Client",
    # ._settings
    "D1Settings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._sync.helpers
        "create_d1_client": "._sync.helpers.create_d1_client",
        # ._sync.models
        "D1Client": "._sync.models.d1_client",
        # ._settings
        "D1Settings": "._settings",
        "settings_manager": "._settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
