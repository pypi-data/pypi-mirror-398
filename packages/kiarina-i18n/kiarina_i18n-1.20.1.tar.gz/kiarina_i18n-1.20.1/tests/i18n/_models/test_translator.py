from kiarina.i18n import Translator


def test_translator_basic(sample_catalog):
    """Test basic translation."""
    t = Translator(catalog=sample_catalog, language="en", scope="app.greeting")
    assert t("hello", name="World") == "Hello, World!"
    assert t("goodbye") == "Goodbye!"


def test_translator_japanese(sample_catalog):
    """Test Japanese translation."""
    t = Translator(catalog=sample_catalog, language="ja", scope="app.greeting")
    assert t("hello", name="世界") == "こんにちは、世界!"
    assert t("goodbye") == "さようなら!"


def test_translator_fallback(sample_catalog):
    """Test fallback to English when translation is not found."""
    # Remove Japanese translation for "goodbye"
    del sample_catalog["ja"]["app.greeting"]["goodbye"]

    t = Translator(
        catalog=sample_catalog,
        language="ja",
        scope="app.greeting",
        fallback_language="en",
    )
    assert t("goodbye") == "Goodbye!"


def test_translator_default(sample_catalog):
    """Test default value when translation is not found."""
    t = Translator(catalog=sample_catalog, language="en", scope="app.greeting")
    assert t("unknown", default="Default text") == "Default text"


def test_translator_missing_key(sample_catalog):
    """Test behavior when key is missing and no default is provided."""
    t = Translator(catalog=sample_catalog, language="en", scope="app.greeting")
    result = t("unknown")
    assert result == "app.greeting#unknown"


def test_translator_template_substitution(sample_catalog):
    """Test template variable substitution."""
    t = Translator(catalog=sample_catalog, language="en", scope="app.greeting")
    assert t("hello", name="Alice") == "Hello, Alice!"
    assert t("hello", name="Bob") == "Hello, Bob!"


def test_translator_different_scope(sample_catalog):
    """Test translation with different scope."""
    t = Translator(catalog=sample_catalog, language="en", scope="app.error")
    assert t("not_found") == "Not found"

    t_ja = Translator(catalog=sample_catalog, language="ja", scope="app.error")
    assert t_ja("not_found") == "見つかりません"
