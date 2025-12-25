"""Sentinel values for attrs_xml.

This module provides sentinel values that can be used to represent special states
in attribute values, such as "required but not yet set".
"""

from __future__ import annotations


class _UnsetType:
    """Sentinel type for required but unset fields.
    
    This provides a distinct value from None, attrs.NOTHING, or any valid value,
    allowing for fields that are required but can be initialized without a value
    and validated later.
    """

    def __repr__(self) -> str:
        return " UNSET "

    def __bool__(self) -> bool:
        return False


UNSET = _UnsetType()
"""Sentinel value indicating a field is required but has not been set yet.

Use this as a default value for fields that are required but you want to allow
initialization without providing them. Later validation can check if the field
has been set using `is_set()`.

Example:
    >>> @define
    ... class MyClass:
    ...     required_field: str | _UnsetType = field(default=UNSET)
    ...
    >>> obj = MyClass()
    >>> is_set(obj.required_field)
    False
    >>> obj.required_field = "value"
    >>> is_set(obj.required_field)
    True
"""


def is_set(value) -> bool:
    """Check if a value has been set (is not UNSET).
    
    Args:
        value: The value to check
        
    Returns:
        True if the value has been set, False if it's UNSET
        
    Example:
        >>> is_set(UNSET)
        False
        >>> is_set(None)
        True
        >>> is_set("value")
        True
    """
    return value is not UNSET


def require_set():
    """Create a validator that ensures fields are set (not UNSET).
    
    Returns:
        An attrs validator function that raises ValueError if the value is UNSET
        
    Example:
        >>> @define
        ... class MyClass:
        ...     required_field: str | _UnsetType = field(
        ...         default=UNSET,
        ...         validator=require_set()
        ...     )
        ...
        >>> obj = MyClass()  # Raises ValueError
    """

    def validator(_instance, attribute, value):
        if value is UNSET:
            msg = f"Field '{attribute.name}' is required but was not set"
            raise ValueError(msg)

    return validator


__all__ = ["UNSET", "_UnsetType", "is_set", "require_set"]
