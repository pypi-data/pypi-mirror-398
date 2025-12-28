# kiarina-utils-common

[![PyPI version](https://badge.fury.io/py/kiarina-utils-common.svg)](https://badge.fury.io/py/kiarina-utils-common)
[![Python](https://img.shields.io/pypi/pyversions/kiarina-utils-common.svg)](https://pypi.org/project/kiarina-utils-common/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Common utility functions for the kiarina namespace packages.

## Installation

```bash
pip install kiarina-utils-common
```

## Features

### Dynamic Object Import

Import objects (classes, functions, constants) dynamically from import paths. Useful for plugin systems and dynamic loading scenarios.

```python
from kiarina.utils.common import import_object

# Import a function
parse_fn = import_object("kiarina.utils.common:parse_config_string")
result = parse_fn("key:value")

# Import a class
MyClass = import_object("myapp.plugins:MyPlugin")
instance = MyClass()

# Import with type hints for better IDE support
from typing import Callable
parser: Callable = import_object("kiarina.utils.common:parse_config_string")
```

### Configuration String Parser

Parse configuration strings into nested dictionaries with automatic type conversion.

```python
from kiarina.utils.common import parse_config_string

# Basic usage
config = parse_config_string("cache.enabled:true,db.port:5432")
# Result: {"cache": {"enabled": True}, "db": {"port": 5432}}

# Flag support (no value)
config = parse_config_string("debug,verbose,cache.enabled:true")
# Result: {"debug": None, "verbose": None, "cache": {"enabled": True}}

# Array indices support
config = parse_config_string("items.0:first,items.1:second")
# Result: {"items": ["first", "second"]}

# Custom separators
config = parse_config_string(
    "key1=val1;key2.sub=42", 
    separator=";", 
    key_value_separator="="
)
# Result: {"key1": "val1", "key2": {"sub": 42}}
```

#### Type Conversion

Values are automatically converted to appropriate types:

- `"true"`, `"True"` → `bool(True)`
- `"false"`, `"False"` → `bool(False)`
- Numeric strings (`"1"`, `"0"`, `"-5"`, `"3.14"`) → `int` or `float`
- Other strings → `str`

#### Nested Keys

Use dot notation for nested structures:

```python
config = parse_config_string("database.host:localhost,database.port:5432")
# Result: {"database": {"host": "localhost", "port": 5432}}
```

#### Array Indices

Use numeric keys for array structures:

```python
config = parse_config_string("users.0.name:Alice,users.0.age:30,users.1.name:Bob")
# Result: {"users": [{"name": "Alice", "age": 30}, {"name": "Bob"}]}
```

## API Reference

### `import_object(import_path)`

Import and return an object from an import path.

**Parameters:**
- `import_path` (str): Import path in the format `'module_name:object_name'`
  - Example: `'kiarina.utils.common:parse_config_string'`

**Returns:**
- The imported object (class, function, or any other object)

**Raises:**
- `ValueError`: If import_path format is invalid
- `ImportError`: If the module cannot be imported
- `AttributeError`: If the object doesn't exist in the module

**Examples:**

```python
# Import a function
parse_fn = import_object('kiarina.utils.common:parse_config_string')
result = parse_fn('key:value')

# Import a class
MyClass = import_object('myapp.plugins:MyPlugin')
instance = MyClass()

# Use with type hints
from typing import Callable
parser: Callable = import_object('kiarina.utils.common:parse_config_string')
```

### `parse_config_string(config_str, *, separator=",", key_value_separator=":", nested_separator=".")`

Parse configuration string into nested dictionary.

**Parameters:**
- `config_str` (str): Configuration string to parse
- `separator` (str, optional): Item separator. Default: `","`
- `key_value_separator` (str, optional): Key-value separator. Default: `":"`
- `nested_separator` (str, optional): Nested key separator. Default: `"."`

**Returns:**
- `dict[str, Any]`: Parsed configuration dictionary

**Examples:**

```python
# Basic usage
parse_config_string("key1:value1,key2:value2")
# {"key1": "value1", "key2": "value2"}

# Nested keys
parse_config_string("cache.enabled:true,db.port:5432")
# {"cache": {"enabled": True}, "db": {"port": 5432}}

# Flags (no value)
parse_config_string("debug,verbose")
# {"debug": None, "verbose": None}

# Custom separators
parse_config_string("a=1;b=2", separator=";", key_value_separator="=")
# {"a": 1, "b": 2}
```

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Contributing

This is a personal project by kiarina. While issues and pull requests are welcome, please note that this is primarily developed for personal use.

## Related Packages

- [kiarina-utils-file](../kiarina-utils-file/): File operation utilities
- [kiarina-llm](../kiarina-llm/): LLM-related utilities
