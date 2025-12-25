"""Utilities for traversing and manipulating attrs element trees."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import Any

import attrs
from loguru import logger as log


def walk_attrs_tree(
    obj: Any,
    *,
    visit_func: Callable[[Any, str, Any], None] | None = None,
    skip_none: bool = True,
) -> Iterator[tuple[Any, str, Any]]:
    """
    Walk through an attrs element tree, yielding (parent, field_name, value) tuples.

    This generator traverses a tree of attrs-decorated objects recursively,
    visiting all fields and their children. It handles circular references
    and can optionally skip None values.

    Args:
        obj: The root object to traverse
        visit_func: Optional callback function called for each field.
                   Receives (parent, field_name, field_value) as arguments.
        skip_none: Whether to skip None values (default: True)

    Yields:
        Tuples of (parent_object, field_name, field_value) for each field

    Example:
        # Iterate through all fields
        for parent, field_name, value in walk_attrs_tree(my_timeline):
            print(f"{type(parent).__name__}.{field_name} = {value}")

        # Use with a visitor function
        def print_field(parent, name, value):
            print(f"Found: {type(parent).__name__}.{name}")

        list(walk_attrs_tree(my_timeline, visit_func=print_field))
    """
    visited: set[int] = set()
    yield from _walk_recursive(obj, visited, visit_func, skip_none)


def _walk_recursive(
    obj: Any,
    visited: set[int],
    visit_func: Callable[[Any, str, Any], None] | None,
    skip_none: bool,
) -> Iterator[tuple[Any, str, Any]]:
    """Recursively walk through an attrs tree."""
    # Handle None
    if obj is None:
        return

    # Check for circular references
    obj_id = id(obj)
    if obj_id in visited:
        log.debug(f"Skipping already visited object of type {type(obj).__name__}")
        return
    visited.add(obj_id)

    # Check if object has attrs fields
    if not attrs.has(type(obj)):
        return

    log.debug(f"Walking through object of type {type(obj).__name__}")

    # Process each attrs field
    for attr in attrs.fields(type(obj)):
        field_name = attr.name
        field_value = getattr(obj, field_name, None)

        if skip_none and field_value is None:
            continue

        # Yield this field
        yield (obj, field_name, field_value)

        # Call visitor function if provided
        if visit_func is not None:
            visit_func(obj, field_name, field_value)

        # Recursively process field value
        yield from _walk_field_value(field_value, visited, visit_func, skip_none)


def _walk_field_value(
    field_value: Any,
    visited: set[int],
    visit_func: Callable[[Any, str, Any], None] | None,
    skip_none: bool,
) -> Iterator[tuple[Any, str, Any]]:
    """Walk through a field value, handling sequences and nested objects."""
    # Handle lists/sequences
    if isinstance(field_value, Sequence) and not isinstance(field_value, str):
        for item in field_value:
            if skip_none and item is None:
                continue
            yield from _walk_recursive(item, visited, visit_func, skip_none)

    # Handle single nested objects
    elif attrs.has(type(field_value)):
        yield from _walk_recursive(field_value, visited, visit_func, skip_none)


def apply_to_attrs_tree(
    obj: Any,
    func: Callable[[Any, str, Any], Any | None],
    *,
    modify_in_place: bool = True,
) -> Any:
    """
    Apply a function to all fields in an attrs tree and optionally update them.

    This function traverses an attrs element tree and applies a transformation
    function to each field. If the function returns a non-None value and
    modify_in_place is True, the field is updated with the new value.

    Args:
        obj: The root object to process
        func: Function that takes (parent, field_name, field_value) and
              returns a new value or None to keep the existing value
        modify_in_place: Whether to update fields with returned values

    Returns:
        The processed object (same as input if modify_in_place=True)

    Example:
        # Replace all None values with empty strings
        def replace_none(parent, name, value):
            if value is None:
                return ""
            return None  # Keep existing value

        apply_to_attrs_tree(my_obj, replace_none)

        # Log all string fields
        def log_strings(parent, name, value):
            if isinstance(value, str):
                print(f"{name}: {value}")
            return None  # Don't modify

        apply_to_attrs_tree(my_obj, log_strings, modify_in_place=False)
    """
    visited: set[int] = set()
    _apply_recursive(obj, func, visited, modify_in_place)
    return obj


def _apply_recursive(
    obj: Any,
    func: Callable[[Any, str, Any], Any | None],
    visited: set[int],
    modify_in_place: bool,
) -> None:
    """Recursively apply function to attrs tree."""
    # Handle None
    if obj is None:
        return

    # Check for circular references
    obj_id = id(obj)
    if obj_id in visited:
        return
    visited.add(obj_id)

    # Check if object has attrs fields
    if not attrs.has(type(obj)):
        return

    # Process each attrs field
    for attr in attrs.fields(type(obj)):
        field_name = attr.name
        field_value = getattr(obj, field_name, None)

        # Apply function to this field
        new_value = func(obj, field_name, field_value)

        # Update field if function returned a value
        if modify_in_place and new_value is not None:
            setattr(obj, field_name, new_value)
            field_value = new_value  # Use new value for recursion

        # Recursively process field value
        _apply_to_field_value(field_value, func, visited, modify_in_place)


def _apply_to_field_value(
    field_value: Any,
    func: Callable[[Any, str, Any], Any | None],
    visited: set[int],
    modify_in_place: bool,
) -> None:
    """Apply function to a field value, handling sequences and nested objects."""
    # Handle lists/sequences
    if isinstance(field_value, Sequence) and not isinstance(field_value, str):
        for item in field_value:
            if item is not None:
                _apply_recursive(item, func, visited, modify_in_place)

    # Handle single nested objects
    elif attrs.has(type(field_value)):
        _apply_recursive(field_value, func, visited, modify_in_place)
