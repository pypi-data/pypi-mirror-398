type ConfigStr = str
"""
Configuration string for parse_config_string()

Format: key:value,key2:value2

Features:
- Nested keys: cache.enabled:true → {"cache": {"enabled": True}}
- Array indices: items.0:foo,items.1:bar → {"items": ["foo", "bar"]}
- Flags: debug,verbose → {"debug": None, "verbose": None}
- Type conversion: true/false → bool, numbers → int/float

Examples:
    >>> "debug:true,port:8080"
    >>> "cache.enabled:true,db.port:5432"
    >>> "items.0:foo,items.1:bar"
    >>> "debug,verbose,cache.enabled:true"

See Also:
    parse_config_string: Parser function for this format
"""
