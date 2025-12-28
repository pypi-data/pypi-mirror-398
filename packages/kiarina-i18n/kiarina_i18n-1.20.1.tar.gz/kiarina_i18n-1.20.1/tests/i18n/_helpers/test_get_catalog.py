from kiarina.i18n import get_catalog, settings_manager


def test_get_catalog_from_settings(sample_catalog):
    """Test get_catalog returns catalog from settings."""
    settings_manager.user_config = {"catalog": sample_catalog}

    catalog = get_catalog()
    assert catalog == sample_catalog
    assert catalog["en"]["app.greeting"]["hello"] == "Hello, $name!"
    assert catalog["ja"]["app.greeting"]["hello"] == "こんにちは、$name!"


def test_get_catalog_returns_settings_catalog(sample_catalog):
    """Test that get_catalog returns catalog from settings (no caching)."""
    settings_manager.user_config = {"catalog": sample_catalog}

    catalog1 = get_catalog()
    catalog2 = get_catalog()

    assert catalog1 is catalog2


def test_get_catalog_from_file(tmp_path, sample_catalog):
    """Test get_catalog loads catalog from YAML file."""
    import yaml

    # Create temporary catalog file
    catalog_file = tmp_path / "catalog.yaml"
    with open(catalog_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_catalog, f)

    # Configure to use file
    settings_manager.user_config = {"catalog_file": str(catalog_file)}

    catalog = get_catalog()
    assert catalog == sample_catalog


def test_get_catalog_empty():
    """Test get_catalog returns empty dict when no catalog is configured."""
    settings_manager.user_config = {}

    catalog = get_catalog()
    assert catalog == {}


def test_get_catalog_independent_usage():
    """Test that get_catalog can be used independently."""
    # This test demonstrates that get_catalog can be used
    # without get_translator
    settings_manager.user_config = {
        "catalog": {
            "en": {"app": {"title": "My App"}},
            "ja": {"app": {"title": "マイアプリ"}},
        }
    }

    catalog = get_catalog()

    # Direct access to catalog
    assert catalog["en"]["app"]["title"] == "My App"
    assert catalog["ja"]["app"]["title"] == "マイアプリ"

    # Can be used for custom translation logic
    def custom_translate(lang: str, scope: str, key: str) -> str:
        return catalog.get(lang, {}).get(scope, {}).get(key, "")

    assert custom_translate("en", "app", "title") == "My App"
    assert custom_translate("ja", "app", "title") == "マイアプリ"
