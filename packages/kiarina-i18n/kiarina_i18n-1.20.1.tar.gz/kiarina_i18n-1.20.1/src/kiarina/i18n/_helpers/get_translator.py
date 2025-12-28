from .._models.translator import Translator
from .._settings import settings_manager
from .._types.i18n_scope import I18nScope
from .._types.language import Language
from .get_catalog import get_catalog


def get_translator(language: Language, scope: I18nScope) -> Translator:
    """Get a translator for the specified language and scope.

    Args:
        language: Target language for translation.
        scope: Scope for translation keys (e.g., "kiarina.app.greeting").

    Returns:
        Translator instance configured for the specified language and scope.

    Example:
        >>> t = get_translator("ja", "app.greeting")
        >>> t("hello", name="World")
        'こんにちは、World!'
    """
    settings = settings_manager.settings
    catalog = get_catalog()
    return Translator(
        catalog=catalog,
        language=language,
        scope=scope,
        fallback_language=settings.default_language,
    )
