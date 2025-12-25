from typing import Any

def filter_json(data: Any, fields: list[str]) -> Any:
    """Filter JSON data based on field paths.

    Args:
        data: The data to filter (can be dict or object)
        fields: List of dot-notation paths to include

    Returns:
        Filtered data containing only the specified fields
    """
def convert_keys_to_snake_case(data: Any) -> Any:
    """Recursively convert all dictionary keys from camelCase to snake_case.

    Args:
        data: The data to convert (can be dict, list, or other types)

    Returns:
        Data with all dictionary keys converted to snake_case
    """
def get_value(obj: Any, key: str) -> Any:
    """Get value from an object or dict using either attribute or key access."""
def has_value(obj: Any, key: str) -> bool:
    """Check if an object or dict has a value using either attribute or key access."""
def merge_dicts(d1: dict, d2: dict) -> dict:
    """Deep merge two dictionaries."""
def get_value_by_path(data: Any, path: list[str]) -> Any:
    """Get a value from nested data using a path list."""
def set_value_by_path(target: dict, path: list[str], value: Any) -> None:
    """Set a value in a nested dictionary using a path list."""
def to_dict(obj: Any) -> Any:
    """Convert any object to a dictionary recursively.

    Handles:
    - Pydantic models (using .model_dump())
    - Lists and tuples
    - Datetime objects
    - Basic Python types

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation of the object
    """
def camel_to_snake_case(text: str) -> str:
    '''Convert a camelCase string to snake_case.

    Args:
        text: The camelCase string to convert

    Returns:
        The converted snake_case string

    Examples:
        >>> camel_to_snake_case("helloWorld")
        \'hello_world\'
        >>> camel_to_snake_case("APIResponse")
        \'api_response\'
        >>> camel_to_snake_case("IOStream")
        \'io_stream\'
    '''
