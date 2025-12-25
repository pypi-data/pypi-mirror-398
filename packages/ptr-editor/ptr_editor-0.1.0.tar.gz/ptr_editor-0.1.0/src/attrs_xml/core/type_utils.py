"""Type inspection and resolution utilities.

This module provides utilities for analyzing type annotations, checking for
optional types, UNSET sentinels, and extracting resolved types from unions.
"""

from __future__ import annotations

from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints

import attrs

from attrs_xml.core.base_element import BaseElement
from attrs_xml.core.sentinels import _UnsetType


class TypeInfo:
    """Encapsulates resolved type information for a field.

    This class analyzes a type annotation and extracts:
    - Whether it's optional (includes None)
    - Whether it includes UNSET sentinel
    - The actual types (excluding None and UNSET)
    """

    def __init__(self, field_type: type):
        self.original_type = field_type
        self.is_optional = _is_optional(field_type)
        self.has_unset = _has_unset_type(field_type)
        self.resolved_types = self._extract_types(field_type)

    def _extract_types(self, field_type: type) -> tuple[type, ...]:
        """Extract the actual types, excluding None and UNSET."""
        origin = get_origin(field_type)

        if origin in (Union, UnionType):
            args = get_args(field_type)
            return tuple(
                arg for arg in args if arg is not type(None) and arg is not _UnsetType
            )

        return (field_type,)

    @property
    def single_type(self) -> type | None:
        """Get the single resolved type, or None if multiple types."""
        return self.resolved_types[0] if len(self.resolved_types) == 1 else None

    @property
    def is_union(self) -> bool:
        """Check if this represents a union of multiple types."""
        return len(self.resolved_types) > 1


def _is_optional(field_type: type) -> bool:
    """Check if type is Optional (Union with None)."""
    origin = get_origin(field_type)
    if origin is Union:
        return type(None) in get_args(field_type)
    return False


def _has_unset_type(field_type: type) -> bool:
    """Check if type includes UNSET sentinel."""
    origin = get_origin(field_type)
    if origin is Union:
        return _UnsetType in get_args(field_type)
    return False


def _get_field_type(cls: type, field: attrs.Attribute) -> type | None:
    """Get the type annotation for a field, handling __future__ annotations."""
    try:
        type_hints = get_type_hints(cls)
        return type_hints.get(field.name)
    except Exception:
        return field.type


def _is_base_element_type(t: type) -> bool:
    """Check if type is BaseElement or a subclass."""
    try:
        return t is BaseElement or (isinstance(t, type) and issubclass(t, BaseElement))
    except TypeError:
        return False


def extract_base_element_types(field_type: type) -> tuple[type, ...]:
    """Extract BaseElement types from a field type annotation.
    
    Handles:
    - Single types
    - List[Type]
    - Union types
    - Optional types
    
    Returns:
        Tuple of BaseElement types found in the annotation.
    """
    origin = get_origin(field_type)

    # Handle list types
    if origin is list:
        args = get_args(field_type)
        if args:
            field_type = args[0]
            origin = get_origin(field_type)

    # Handle Union/Optional types
    if origin in (Union, UnionType):
        args = get_args(field_type)
        # Filter out None and keep only BaseElement types
        base_types = tuple(
            arg for arg in args
            if arg is not type(None) and _is_base_element_type(arg)
        )
        return base_types

    # Handle single type
    if _is_base_element_type(field_type):
        return (field_type,)

    return ()


def is_list_type(field_type: type) -> bool:
    """Check if a type is a list type annotation."""
    return get_origin(field_type) is list


def is_union_type(field_type: type) -> bool:
    """Check if a type is a Union type annotation."""
    return get_origin(field_type) in (Union, UnionType)


def create_union_type(types: tuple[type, ...]) -> type:
    """Create a Union type from multiple types.
    
    Args:
        types: Tuple of types to combine
        
    Returns:
        A Union type or single type if only one type provided
    """
    if not types:
        raise ValueError("Cannot create union from empty types")

    if len(types) == 1:
        return types[0]

    # Create Union using the | operator
    result = types[0]
    for t in types[1:]:
        result = result | t
    return result
