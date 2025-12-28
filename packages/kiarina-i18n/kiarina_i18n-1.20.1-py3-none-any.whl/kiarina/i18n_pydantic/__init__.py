import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ._helpers.translate_pydantic_model import translate_pydantic_model

__version__ = version("kiarina-i18n")

__all__ = [
    # ._helpers
    "translate_pydantic_model",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._helpers
        "translate_pydantic_model": "._helpers.translate_pydantic_model",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
