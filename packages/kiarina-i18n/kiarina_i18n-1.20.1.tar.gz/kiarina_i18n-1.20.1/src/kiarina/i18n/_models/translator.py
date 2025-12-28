import logging
from string import Template
from typing import Any

from .._types.catalog import Catalog
from .._types.i18n_key import I18nKey
from .._types.i18n_scope import I18nScope
from .._types.language import Language

logger = logging.getLogger(__name__)


class Translator:
    """Translator for internationalization (i18n) support.

    This class provides translation functionality with fallback support.
    It supports template substitution using Python's string.Template.

    Args:
        catalog: Translation catalog mapping languages to scopes to keys to translations.
        language: Target language for translation.
        scope: Scope for translation keys (e.g., "kiarina.app.greeting").
        fallback_language: Fallback language when translation is not found.

    Example:
        >>> catalog = {
        ...     "en": {"app.greeting": {"hello": "Hello, $name!"}},
        ...     "ja": {"app.greeting": {"hello": "こんにちは、$name!"}}
        ... }
        >>> t = Translator(catalog=catalog, language="ja", scope="app.greeting")
        >>> t("hello", name="World")
        'こんにちは、World!'
    """

    def __init__(
        self,
        *,
        catalog: Catalog,
        language: Language,
        scope: I18nScope,
        fallback_language: Language = "en",
    ) -> None:
        self.catalog = catalog
        self.language = language
        self.scope = scope
        self.fallback_language = fallback_language

    def __call__(self, key: I18nKey, default: str | None = None, **kwargs: Any) -> str:
        """Translate a key to the target language.

        Args:
            key: Translation key.
            default: Default text to use if translation is not found.
            **kwargs: Template variables for substitution.

        Returns:
            Translated text with template variables substituted.
        """
        text = self._get_text(self.language, self.scope, key)

        if text is None and self.language != self.fallback_language:
            text = self._get_text(self.fallback_language, self.scope, key)

        if text is None:
            text = default

        if text is None:
            logger.error(
                f"Translation not found for key '{key}' in scope '{self.scope}' "
                f"and language '{self.language}'"
            )

            text = f"{self.scope}#{key}"

        if kwargs:
            return Template(text).safe_substitute(**kwargs)

        return text

    def _get_text(
        self,
        language: Language,
        scope: I18nScope,
        key: I18nKey,
    ) -> str | None:
        return self.catalog.get(language, {}).get(scope, {}).get(key)
