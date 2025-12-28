from typing import TypeVar

from .._models.i18n import I18n
from .get_translator import get_translator

T = TypeVar("T", bound=I18n)


def get_i18n(i18n_class: type[T], language: str) -> T:
    """
    Get translated i18n instance.

    This function creates an instance of the given i18n class with all fields
    translated to the specified language.

    Args:
        i18n_class: I18n class to instantiate (not instance!)
        language: Target language code (e.g., "en", "ja")

    Returns:
        Translated i18n instance with all fields translated

    Example:
        ```python
        from kiarina.i18n import I18n, get_i18n

        class MyI18n(I18n, scope="my.module"):
            title: str = "My Title"
            description: str = "My Description"

        # Get translated instance
        t = get_i18n(MyI18n, "ja")
        print(t.title)  # Translated title in Japanese
        print(t.description)  # Translated description in Japanese
        ```
    """
    # Get scope from class attribute
    scope = i18n_class._scope

    # Create default instance to get default values
    default_instance = i18n_class.model_construct()

    # Get translator for the scope
    translator = get_translator(language, scope)

    # Translate all fields
    translated_data = {}
    for field_name in i18n_class.model_fields:
        default_value = getattr(default_instance, field_name)
        translated_data[field_name] = translator(field_name, default=default_value)

    return i18n_class(**translated_data)
