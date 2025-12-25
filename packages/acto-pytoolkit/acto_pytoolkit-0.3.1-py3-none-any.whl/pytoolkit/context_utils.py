"""Utilities for working with nested dictionaries and context objects."""
from typing import Any, Dict, Iterable, Mapping, Optional


def merge_dicts(*dicts: Mapping[str, Any]) -> Dict[str, Any]:
    """Shallow merge multiple dictionaries into a new dictionary.

    Later dictionaries override earlier ones.
    """
    result: Dict[str, Any] = {}
    for d in dicts:
        result.update(d)
    return result


def deep_merge(*dicts: Mapping[str, Any]) -> Dict[str, Any]:
    """Deeply merge multiple dictionaries.

    Nested dictionaries are merged recursively, other values are overwritten by
    later dictionaries.
    """
    result: Dict[str, Any] = {}
    for d in dicts:
        for key, value in d.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)  # type: ignore[arg-type]
            else:
                result[key] = value
    return result


def select_keys(source: Mapping[str, Any], keys: Iterable[str]) -> Dict[str, Any]:
    """Return a new dictionary containing only the given keys."""
    return {k: source[k] for k in keys if k in source}


def get_nested(data: Dict[str, Any], path: str, default: Any = None, separator: str = ".") -> Any:
    """Get a value from a nested dictionary using dot notation.

    Parameters
    ----------
    data : Dict[str, Any]
        The dictionary to query
    path : str
        Dot-separated path to the value (e.g., "user.address.city")
    default : Any, optional
        Default value if the path doesn't exist
    separator : str, optional
        Separator to use in the path (default: ".")

    Returns
    -------
    Any
        The value at the specified path, or default if not found

    Examples
    --------
    >>> data = {"user": {"name": "Alice", "address": {"city": "NYC"}}}
    >>> get_nested(data, "user.address.city")
    'NYC'
    >>> get_nested(data, "user.age", default=0)
    0
    """
    keys = path.split(separator)
    current = data

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


def set_nested(data: Dict[str, Any], path: str, value: Any, separator: str = ".") -> None:
    """Set a value in a nested dictionary using dot notation.

    Creates intermediate dictionaries as needed.

    Parameters
    ----------
    data : Dict[str, Any]
        The dictionary to modify
    path : str
        Dot-separated path to set (e.g., "user.address.city")
    value : Any
        Value to set at the path
    separator : str, optional
        Separator to use in the path (default: ".")

    Examples
    --------
    >>> data = {}
    >>> set_nested(data, "user.address.city", "NYC")
    >>> data
    {'user': {'address': {'city': 'NYC'}}}
    """
    keys = path.split(separator)
    current = data

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def flatten_dict(data: Dict[str, Any], parent_key: str = "", separator: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary into a single-level dictionary.

    Parameters
    ----------
    data : Dict[str, Any]
        The nested dictionary to flatten
    parent_key : str, optional
        Prefix for keys (used internally for recursion)
    separator : str, optional
        Separator to use between nested keys (default: ".")

    Returns
    -------
    Dict[str, Any]
        Flattened dictionary with dot-separated keys

    Examples
    --------
    >>> data = {"user": {"name": "Alice", "address": {"city": "NYC"}}}
    >>> flatten_dict(data)
    {'user.name': 'Alice', 'user.address.city': 'NYC'}
    """
    items: Dict[str, Any] = {}

    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key

        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, separator))
        else:
            items[new_key] = value

    return items


def unflatten_dict(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Unflatten a dictionary with dot-separated keys into a nested dictionary.

    Parameters
    ----------
    data : Dict[str, Any]
        The flattened dictionary
    separator : str, optional
        Separator used in keys (default: ".")

    Returns
    -------
    Dict[str, Any]
        Nested dictionary

    Examples
    --------
    >>> data = {'user.name': 'Alice', 'user.address.city': 'NYC'}
    >>> unflatten_dict(data)
    {'user': {'name': 'Alice', 'address': {'city': 'NYC'}}}
    """
    result: Dict[str, Any] = {}

    for key, value in data.items():
        set_nested(result, key, value, separator)

    return result
