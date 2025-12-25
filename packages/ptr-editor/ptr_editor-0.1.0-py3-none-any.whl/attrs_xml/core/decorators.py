"""Main decorator for creating XML-serializable attrs classes.

This module provides the `element_define` decorator that extends attrs.define
to create classes with automatic type conversion, validation, and change tracking.
"""

from __future__ import annotations

import typing
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, overload

import attrs
from attrs import define as _define

from attrs_xml.core.field_transformer import ElementFieldTransformer

from .fields import attr, element, text, time_element

if TYPE_CHECKING:
    from collections.abc import Callable


# ============================================================================
# Main Decorator
# ============================================================================


def _class_tagger(class_name: str):
    """Default class name tagger - converts to camelCase."""
    return class_name[0].lower() + class_name[1:]


T = TypeVar("T", bound=type)


@typing.dataclass_transform(
    field_specifiers=(
        attrs.field,
        element,
        text,
        attr,
        time_element,
    ),
)
@overload
def element_define(
    cls: type[T],
) -> type[T]:
    ...


@overload
def element_define(
    *,
    defname: str | None = None,
    class_tagger: Callable[[str], str] = _class_tagger,
    **kwargs,
) -> Callable[[type[T]], type[T]]:
    ...


def element_define(
    cls: type[T] | None = None,
    *,
    defname: str | None = None,
    class_tagger: Callable[[str], str] = _class_tagger,
    **kwargs,
) -> type[T] | Callable[[type[T]], type[T]]:
    """A decorator that wraps attrs.define to create XML-serializable classes.

    This decorator adds:
    - Automatic type conversion using from_any/from_string methods
    - Template reference resolution
    - Change tracking
    - Type validation
    - Parent-child relationship management

    Args:
        cls: The class to decorate (provided automatically)
        defname: Optional custom name for the element (defaults to class name)
        class_tagger: Function to convert class name to element name
        **kwargs: Additional arguments passed to attrs.define

    Returns:
        The decorated class

    Example:
        >>> from attrs_xml import (
        ...     element_define,
        ...     element,
        ... )
        >>> @element_define
        ... class MyElement:
        ...     name: str = (
        ...         element()
        ...     )
        ...     value: int = (
        ...         element()
        ...     )
    """

    def decorator(cls: type[T]) -> type[T]:
        # Determine element name
        default_name = _determine_default_name(
            cls,
            defname,
            class_tagger,
        )

        # Set up field transformer
        field_transformer = ElementFieldTransformer()

        # Apply attrs.define with our field transformer
        cls = _define(cls, hash=True, field_transformer=field_transformer, **kwargs)

        # Set default name
        cls.default_name = default_name

        return cls

    return decorator if cls is None else decorator(cls)


def _determine_default_name(
    cls: type,
    defname: str | None,
    class_tagger: Callable[[str], str],
) -> str:
    """Determine the default name for an element class."""
    if defname is not None:
        return defname

    if hasattr(cls, "default_name") and cls.default_name is not None:
        return cls.default_name

    return class_tagger(cls.__name__)
