"""Protocols for attrs_xml library.

This module defines protocols that can be implemented by user code
to integrate with attrs_xml's conversion and validation system.
"""

from typing import Protocol

from typing_extensions import runtime_checkable

from attrs_xml.core.base_element import BaseElement


@runtime_checkable
class ElementGenerator(Protocol):
    """Protocol for classes that can generate BaseElement instances.

    Any object implementing this protocol must provide the
    `_element_generate_` method that returns a BaseElement or list of BaseElements.

    The generator will be usable in place of a BaseElement in any context
    that accepts BaseElement instances. The generation of real BaseElement
    instances will be deferred until needed, allowing for lazy behavior.

    Example:
        >>> from attrs_xml.core.protocols import ElementGenerator
        >>> from attrs_xml.core import BaseElement, element_define
        >>>
        >>> @element_define
        >>> class MyElement(BaseElement):
        ...     pass
        >>>
        >>> class MyGenerator:
        ...     def _element_generate_(self) -> MyElement:
        ...         return MyElement()
        >>>
        >>> gen = MyGenerator()
        >>> isinstance(gen, ElementGenerator)
        True
    """

    def _element_generate_(self) -> BaseElement | list[BaseElement]: ...


# Alias for backward compatibility
PtrElementGenerator = ElementGenerator

__all__ = ["ElementGenerator", "PtrElementGenerator"]
