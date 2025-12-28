import pytest

from kiarina.utils.common import import_object


class SampleClass:
    def hello(self) -> str:
        return "Hello, World!"


def sample_function() -> str:
    return "Hello from function!"


SAMPLE_CONSTANT = "constant_value"


def test_import_object_invalid_format_no_colon() -> None:
    with pytest.raises(
        ValueError,
        match="import_path must be in the format 'module_name:object_name'",
    ):
        import_object("invalid_import_path")


def test_import_object_empty_module_name() -> None:
    with pytest.raises(ValueError, match="module_name must not be empty"):
        import_object(":object_name")


def test_import_object_empty_object_name() -> None:
    with pytest.raises(ValueError, match="object_name must not be empty"):
        import_object("module_name:")


def test_import_object_module_not_found() -> None:
    with pytest.raises(
        ImportError,
        match="Could not import module 'non_existent_module'",
    ):
        import_object("non_existent_module:SomeClass")


def test_import_object_attribute_not_found() -> None:
    with pytest.raises(
        AttributeError,
        match=f"Module '{__name__}' does not have a 'NonExistentClass' attribute",
    ):
        import_object(f"{__name__}:NonExistentClass")


def test_import_object_import_class() -> None:
    ImportedClass = import_object(f"{__name__}:SampleClass")
    assert ImportedClass is SampleClass
    instance = ImportedClass()
    assert instance.hello() == "Hello, World!"


def test_import_object_import_function() -> None:
    imported_fn = import_object(f"{__name__}:sample_function")
    assert imported_fn is sample_function
    assert imported_fn() == "Hello from function!"


def test_import_object_import_constant() -> None:
    imported_const = import_object(f"{__name__}:SAMPLE_CONSTANT")
    assert imported_const == "constant_value"


def test_import_object_from_kiarina_package() -> None:
    parse_fn = import_object("kiarina.utils.common:parse_config_string")
    result = parse_fn("key:value")
    assert result == {"key": "value"}


def test_import_object_with_nested_module() -> None:
    parse_fn = import_object(
        "kiarina.utils.common._helpers.parse_config_string:parse_config_string"
    )
    result = parse_fn("debug:true")
    assert result == {"debug": True}
