from importlib import import_module
from typing import Any

from .._types.import_path import ImportPath


def import_object(import_path: ImportPath) -> Any:
    """
    Import and return an object from an import path.

    This function dynamically imports a module and returns the specified object.
    Useful for plugin systems and dynamic loading scenarios.

    Args:
        import_path: Import path in the format 'module_name:object_name'
                    Example: 'kiarina.utils.common:parse_config_string'

    Returns:
        The imported object (class, function, or any other object)

    Raises:
        ValueError: If import_path format is invalid
        ImportError: If the module cannot be imported
        AttributeError: If the object doesn't exist in the module

    Examples:
        >>> # Import a function
        >>> parse_fn = import_object('kiarina.utils.common:parse_config_string')
        >>> result = parse_fn('key:value')

        >>> # Import a class
        >>> MyClass = import_object('myapp.plugins:MyPlugin')
        >>> instance = MyClass()

        >>> # Use with type hints for better IDE support
        >>> from typing import Callable
        >>> parser: Callable = import_object('kiarina.utils.common:parse_config_string')
    """
    if ":" not in import_path:
        raise ValueError(
            "import_path must be in the format 'module_name:object_name'. "
            f"Got: '{import_path}'"
        )

    module_name, object_name = import_path.split(":", 1)

    if not module_name:
        raise ValueError("module_name must not be empty")

    if not object_name:
        raise ValueError("object_name must not be empty")

    try:
        module = import_module(module_name)

    except ImportError as e:
        raise ImportError(
            f"Could not import module '{module_name}'. "
            f"Make sure the module is installed and accessible."
        ) from e

    if not hasattr(module, object_name):
        raise AttributeError(
            f"Module '{module_name}' does not have a '{object_name}' attribute. "
            f"Available attributes: {', '.join(dir(module))}"
        )

    return getattr(module, object_name)
