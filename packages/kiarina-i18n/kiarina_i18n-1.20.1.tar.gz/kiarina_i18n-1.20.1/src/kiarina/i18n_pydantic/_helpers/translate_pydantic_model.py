from typing import Any, TypeVar, overload

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from ...i18n._helpers.get_translator import get_translator
from ...i18n._models.i18n import I18n

T = TypeVar("T", bound=BaseModel)


@overload
def translate_pydantic_model(
    model: type[T],
    language: str,
    scope: str,
) -> type[T]: ...


@overload
def translate_pydantic_model(
    model: type[I18n],
    language: str,
    scope: None = None,
) -> type[I18n]: ...


def translate_pydantic_model(
    model: type[T],
    language: str,
    scope: str | None = None,
) -> type[T]:
    """
    Translate Pydantic model field descriptions.

    This function creates a new model class with translated field descriptions
    while preserving all other field attributes and model configuration.

    Args:
        model: Pydantic model class to translate
        language: Target language code (e.g., "ja", "en")
        scope: Translation scope (e.g., "hoge.fields").
               If model is an I18n subclass and scope is None, uses model._scope.

    Returns:
        New model class with translated field descriptions

    Example:
        ```python
        # With explicit scope
        from pydantic import BaseModel, Field
        from kiarina.i18n import translate_pydantic_model, settings_manager

        class Hoge(BaseModel):
            name: str = Field(description="Your Name")
            age: int = Field(description="Your Age")

        # Configure catalog
        settings_manager.user_config = {
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
        print(HogeJa.model_fields["name"].description)  # "あなたの名前"

        # With I18n subclass (scope auto-detected)
        from kiarina.i18n import I18n

        class HogeI18n(I18n, scope="hoge.fields"):
            name: str = "Your Name"
            age: str = "Your Age"

        HogeI18nJa = translate_pydantic_model(HogeI18n, "ja")
        print(HogeI18nJa.model_fields["name"].description)  # "あなたの名前"
        ```
    """
    # Auto-detect scope from I18n subclass
    if scope is None:
        if issubclass(model, I18n):
            scope = model._scope
        else:
            raise ValueError(
                "scope parameter is required when model is not an I18n subclass"
            )

    translator = get_translator(language, scope)

    # Translate __doc__ (use original as fallback)
    original_doc = model.__doc__ or ""
    translated_doc = translator("__doc__", default=original_doc)

    # Build new fields with translated descriptions
    new_fields: dict[str, Any] = {}

    for field_name, field_info in model.model_fields.items():
        # Translate description (use original as fallback)
        original_desc = field_info.description or ""
        translated_desc = translator(field_name, default=original_desc)

        # Create a copy of the field info with translated description
        # We create a new FieldInfo by copying the original and updating description
        annotation = field_info.annotation if field_info.annotation is not None else Any
        new_field_info = FieldInfo.from_annotation(annotation)

        # Copy all attributes from original field
        for attr in dir(field_info):
            if not attr.startswith("_") and attr not in ("annotation", "description"):
                try:
                    value = getattr(field_info, attr)
                    if not callable(value):
                        setattr(new_field_info, attr, value)
                except (AttributeError, TypeError):
                    pass

        # Set translated description
        new_field_info.description = translated_desc

        new_fields[field_name] = (field_info.annotation, new_field_info)

    # Create new model with translated fields
    # Preserve model config
    translated_model = create_model(
        model.__name__,
        __config__=model.model_config,
        __doc__=translated_doc,
        __base__=model.__base__,
        __module__=model.__module__,
        **new_fields,
    )

    return translated_model  # type: ignore
