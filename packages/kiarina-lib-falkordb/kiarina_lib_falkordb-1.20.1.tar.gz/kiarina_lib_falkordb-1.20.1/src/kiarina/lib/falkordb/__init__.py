import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._sync.helpers.get_falkordb import get_falkordb
    from ._settings import FalkorDBSettings, settings_manager

__version__ = version("kiarina-lib-falkordb")

__all__ = [
    # ._sync._helpers
    "get_falkordb",
    # ._settings
    "FalkorDBSettings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._sync.helpers
        "get_falkordb": "._sync.helpers.get_falkordb",
        # ._settings
        "FalkorDBSettings": "._settings",
        "settings_manager": "._settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
