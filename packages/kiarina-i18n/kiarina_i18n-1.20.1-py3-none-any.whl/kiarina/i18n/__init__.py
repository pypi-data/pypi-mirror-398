import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ._helpers.clear_cache import clear_cache
    from ._helpers.get_catalog import get_catalog
    from ._helpers.get_i18n import get_i18n
    from ._helpers.get_translator import get_translator
    from ._models.i18n import I18n
    from ._models.translator import Translator
    from ._settings import I18nSettings, settings_manager
    from ._types.catalog import Catalog
    from ._types.i18n_key import I18nKey
    from ._types.i18n_scope import I18nScope
    from ._types.language import Language

__version__ = version("kiarina-i18n")

__all__ = [
    # ._helpers
    "clear_cache",
    "get_catalog",
    "get_i18n",
    "get_translator",
    # ._models
    "I18n",
    "Translator",
    # ._settings
    "I18nSettings",
    "settings_manager",
    # ._types
    "Catalog",
    "I18nKey",
    "I18nScope",
    "Language",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._helpers
        "clear_cache": "._helpers.clear_cache",
        "get_catalog": "._helpers.get_catalog",
        "get_i18n": "._helpers.get_i18n",
        "get_translator": "._helpers.get_translator",
        # ._models
        "I18n": "._models.i18n",
        "Translator": "._models.translator",
        # ._settings
        "I18nSettings": "._settings",
        "settings_manager": "._settings",
        # ._types
        "Catalog": "._types.catalog",
        "I18nKey": "._types.i18n_key",
        "I18nScope": "._types.i18n_scope",
        "Language": "._types.language",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
