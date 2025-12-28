import pytest
from pydantic import BaseModel, Field

from kiarina.i18n import settings_manager
from kiarina.i18n_pydantic import translate_pydantic_model


def test_translate_pydantic_model_basic():
    """Test basic translation of Pydantic model field descriptions."""

    class Hoge(BaseModel):
        """
        Hoge model for testing.
        """

        name: str = Field(description="Your Name")
        age: int = Field(description="Your Age")

    # Configure catalog
    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "name": "あなたの名前",
                    "age": "あなたの年齢",
                }
            }
        }
    }

    # Translate model
    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Check translated descriptions
    assert HogeJa.model_fields["name"].description == "あなたの名前"
    assert HogeJa.model_fields["age"].description == "あなたの年齢"


def test_translate_pydantic_model_preserves_types():
    """Test that translation preserves field types."""

    class Hoge(BaseModel):
        name: str = Field(description="Your Name")
        age: int = Field(description="Your Age")
        active: bool = Field(default=True, description="Is Active")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "name": "名前",
                    "age": "年齢",
                    "active": "アクティブ",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Check field types are preserved
    assert HogeJa.model_fields["name"].annotation is str
    assert HogeJa.model_fields["age"].annotation is int
    assert HogeJa.model_fields["active"].annotation is bool


def test_translate_pydantic_model_preserves_defaults():
    """Test that translation preserves default values."""

    class Hoge(BaseModel):
        name: str = Field(default="Anonymous", description="Your Name")
        age: int = Field(default=0, description="Your Age")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "name": "名前",
                    "age": "年齢",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Check defaults are preserved
    assert HogeJa.model_fields["name"].default == "Anonymous"
    assert HogeJa.model_fields["age"].default == 0

    # Create instance without arguments
    instance = HogeJa()
    assert instance.name == "Anonymous"
    assert instance.age == 0


def test_translate_pydantic_model_fallback_to_original():
    """Test that missing translations fall back to original descriptions."""

    class Hoge(BaseModel):
        name: str = Field(description="Your Name")
        age: int = Field(description="Your Age")

    # Only translate 'name', not 'age'
    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "name": "名前",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # 'name' should be translated
    assert HogeJa.model_fields["name"].description == "名前"
    # 'age' should fall back to original
    assert HogeJa.model_fields["age"].description == "Your Age"


def test_translate_pydantic_model_validation_works():
    """Test that validation still works on translated model."""

    class Hoge(BaseModel):
        name: str = Field(min_length=1, description="Your Name")
        age: int = Field(ge=0, description="Your Age")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "name": "名前",
                    "age": "年齢",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Valid instance
    instance = HogeJa(name="Alice", age=30)
    assert instance.name == "Alice"
    assert instance.age == 30

    # Invalid: empty name
    with pytest.raises(Exception):  # ValidationError
        HogeJa(name="", age=30)

    # Invalid: negative age
    with pytest.raises(Exception):  # ValidationError
        HogeJa(name="Alice", age=-1)


def test_translate_pydantic_model_json_schema():
    """Test that translated descriptions appear in JSON schema."""

    class Hoge(BaseModel):
        name: str = Field(description="Your Name")
        age: int = Field(description="Your Age")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "name": "あなたの名前",
                    "age": "あなたの年齢",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Get JSON schema
    schema = HogeJa.model_json_schema()

    # Check translated descriptions in schema
    assert schema["properties"]["name"]["description"] == "あなたの名前"
    assert schema["properties"]["age"]["description"] == "あなたの年齢"


def test_translate_pydantic_model_multiple_languages():
    """Test translating the same model to multiple languages."""

    class Hoge(BaseModel):
        name: str = Field(description="Your Name")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {"hoge.fields": {"name": "名前"}},
            "fr": {"hoge.fields": {"name": "Votre nom"}},
            "es": {"hoge.fields": {"name": "Tu nombre"}},
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")
    HogeFr = translate_pydantic_model(Hoge, "fr", "hoge.fields")
    HogeEs = translate_pydantic_model(Hoge, "es", "hoge.fields")

    assert HogeJa.model_fields["name"].description == "名前"
    assert HogeFr.model_fields["name"].description == "Votre nom"
    assert HogeEs.model_fields["name"].description == "Tu nombre"


def test_translate_pydantic_model_preserves_model_config():
    """Test that model configuration is preserved."""

    class Hoge(BaseModel):
        model_config = {"frozen": True, "extra": "forbid"}

        name: str = Field(description="Your Name")

    settings_manager.cli_args = {"catalog": {"ja": {"hoge.fields": {"name": "名前"}}}}

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Check model config is preserved
    assert HogeJa.model_config.get("frozen") is True
    assert HogeJa.model_config.get("extra") == "forbid"

    # Test frozen behavior
    instance = HogeJa(name="Alice")
    with pytest.raises(Exception):  # ValidationError
        instance.name = "Bob"  # type: ignore


def test_translate_pydantic_model_with_i18n_subclass():
    """Test translating I18n subclass without explicit scope."""
    from kiarina.i18n import I18n

    class HogeI18n(I18n, scope="hoge.i18n"):
        name: str = "Your Name"
        age: str = "Your Age"

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.i18n": {
                    "name": "あなたの名前",
                    "age": "あなたの年齢",
                }
            }
        }
    }

    # Translate without explicit scope (should use model._scope)
    HogeI18nJa = translate_pydantic_model(HogeI18n, "ja")

    # Check translated descriptions
    assert HogeI18nJa.model_fields["name"].description == "あなたの名前"
    assert HogeI18nJa.model_fields["age"].description == "あなたの年齢"


def test_translate_pydantic_model_with_i18n_subclass_explicit_scope():
    """Test that explicit scope overrides I18n subclass scope."""
    from kiarina.i18n import I18n

    class HogeI18n(I18n, scope="hoge.i18n"):
        name: str = "Your Name"

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.i18n": {"name": "I18nスコープ"},
                "custom.scope": {"name": "カスタムスコープ"},
            }
        }
    }

    # With explicit scope (should override model._scope)
    HogeI18nJa = translate_pydantic_model(HogeI18n, "ja", "custom.scope")

    # Should use custom scope, not model._scope
    assert HogeI18nJa.model_fields["name"].description == "カスタムスコープ"


def test_translate_pydantic_model_without_scope_raises_error():
    """Test that omitting scope for non-I18n model raises error."""

    class Hoge(BaseModel):
        name: str = Field(description="Your Name")

    settings_manager.cli_args = {"catalog": {"ja": {"hoge.fields": {"name": "名前"}}}}

    # Should raise ValueError when scope is omitted for non-I18n model
    with pytest.raises(ValueError, match="scope parameter is required"):
        translate_pydantic_model(Hoge, "ja")  # type: ignore


def test_translate_pydantic_model_i18n_with_auto_scope():
    """Test I18n subclass with auto-generated scope."""
    from kiarina.i18n import I18n

    # Auto-generated scope will be: tests.i18n_pydantic._helpers.test_translate_pydantic_model.UserI18n
    class UserI18n(I18n):
        name: str = "Name"
        email: str = "Email"

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "tests.i18n_pydantic._helpers.test_translate_pydantic_model.UserI18n": {
                    "name": "名前",
                    "email": "メールアドレス",
                }
            }
        }
    }

    # Translate without explicit scope
    UserI18nJa = translate_pydantic_model(UserI18n, "ja")

    # Check translated descriptions
    assert UserI18nJa.model_fields["name"].description == "名前"
    assert UserI18nJa.model_fields["email"].description == "メールアドレス"


def test_translate_pydantic_model_translates_docstring():
    """Test that __doc__ is translated."""

    class Hoge(BaseModel):
        """
        Hoge model for testing.
        """

        name: str = Field(description="Your Name")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "__doc__": "テスト用のHogeモデル。",
                    "name": "あなたの名前",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Check translated __doc__
    assert HogeJa.__doc__ == "テスト用のHogeモデル。"
    assert HogeJa.model_fields["name"].description == "あなたの名前"


def test_translate_pydantic_model_docstring_fallback():
    """Test that __doc__ falls back to original when translation is missing."""

    class Hoge(BaseModel):
        """Original documentation."""

        name: str = Field(description="Your Name")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    # __doc__ translation is missing
                    "name": "あなたの名前",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Should fall back to original __doc__
    assert HogeJa.__doc__ == "Original documentation."
    assert HogeJa.model_fields["name"].description == "あなたの名前"


def test_translate_pydantic_model_without_docstring():
    """Test translation when model has no __doc__."""

    class Hoge(BaseModel):
        name: str = Field(description="Your Name")

    settings_manager.cli_args = {
        "catalog": {
            "ja": {
                "hoge.fields": {
                    "__doc__": "追加されたドキュメント",
                    "name": "あなたの名前",
                }
            }
        }
    }

    HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

    # Should use translated __doc__ even if original is None
    assert HogeJa.__doc__ == "追加されたドキュメント"
    assert HogeJa.model_fields["name"].description == "あなたの名前"
