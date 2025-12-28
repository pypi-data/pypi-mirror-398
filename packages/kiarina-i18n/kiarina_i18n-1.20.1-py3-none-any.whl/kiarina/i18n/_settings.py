from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

from ._types.catalog import Catalog
from ._types.language import Language


class I18nSettings(BaseSettings):
    default_language: Language = "en"
    """Default language to use when translation is not found."""
    catalog_file: str | None = None
    """Path to YAML file containing translation catalog."""
    catalog: Catalog = Field(default_factory=dict)
    """Translation catalog mapping languages to scopes to keys to translations."""


settings_manager = SettingsManager(I18nSettings)
