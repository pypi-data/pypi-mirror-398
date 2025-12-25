"""Core attrs extension components.

This module provides the foundational components for extending attrs
with additional functionality like element definition, field types,
protocols, and sentinels.
"""

from .base_element import BaseElement
from .decorators import element_define
from .decorators_utils import classproperty, remove_empty_items
from .fields import attr, element, text, time_element
from .protocols import ElementGenerator, PtrElementGenerator
from .sentinels import UNSET, _UnsetType, is_set, require_set

__all__ = [
    "UNSET",
    "BaseElement",
    "ElementGenerator",
    "PtrElementGenerator",
    "_UnsetType",
    "attr",
    "classproperty",
    "element",
    "element_define",
    "is_set",
    "remove_empty_items",
    "require_set",
    "text",
    "time_element",
]
