import pytest

from kiarina.utils.common import parse_config_string


def test_parse_config_string_empty():
    """Test empty configuration string"""
    result = parse_config_string("")
    assert result == {}


@pytest.mark.parametrize(
    "config_str,expected",
    [
        # Basic key-value pairs
        ("key1:value1,key2:value2", {"key1": "value1", "key2": "value2"}),
        ("single:option", {"single": "option"}),
        # Flag functionality (no key_value_separator)
        ("debug", {"debug": None}),
        ("debug,verbose", {"debug": None, "verbose": None}),
        ("debug,enabled:true", {"debug": None, "enabled": True}),
        (
            "debug,verbose,cache.enabled:true",
            {"debug": None, "verbose": None, "cache": {"enabled": True}},
        ),
        # Type conversion
        ("bool_true:true", {"bool_true": True}),
        ("bool_false:false", {"bool_false": False}),
        ("bool_True:True", {"bool_True": True}),
        ("bool_False:False", {"bool_False": False}),
        ("int_pos:123", {"int_pos": 123}),
        ("int_neg:-456", {"int_neg": -456}),
        ("int_zero:0", {"int_zero": 0}),
        ("float_pos:3.14", {"float_pos": 3.14}),
        ("float_neg:-2.5", {"float_neg": -2.5}),
        ("str_val:hello", {"str_val": "hello"}),
        # Mixed types
        (
            "bool:true,int:42,float:3.14,str:hello",
            {"bool": True, "int": 42, "float": 3.14, "str": "hello"},
        ),
    ],
)
def test_parse_config_string_basic(config_str, expected):
    """Test basic configuration string parsing and type conversion"""
    result = parse_config_string(config_str)
    assert result == expected


@pytest.mark.parametrize(
    "config_str,expected",
    [
        # Simple nesting
        ("cache.enabled:true", {"cache": {"enabled": True}}),
        ("db.port:5432", {"db": {"port": 5432}}),
        # Nested flags
        ("app.debug", {"app": {"debug": None}}),
        ("app.debug,app.verbose", {"app": {"debug": None, "verbose": None}}),
        ("app.debug,app.port:8080", {"app": {"debug": None, "port": 8080}}),
        # Multiple nested keys
        (
            "cache.enabled:true,cache.ttl:3600",
            {"cache": {"enabled": True, "ttl": 3600}},
        ),
        # Different sections
        (
            "cache.enabled:true,db.host:localhost,db.port:5432",
            {"cache": {"enabled": True}, "db": {"host": "localhost", "port": 5432}},
        ),
        # Deep nesting
        ("a.b.c.d:value1", {"a": {"b": {"c": {"d": "value1"}}}}),
        # Mixed depth nesting with flags
        (
            "a.b.c.d:value1,a.b.e:value2,a.f:value3,a.b.flag",
            {
                "a": {
                    "b": {"c": {"d": "value1"}, "e": "value2", "flag": None},
                    "f": "value3",
                }
            },
        ),
    ],
)
def test_parse_config_string_nested(config_str, expected):
    """Test nested key parsing with dot notation"""
    result = parse_config_string(config_str)
    assert result == expected


@pytest.mark.parametrize(
    "config_str,expected",
    [
        # Whitespace around options
        ("  key1:value1  ,  key2:value2  ", {"key1": "value1", "key2": "value2"}),
        # Whitespace around key-value pairs
        ("key1  :  value1", {"key1": "value1"}),
        # Whitespace with nested keys
        ("  key1.nested  :  42  ", {"key1": {"nested": 42}}),
        # Mixed whitespace
        (
            "  cache.enabled : true , db.port : 5432  ",
            {"cache": {"enabled": True}, "db": {"port": 5432}},
        ),
    ],
)
def test_parse_config_string_whitespace(config_str, expected):
    """Test whitespace handling in keys and values"""
    result = parse_config_string(config_str)
    assert result == expected


@pytest.mark.parametrize(
    "config_str,separator,key_value_separator,nested_separator,expected",
    [
        # Custom item separator
        (
            "key1=value1;key2=value2",
            ";",
            "=",
            ".",
            {"key1": "value1", "key2": "value2"},
        ),
        # Custom key-value separator with nesting
        (
            "key1=value1;key2.sub=42",
            ";",
            "=",
            ".",
            {"key1": "value1", "key2": {"sub": 42}},
        ),
        # Custom nested separator
        (
            "key1/sub:value1,key2/nested/deep:42",
            ",",
            ":",
            "/",
            {"key1": {"sub": "value1"}, "key2": {"nested": {"deep": 42}}},
        ),
        # All custom separators
        (
            "app|debug=true;app|port=8080",
            ";",
            "=",
            "|",
            {"app": {"debug": True, "port": 8080}},
        ),
    ],
)
def test_parse_config_string_custom_separators(
    config_str, separator, key_value_separator, nested_separator, expected
):
    """Test custom separators"""
    result = parse_config_string(
        config_str,
        separator=separator,
        key_value_separator=key_value_separator,
        nested_separator=nested_separator,
    )
    assert result == expected


@pytest.mark.parametrize(
    "config_str,expected",
    [
        # Options without key-value separator are now treated as flags
        ("debug,valid:value", {"debug": None, "valid": "value"}),
        ("flag1,key1:value1,flag2", {"flag1": None, "key1": "value1", "flag2": None}),
        # Empty options (should be ignored)
        ("key1:value1,,key2:value2", {"key1": "value1", "key2": "value2"}),
        # Mixed flags and values with empty options
        ("debug,,verbose,port:8080,", {"debug": None, "verbose": None, "port": 8080}),
        # Whitespace handling with flags
        (
            "  debug  ,  verbose  ,  port : 8080  ",
            {"debug": None, "verbose": None, "port": 8080},
        ),
    ],
)
def test_parse_config_string_edge_cases(config_str, expected):
    """Test edge cases and error handling"""
    result = parse_config_string(config_str)
    assert result == expected


@pytest.mark.parametrize(
    "config_str,expected",
    [
        # Simple array
        ("items.0:foo,items.1:bar,items.2:baz", {"items": ["foo", "bar", "baz"]}),
        ("tags.0:python,tags.1:rust", {"tags": ["python", "rust"]}),
        # Array with type conversion
        ("numbers.0:1,numbers.1:2,numbers.2:3", {"numbers": [1, 2, 3]}),
        ("mixed.0:1,mixed.1:true,mixed.2:hello", {"mixed": [1, True, "hello"]}),
        # Sparse array (with None gaps)
        ("sparse.0:first,sparse.2:third", {"sparse": ["first", None, "third"]}),
        # Nested structure with arrays
        (
            "users.0.name:Alice,users.0.age:30,users.1.name:Bob,users.1.age:25",
            {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]},
        ),
        # Mixed arrays and regular keys
        (
            "app.name:myapp,app.tags.0:web,app.tags.1:api,app.debug:true",
            {"app": {"name": "myapp", "tags": ["web", "api"], "debug": True}},
        ),
        # Array in nested structure
        (
            "db.servers.0:localhost,db.servers.1:192.168.1.1,db.port:5432",
            {"db": {"servers": ["localhost", "192.168.1.1"], "port": 5432}},
        ),
        # Deep nesting with arrays
        (
            "config.db.hosts.0:primary,config.db.hosts.1:secondary",
            {"config": {"db": {"hosts": ["primary", "secondary"]}}},
        ),
    ],
)
def test_parse_config_string_arrays(config_str, expected):
    """Test array support with index notation"""
    result = parse_config_string(config_str)
    assert result == expected


@pytest.mark.parametrize(
    "config_str,expected",
    [
        # Array flags (no values)
        ("items.0,items.1:value", {"items": [None, "value"]}),
        ("flags.0,flags.1,flags.2", {"flags": [None, None, None]}),
        # Mixed flags and arrays
        (
            "debug,items.0:first,verbose,items.1:second",
            {"debug": None, "items": ["first", "second"], "verbose": None},
        ),
    ],
)
def test_parse_config_string_array_flags(config_str, expected):
    """Test array support with flag notation"""
    result = parse_config_string(config_str)
    assert result == expected


def test_parse_config_string_array_edge_cases():
    """Test edge cases for array functionality"""
    # Single element array
    result = parse_config_string("items.0:single")
    assert result == {"items": ["single"]}

    # Large index (creates sparse array)
    result = parse_config_string("items.10:value")
    expected_items = [None] * 10 + ["value"]
    assert result == {"items": expected_items}

    # Zero index
    result = parse_config_string("items.0:zero")
    assert result == {"items": ["zero"]}


def test_parse_config_string_array_type_conflicts():
    """Test handling of type conflicts with arrays"""
    # When dict key comes first, then array index - dict gets converted to array
    result = parse_config_string("items.key:value,items.0:first")
    # The dict gets converted to array, losing the original key
    assert result == {"items": ["first"]}

    # When array index comes first, then dict key - array gets converted to dict
    result = parse_config_string("items.0:first,items.key:value")
    # The array gets converted to dict, preserving both values
    assert result == {"items": {"key": "value"}}


def test_parse_config_string_real_world_example():
    """Test real-world application configuration example"""
    config_str = "app.debug:true,app.port:8080,app.name:myapp,db.host:localhost,db.port:5432,db.timeout:30.5,cache.enabled:true,cache.ttl:3600"

    expected = {
        "app": {"debug": True, "port": 8080, "name": "myapp"},
        "db": {"host": "localhost", "port": 5432, "timeout": 30.5},
        "cache": {"enabled": True, "ttl": 3600},
    }

    result = parse_config_string(config_str)
    assert result == expected


def test_parse_config_string_real_world_with_arrays():
    """Test real-world configuration with arrays"""
    config_str = "app.name:myapp,app.tags.0:web,app.tags.1:api,db.servers.0:primary,db.servers.1:secondary,db.ports.0:5432,db.ports.1:5433"

    expected = {
        "app": {"name": "myapp", "tags": ["web", "api"]},
        "db": {"servers": ["primary", "secondary"], "ports": [5432, 5433]},
    }

    result = parse_config_string(config_str)
    assert result == expected
