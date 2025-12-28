from typing import TypeAlias

from .i18n_key import I18nKey
from .i18n_scope import I18nScope
from .language import Language

Catalog: TypeAlias = dict[Language, dict[I18nScope, dict[I18nKey, str]]]
