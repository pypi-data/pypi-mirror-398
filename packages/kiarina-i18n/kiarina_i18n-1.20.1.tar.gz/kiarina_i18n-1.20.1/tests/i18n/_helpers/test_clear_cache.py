import yaml

from kiarina.i18n import clear_cache, get_catalog, get_translator, settings_manager


def test_clear_cache_clears_catalog_file_cache(tmp_path):
    """Test that clear_cache clears catalog file loading cache."""
    # Create catalog file
    catalog_file = tmp_path / "catalog.yaml"
    catalog_v1 = {"en": {"app": {"title": "Title V1"}}}
    with open(catalog_file, "w", encoding="utf-8") as f:
        yaml.dump(catalog_v1, f)

    # Setup to use catalog file
    settings_manager.user_config = {"catalog_file": str(catalog_file)}

    # Load catalog (will be cached)
    catalog1 = get_catalog()
    assert catalog1["en"]["app"]["title"] == "Title V1"

    # Modify file
    catalog_v2 = {"en": {"app": {"title": "Title V2"}}}
    with open(catalog_file, "w", encoding="utf-8") as f:
        yaml.dump(catalog_v2, f)

    # Without clear_cache, should return cached value
    catalog2 = get_catalog()
    assert catalog2["en"]["app"]["title"] == "Title V1"  # Still cached

    # Clear cache
    clear_cache()

    # Should load new value from file
    catalog3 = get_catalog()
    assert catalog3["en"]["app"]["title"] == "Title V2"


def test_settings_changes_reflected_immediately():
    """Test that settings changes are reflected immediately (no caching)."""
    # Setup catalog
    settings_manager.user_config = {
        "catalog": {
            "en": {"app": {"title": "Title"}},
        }
    }

    # Get catalog
    catalog1 = get_catalog()
    assert catalog1["en"]["app"]["title"] == "Title"

    # Modify settings
    settings_manager.user_config = {
        "catalog": {
            "en": {"app": {"title": "New Title"}},
        }
    }

    # Should immediately reflect new settings (no cache)
    catalog2 = get_catalog()
    assert catalog2["en"]["app"]["title"] == "New Title"


def test_clear_cache_multiple_calls():
    """Test that clear_cache can be called multiple times safely."""
    settings_manager.user_config = {
        "catalog": {
            "en": {"app": {"title": "Title"}},
        }
    }

    # Populate caches
    get_catalog()
    get_translator("en", "app")

    # Clear multiple times (should not raise errors)
    clear_cache()
    clear_cache()
    clear_cache()

    # Should still work
    catalog = get_catalog()
    assert catalog["en"]["app"]["title"] == "Title"


def test_clear_cache_with_empty_caches():
    """Test that clear_cache works even when caches are empty."""
    # Clear without populating caches (should not raise errors)
    clear_cache()

    # Should still work
    settings_manager.user_config = {
        "catalog": {
            "en": {"app": {"title": "Title"}},
        }
    }
    catalog = get_catalog()
    assert catalog["en"]["app"]["title"] == "Title"
