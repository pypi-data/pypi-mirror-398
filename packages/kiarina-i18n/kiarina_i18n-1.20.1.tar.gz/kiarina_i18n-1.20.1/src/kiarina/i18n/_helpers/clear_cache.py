from .._operations.load_catalog_file import load_catalog_file


def clear_cache() -> None:
    """
    Clear all i18n-related caches.

    This function clears the catalog file loading cache.
    Useful when you need to reload configuration or reset state during testing.

    Example:
        ```python
        from kiarina.i18n import clear_cache, settings_manager

        # Change settings
        settings_manager.user_config = {"catalog_file": "new_catalog.yaml"}

        # Clear caches to apply new settings
        clear_cache()
        ```
    """
    load_catalog_file.cache_clear()
