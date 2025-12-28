from typing import Any

from pydantic import BaseModel


class I18n(BaseModel):
    """
    Base class for i18n definitions.

    This class provides a type-safe way to define translation keys and default values.
    Subclasses can optionally define a scope using class inheritance parameter.
    If scope is not provided, it will be automatically generated from module and class name.

    Example:
        ```python
        from kiarina.i18n import I18n, get_i18n

        # Explicit scope
        class MyI18n(I18n, scope="my.module"):
            title: str = "My Title"
            description: str = "My Description"

        # Auto-generated scope (my.app.UserProfileI18n)
        class UserProfileI18n(I18n):
            name: str = "Name"
            email: str = "Email"

        # Get translated instance
        t = get_i18n(MyI18n, "ja")
        print(t.title)  # Translated title
        ```
    """

    _scope: str = ""  # Internal field for scope, set via __init_subclass__

    def __init_subclass__(cls, scope: str = "", **kwargs: Any) -> None:
        """
        Set scope when subclass is defined.

        If scope is not provided, automatically generates it from module and class name.
        Example: module.path.MyI18n -> module.path.MyI18n
        """
        super().__init_subclass__(**kwargs)

        if scope:
            cls._scope = scope
        else:
            # Generate scope from module and class name (as-is)
            module_name = cls.__module__
            class_name = cls.__name__
            cls._scope = f"{module_name}.{class_name}"

    model_config = {
        "frozen": True,  # Make instances immutable
        "extra": "forbid",  # Forbid extra fields
    }
