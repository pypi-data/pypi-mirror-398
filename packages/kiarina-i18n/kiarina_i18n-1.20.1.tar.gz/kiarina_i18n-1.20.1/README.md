# kiarina-i18n

Simple internationalization (i18n) utilities for Python applications.

## Purpose

`kiarina-i18n` provides a lightweight and straightforward approach to internationalization in Python applications.
It focuses on simplicity and predictability, avoiding complex grammar rules or plural forms.

For applications requiring advanced features like plural forms or complex localization,
consider using established tools like `gettext`.

## Installation

```bash
pip install kiarina-i18n
```

## Quick Start

### Basic Usage (Functional API)

```python
from kiarina.i18n import get_translator, settings_manager

# Configure the catalog
settings_manager.user_config = {
    "catalog": {
        "en": {
            "app.greeting": {
                "hello": "Hello, $name!",
                "goodbye": "Goodbye!"
            }
        },
        "ja": {
            "app.greeting": {
                "hello": "こんにちは、$name!",
                "goodbye": "さようなら!"
            }
        }
    }
}

# Get a translator
t = get_translator("ja", "app.greeting")

# Translate with template variables
print(t("hello", name="World"))  # Output: こんにちは、World!
print(t("goodbye"))  # Output: さようなら!
```

### Type-Safe Class-Based API (Recommended)

For better type safety and IDE support, use the class-based API:

```python
from kiarina.i18n import I18n, get_i18n, settings_manager

# Define your i18n class with explicit scope
class AppI18n(I18n, scope="app.greeting"):
    hello: str = "Hello, $name!"
    goodbye: str = "Goodbye!"
    welcome: str = "Welcome to our app!"

# Or let scope be auto-generated from module.class_name
# If defined in my_app/i18n.py, scope will be: my_app.i18n.UserProfileI18n
class UserProfileI18n(I18n):
    name: str = "Name"
    email: str = "Email"
    bio: str = "Biography"

# Configure the catalog
settings_manager.user_config = {
    "catalog": {
        "ja": {
            "app.greeting": {
                "hello": "こんにちは、$name!",
                "goodbye": "さようなら!",
                "welcome": "アプリへようこそ!"
            }
        }
    }
}

# Get translated instance
t = get_i18n(AppI18n, "ja")

# Access translations with full type safety and IDE completion
print(t.hello)     # Output: こんにちは、$name!
print(t.goodbye)   # Output: さようなら!
print(t.welcome)   # Output: アプリへようこそ!

# Template variables are handled by the functional API
from kiarina.i18n import get_translator
translator = get_translator("ja", "app.greeting")
print(translator("hello", name="World"))  # Output: こんにちは、World!
```

**Benefits of Class-Based API:**
- **Type Safety**: IDE detects typos in field names
- **Auto-completion**: IDE suggests available translation keys
- **Self-documenting**: Class definition serves as documentation
- **Default Values**: Explicit fallback values when translation is missing
- **Immutable**: Translation instances are frozen and cannot be modified
- **Clean Syntax**: Scope is defined at class level, not as a field

### Using Catalog File

```python
from kiarina.i18n import get_translator, settings_manager

# Load catalog from YAML file
settings_manager.user_config = {
    "catalog_file": "i18n_catalog.yaml"
}

t = get_translator("en", "app.greeting")
print(t("hello", name="Alice"))
```

Example `i18n_catalog.yaml`:

```yaml
en:
  app.greeting:
    hello: "Hello, $name!"
    goodbye: "Goodbye!"
ja:
  app.greeting:
    hello: "こんにちは、$name!"
    goodbye: "さようなら!"
```

### Pydantic Integration for LLM Tools

For LLM tool schemas, use `translate_pydantic_model` to create language-specific tool schemas at runtime:

```python
from pydantic import Field
from langchain.tools import BaseTool, tool
from kiarina.i18n import I18n, get_i18n, settings_manager
from kiarina.i18n_pydantic import translate_pydantic_model

# Step 1: Define argument schema with I18n
class ArgsSchema(I18n, scope="hoge_tool.args_schema"):
    """Hoge tool for processing data."""
    name: str = Field(description="Your Name")
    age: int = Field(description="Your Age")

# Step 2: Define tool with default schema
@tool(args_schema=ArgsSchema)
def hoge_tool(name: str, age: int) -> str:
    """Process user data"""
    return f"Processed: {name}, {age}"

# Step 3: Configure translations
settings_manager.user_config = {
    "catalog": {
        "ja": {
            "hoge_tool.args_schema": {
                "__doc__": "データ処理用のHogeツール。",
                "name": "あなたの名前",
                "age": "あなたの年齢",
            }
        },
        "en": {
            "hoge_tool.args_schema": {
                "__doc__": "Hoge tool for processing data.",
                "name": "Your Name",
                "age": "Your Age",
            }
        }
    }
}

# Step 4: Create language-specific tools at runtime
def get_tool(language: str) -> BaseTool:
    """Get tool with translated schema for the specified language."""
    # Translate the schema (scope is auto-detected from I18n subclass)
    translated_schema = translate_pydantic_model(hoge_tool.args_schema, language)

    # Create a copy of the tool with translated schema
    translated_tool = hoge_tool.model_copy(update={"args_schema": translated_schema})

    return translated_tool

# Step 5: Use language-specific tools
tool_ja = get_tool("ja")  # Japanese version
tool_en = get_tool("en")  # English version

# The tool schema will have language-specific descriptions
schema_ja = tool_ja.args_schema.model_json_schema()
print(tool_ja.args_schema.__doc__)  # "データ処理用のHogeツール。"
print(schema_ja["properties"]["name"]["description"])  # "あなたの名前"

schema_en = tool_en.args_schema.model_json_schema()
print(tool_en.args_schema.__doc__)  # "Hoge tool for processing data."
print(schema_en["properties"]["name"]["description"])  # "Your Name"
```

**Benefits:**
- **Simple Structure**: ArgsSchema is both I18n and Pydantic model
- **Type Safety**: Full IDE completion for field names and types
- **Dynamic Translation**: Schema is translated at runtime with `translate_pydantic_model`
- **Clean Syntax**: Scope is defined at class level
- **Easy Translation**: Single catalog entry covers all translations

## API Reference

### Class-Based API

#### `I18n`

Base class for defining i18n translations with type safety.

**Usage:**
```python
from kiarina.i18n import I18n

# Explicit scope
class MyI18n(I18n, scope="my.module"):
    title: str = "Default Title"
    description: str = "Default Description"

# Auto-generated scope (from module.class_name)
# If defined in my_app/i18n.py, scope will be: my_app.i18n.UserProfileI18n
class UserProfileI18n(I18n):
    name: str = "Name"
    email: str = "Email"
```

**Features:**
- **Immutable**: Instances are frozen and cannot be modified
- **Type-safe**: Full type hints and validation
- **Self-documenting**: Field names are translation keys, field values are defaults
- **Clean Syntax**: Scope is defined at class level using inheritance parameter
- **Auto-scope**: Automatically generates scope from module and class name if not provided

#### `get_i18n(i18n_class: type[T], language: str) -> T`

Get a translated i18n instance.

**Parameters:**
- `i18n_class`: I18n class to instantiate (not instance!)
- `language`: Target language code (e.g., "en", "ja")

**Returns:**
- Translated i18n instance with all fields translated

**Example:**
```python
from kiarina.i18n import I18n, get_i18n

class AppI18n(I18n, scope="app"):
    title: str = "My App"

t = get_i18n(AppI18n, "ja")
print(t.title)  # Translated title
```

### Pydantic Model Translation (kiarina.i18n_pydantic)

#### `translate_pydantic_model(model: type[T], language: str, scope: str | None = None) -> type[T]`

Translate Pydantic model field descriptions.

**Parameters:**
- `model`: Pydantic model class to translate
- `language`: Target language code (e.g., "ja", "en")
- `scope`: Translation scope (e.g., "hoge.fields"). Optional if `model` is an `I18n` subclass (automatically uses `model._scope`)

**Returns:**
- New model class with translated field descriptions

**Example:**
```python
from pydantic import BaseModel, Field
from kiarina.i18n import I18n, translate_pydantic_model

# With explicit scope (for regular BaseModel)
class Hoge(BaseModel):
    name: str = Field(description="Your Name")

HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

# With I18n subclass (scope auto-detected)
class HogeI18n(I18n, scope="hoge.fields"):
    name: str = "Your Name"

HogeI18nJa = translate_pydantic_model(HogeI18n, "ja")  # scope is optional
```

### Cache Management

#### `clear_cache() -> None`

Clear all i18n-related caches.

This function clears the catalog file loading cache.
Only file I/O operations are cached for performance.
Settings changes are reflected immediately without requiring cache clearing.

**Example:**
```python
from kiarina.i18n import clear_cache, settings_manager

# When using catalog_file, clear cache to reload from file
settings_manager.user_config = {"catalog_file": "new_catalog.yaml"}
clear_cache()  # Reload catalog from new file

# When using in-memory catalog, changes are immediate (no cache clearing needed)
settings_manager.user_config = {"catalog": {...}}
# No need to call clear_cache() - changes are immediately reflected
```

### Functional API

#### `get_catalog() -> Catalog`

Get the translation catalog from settings.

When using `catalog_file`, file I/O is cached for performance. When using in-memory `catalog`, settings changes are reflected immediately. This function can be used independently for custom translation logic or direct catalog access.

**Returns:**
- `Catalog`: Translation catalog loaded from file or settings

**Example:**
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

# Use for custom translation logic
def custom_translate(lang: str, scope: str, key: str) -> str:
    return catalog.get(lang, {}).get(scope, {}).get(key, "")

print(custom_translate("ja", "app.greeting", "hello"))  # "こんにちは!"
```

#### `get_translator(language: str, scope: str) -> Translator`

Get a translator for the specified language and scope.

**Parameters:**
- `language`: Target language code (e.g., "en", "ja", "fr")
- `scope`: Translation scope (e.g., "app.greeting", "app.error")

**Returns:**
- `Translator`: Translator instance configured for the specified language and scope

**Example:**
```python
t = get_translator("ja", "app.greeting")
```

### `Translator(catalog, language, scope, fallback_language="en")`

Translator class for internationalization support.

**Parameters:**
- `catalog`: Translation catalog mapping languages to scopes to keys to translations
- `language`: Target language for translation
- `scope`: Scope for translation keys
- `fallback_language`: Fallback language when translation is not found (default: "en")

**Methods:**
- `__call__(key, default=None, **kwargs)`: Translate a key with optional template variables

**Example:**
```python
from kiarina.i18n import Translator

catalog = {
    "en": {"app.greeting": {"hello": "Hello, $name!"}},
    "ja": {"app.greeting": {"hello": "こんにちは、$name!"}}
}

t = Translator(catalog=catalog, language="ja", scope="app.greeting")
print(t("hello", name="World"))  # Output: こんにちは、World!
```

### Translation Behavior

1. **Primary lookup**: Searches for the key in the target language
2. **Fallback lookup**: If not found, searches in the fallback language
3. **Default value**: If still not found, uses the provided default value
4. **Error handling**: If no default is provided, returns `"{scope}#{key}"` and logs an error

## Configuration

### Using pydantic-settings-manager

```yaml
# config.yaml
kiarina.i18n:
  default_language: "en"
  catalog:
    en:
      app.greeting:
        hello: "Hello, $name!"
    ja:
      app.greeting:
        hello: "こんにちは、$name!"
```

```python
from pydantic_settings_manager import load_user_configs
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

load_user_configs(config)
```

### Settings Fields

- `default_language` (str): Default language to use when translation is not found (default: "en")
- `catalog_file` (str | None): Path to YAML file containing translation catalog
- `catalog` (dict): Translation catalog mapping languages to scopes to keys to translations

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=kiarina.i18n --cov-report=html
```

## Dependencies

- `pydantic>=2.0.0`
- `pydantic-settings>=2.0.0`
- `pydantic-settings-manager>=2.3.0`
- `pyyaml>=6.0.0`

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - Parent monorepo containing all kiarina packages
