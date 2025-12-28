from typing import Any

from .._types.config_str import ConfigStr


def parse_config_string(
    config_str: ConfigStr,
    *,
    separator: str = ",",
    key_value_separator: str = ":",
    nested_separator: str = ".",
) -> dict[str, Any]:
    """
    Parse configuration string into nested dictionary

    When key contains nested_separator, it will be treated as nested keys:
    - hoge.fuga:30 → {"hoge": {"fuga": 30}}

    When key_value_separator is not found, the key is treated as a flag with None value:
    - debug,enabled:true → {"debug": None, "enabled": True}

    Values are automatically converted to appropriate types:
    - "true", "True" → bool(True)
    - "false", "False" → bool(False)
    - Numeric strings ("1", "0", "-5", etc.) → int/float
    - Others → str

    Args:
        config_str: Configuration string to parse
        separator: Item separator (default: ",")
        key_value_separator: Key-value separator (default: ":")
        nested_separator: Nested key separator (default: ".")

    Returns:
        Parsed configuration dictionary

    Examples:
        >>> parse_config_string("cache.enabled:true,db.port:5432")
        {"cache": {"enabled": True}, "db": {"port": 5432}}

        >>> parse_config_string("debug,verbose,cache.enabled:true")
        {"debug": None, "verbose": None, "cache": {"enabled": True}}

        >>> parse_config_string("key1=val1;key2.sub=42", separator=";", key_value_separator="=")
        {"key1": "val1", "key2": {"sub": 42}}
    """
    if not config_str:
        return {}

    result: dict[str, Any] = {}

    for option in config_str.split(separator):
        option = option.strip()

        if not option:
            continue

        if key_value_separator in option:
            key, value = option.split(key_value_separator, 1)
            key = key.strip()
            value = value.strip()

            converted_value = _convert_value(value)

            # Handle nested keys
            _set_nested_value(result, key, converted_value, nested_separator)
        else:
            # No key_value_separator found, treat as flag with None value
            _set_nested_value(result, option, None, nested_separator)

    return result


def _convert_value(value: str) -> Any:
    """
    Convert string value to appropriate type

    Args:
        value: String value to convert

    Returns:
        Converted value
    """
    try:
        # Boolean values (only true and false, 1 and 0 are treated as numbers)
        if value.lower() == "true":
            return True

        elif value.lower() == "false":
            return False

        # Integer case
        elif value.lstrip("-").isdigit():
            return int(value)

        # Floating point case
        else:
            try:
                float_value = float(value)

                # Don't convert to integer if it can be represented as integer (respect original value)
                if "." in value:
                    return float_value
                else:
                    # If integer format but not caught above, treat as string
                    return value

            except ValueError:
                # String case
                return value

    except (ValueError, TypeError):
        # If conversion fails, save as string
        return value


def _set_nested_value(
    target: dict[str, Any], key: str, value: Any, separator: str = "."
) -> None:
    """
    Set value with nested keys (supports array indices)

    When a key is a numeric string, it's treated as an array index:
    - items.0:foo → {"items": ["foo"]}
    - users.0.name:Alice → {"users": [{"name": "Alice"}]}

    Args:
        target: Target dictionary to set the value
        key: Key (supports dot notation and array indices)
        value: Value to set
        separator: Nested key separator (default: ".")
    """
    keys = key.split(separator)

    current: dict[str, Any] | list[Any] = target

    # Navigate/create nested structure up to the last key
    for i, k in enumerate(keys[:-1]):
        next_key = keys[i + 1]

        if _is_array_index(k):
            index = int(k)

            if not isinstance(current, list):
                raise ValueError(
                    f"Cannot access array index {index} on non-array value"
                )

            while len(current) <= index:
                current.append(None)

            if _is_array_index(next_key):
                if current[index] is None:
                    current[index] = []
                elif not isinstance(current[index], list):
                    current[index] = []

            else:
                if current[index] is None:
                    current[index] = {}
                elif not isinstance(current[index], dict):
                    current[index] = {}

            current = current[index]

        else:
            if not isinstance(current, dict):
                raise ValueError(f"Cannot access key '{k}' on non-dict value")

            if _is_array_index(next_key):
                if k not in current:
                    current[k] = []
                elif not isinstance(current[k], list):
                    current[k] = []

                current = current[k]

            else:
                if k not in current:
                    current[k] = {}
                elif not isinstance(current[k], dict):
                    current[k] = {}

                current = current[k]

    # Set the value for the last key
    last_key = keys[-1]

    if _is_array_index(last_key):
        index = int(last_key)

        if not isinstance(current, list):
            raise ValueError(f"Cannot set array index {index} on non-array value")

        # Extend list if necessary (fill with None)
        while len(current) <= index:
            current.append(None)

        current[index] = value

    else:
        if not isinstance(current, dict):
            raise ValueError(f"Cannot set key '{last_key}' on non-dict value")

        current[last_key] = value


def _is_array_index(key: str) -> bool:
    """
    Check if a key represents an array index

    Args:
        key: Key to check

    Returns:
        True if key is a non-negative integer string
    """
    return key.isdigit()
