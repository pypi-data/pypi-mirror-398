from typing import Type, Any

from .cattrs_converter import get_converter


def to_domain[T](data: Any, cls: Type[T]) -> T:
    """Convert a dict or JSON-like structure into a domain entity."""
    return get_converter().structure(data, cls)
