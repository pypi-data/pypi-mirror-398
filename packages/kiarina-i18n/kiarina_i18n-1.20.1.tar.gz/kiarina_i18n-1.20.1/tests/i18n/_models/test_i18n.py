import pytest

from kiarina.i18n import I18n


def test_i18n_class_definition():
    """Test that I18n class can be subclassed with scope parameter."""

    class MyI18n(I18n, scope="test.my"):
        title: str = "My Title"
        description: str = "My Description"

    # Create instance
    i18n = MyI18n()
    assert i18n._scope == "test.my"
    assert i18n.title == "My Title"
    assert i18n.description == "My Description"


def test_i18n_scope_as_field():
    """Test that 'scope' can be used as a regular translation key."""

    class MyI18n(I18n, scope="test.scope_field"):
        scope: str = "Default Scope Text"
        title: str = "My Title"

    # Create instance
    i18n = MyI18n()
    assert i18n._scope == "test.scope_field"  # Class-level scope
    assert i18n.scope == "Default Scope Text"  # Field-level translation key


def test_i18n_immutable():
    """Test that I18n instances are immutable."""

    class MyI18n(I18n, scope="test.my"):
        title: str = "My Title"

    i18n = MyI18n()

    # Should raise error when trying to modify
    with pytest.raises(Exception):  # ValidationError or AttributeError
        i18n.title = "New Title"  # type: ignore


def test_i18n_forbid_extra_fields():
    """Test that extra fields are forbidden."""

    class MyI18n(I18n, scope="test.my"):
        title: str = "My Title"

    # Should raise error when passing extra fields
    with pytest.raises(Exception):  # ValidationError
        MyI18n(extra_field="value")  # type: ignore


def test_i18n_auto_scope_generation():
    """Test that scope is automatically generated from module and class name."""

    class MyAppI18n(I18n):
        title: str = "My Title"

    # Scope should be auto-generated as: tests.i18n._models.test_i18n.MyAppI18n
    i18n = MyAppI18n()
    assert i18n._scope == "tests.i18n._models.test_i18n.MyAppI18n"


def test_i18n_auto_scope_with_nested_class():
    """Test auto scope generation with different class name patterns."""

    class UserProfileI18n(I18n):
        name: str = "Name"

    i18n = UserProfileI18n()
    # Should use class name as-is: UserProfileI18n
    assert i18n._scope == "tests.i18n._models.test_i18n.UserProfileI18n"


def test_i18n_explicit_scope_overrides_auto():
    """Test that explicit scope parameter overrides auto-generation."""

    class AutoI18n(I18n, scope="custom.scope"):
        title: str = "Title"

    i18n = AutoI18n()
    assert i18n._scope == "custom.scope"
