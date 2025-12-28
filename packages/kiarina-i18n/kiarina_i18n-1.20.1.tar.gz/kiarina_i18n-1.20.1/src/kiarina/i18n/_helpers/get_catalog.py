from .._operations.load_catalog_file import load_catalog_file
from .._settings import settings_manager
from .._types.catalog import Catalog


def get_catalog() -> Catalog:
    """
    Get the translation catalog from settings.

    Returns:
        Translation catalog loaded from file or settings.

    Example:
        ```python
        from kiarina.i18n import get_catalog, settings_manager

        # Configure catalog
        settings_manager.user_config = {
            "catalog": {
                "en": {"app.greeting": {"hello": "Hello!"}},
                "ja": {"app.greeting": {"hello": "こんにちは!"}}
            }
        }

        # Get catalog
        catalog = get_catalog()
        print(catalog["en"]["app.greeting"]["hello"])  # "Hello!"
        ```
    """
    settings = settings_manager.settings

    if settings.catalog_file is not None:
        return load_catalog_file(settings.catalog_file)
    else:
        return settings.catalog
