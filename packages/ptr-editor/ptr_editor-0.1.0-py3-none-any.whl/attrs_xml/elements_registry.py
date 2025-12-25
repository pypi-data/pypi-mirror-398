"""Registry for managing XML-serializable element classes.

This module provides ElementsRegistry, which manages registration and lookup
of element classes for XML serialization/deserialization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Generic, TypeVar, get_type_hints

from attr import fields_dict
from attrs import define, field
from loguru import logger as log

from attrs_xml.core.type_utils import (
    create_union_type,
    extract_base_element_types,
    is_union_type,
)
from attrs_xml.xml.converter import (
    CustomConverter,
    make_default_xml_converter,
    register_default_xml_hooks,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from attrs_xml.core.base_element import BaseElement


T = TypeVar("T", bound="BaseElement")


def _class_tagger(class_name: str) -> str:
    """Convert class name to XML tag (default: camelCase)."""
    return class_name[0].lower() + class_name[1:]


@define
class ElementsRegistry(Generic[T]):
    """Registry for XML-serializable element classes.

    This registry manages:
    - Class registration and lookup
    - XML tag name mapping
    - Schema traversal and auto-registration
    - XML serialization/deserialization

    Attributes:
        classes: List of all registered element classes
        classes_keys: Mapping of class types to their XML tag names
        converter: cattrs converter for XML serialization
        class_tagger: Function to generate XML tag from class name
    """

    classes: list[type[T]] = field(factory=list)
    classes_keys: dict[type[T], set[str]] = field(
        factory=lambda: defaultdict(set),
    )
    converter: CustomConverter = field(factory=make_default_xml_converter)
    class_tagger: Callable[[str], str] = field(default=_class_tagger)

    def __attrs_post_init__(self):
        """Initialize XML converter with default hooks."""
        register_default_xml_hooks(self.converter)

    # ========================================================================
    # XML Serialization/Deserialization
    # ========================================================================

    def to_xml(
        self,
        item: T,
        *,
        pretty: bool = False,
        root_key: str = "",
    ) -> str:
        """Convert an element instance to XML string.

        Args:
            item: Element instance to serialize
            pretty: Whether to format XML with indentation
            root_key: Custom root element name (optional)

        Returns:
            XML string representation
        """
        from attrs_xml.xml.io import object_to_xml

        log.debug(f"Converting {item} to XML with root key '{root_key}'")
        return object_to_xml(item, self.converter, pretty=pretty, root_key=root_key)

    def from_xml(
        self,
        xml: str,
        cls: type | str | None = None,
        *,
        disable_defaults: bool = True,
    ) -> T:
        """Convert XML string to element instance.

        Args:
            xml: XML string to parse
            cls: Expected class type or name (optional)
            disable_defaults: Whether to disable default values when loading.
                When True (default), fields not present in XML will be None
                instead of their default values. This helps distinguish between
                values explicitly set in the file vs. defaults.

        Returns:
            Parsed element instance
        """
        from attrs_xml.xml.io import loads

        log.opt(lazy=True).trace(f"Converting XML to element: {xml[:100]}...")
        return loads(
            xml,
            elements_registry=self,
            cls=cls,
            disable_defaults=disable_defaults,
        )

    # ========================================================================
    # Class Registration
    # ========================================================================

    def register(self, cls: type[T]) -> None:
        """Register a class and its default name.

        Args:
            cls: Element class to register
        """
        if cls not in self.classes:
            self.classes.append(cls)

        # Register default name if available
        if hasattr(cls, "default_name") and cls.default_name is not None:
            self._register_name(cls, cls.default_name)

        # Register field usage names
        self._register_field_names(cls)

    def register_schema(self, cls: type[T]) -> None:
        """Register a class and all nested BaseElement types in its schema.

        This performs a recursive traversal of all field types, registering
        any BaseElement subclasses found. Useful for ensuring all types in
        a complex schema are available for serialization.

        Args:
            cls: Root element class to start schema traversal
        """
        from attrs_xml.core.base_element import BaseElement

        visited: set[type] = set()

        def _register_type_recursive(t: type) -> None:
            """Recursively register a type and its nested types."""
            # Skip if already processed or not a BaseElement
            if t in visited:
                return
            if not isinstance(t, type) or not issubclass(t, BaseElement):
                return

            visited.add(t)
            log.debug(f"Registering schema type: {t.__name__}")

            # Register this type
            if t not in self.classes:
                self.register(t)  # type: ignore[arg-type]

            # Process all fields
            for field_type in self._get_field_types(t):
                # Extract BaseElement types from the field
                base_types = extract_base_element_types(field_type)
                for base_type in base_types:
                    _register_type_recursive(base_type)

        _register_type_recursive(cls)

    def _register_name(self, cls: type[T], name: str) -> None:
        """Register an XML tag name for a class.

        Args:
            cls: Element class
            name: XML tag name to register
        """
        self.classes_keys[cls].add(name)

    def _register_field_names(self, cls: type[T]) -> None:
        """Register XML tag names used in class fields.

        Analyzes all fields of a class and registers the XML tag names
        that child elements will use when serialized.

        Args:
            cls: Element class to analyze
        """

        # Get resolved type hints
        type_hints = self._get_type_hints(cls)

        # Process each field
        try:
            children = fields_dict(cls)
        except NotImplementedError:
            log.warning(f"Cannot get fields for {cls.__name__}")
            return

        for field_name, field_info in children.items():
            # Determine XML tag name
            xml_tag = field_info.metadata.get("xml_tag")
            tag_name = xml_tag.strip() if xml_tag else field_name.strip()

            # Get resolved type
            field_type = type_hints.get(field_name, field_info.type)

            log.debug(
                f"Processing field '{field_name}' of {cls.__name__} "
                f"(tag: {tag_name}, type: {field_type})",
            )

            # Extract BaseElement types
            base_types = extract_base_element_types(field_type)

            if not base_types:
                continue

            # For union types, register the union itself
            if is_union_type(field_type) and len(base_types) > 1:
                union_type = create_union_type(base_types)
                self._register_name(union_type, tag_name)  # type: ignore[arg-type]
                log.debug(f"Registered union type for '{tag_name}': {union_type}")
            else:
                # Register each individual type
                for base_type in base_types:
                    self._register_name(base_type, tag_name)  # type: ignore[arg-type]
                    log.debug(f"Registered '{tag_name}' for {base_type.__name__}")

    def _get_type_hints(self, cls: type) -> dict[str, type]:
        """Get resolved type hints for a class.

        Args:
            cls: Class to get type hints for

        Returns:
            Dictionary of field names to resolved types
        """
        try:
            return get_type_hints(cls)
        except Exception as e:
            log.warning(
                f"Could not resolve type hints for {cls.__name__}: {e}. "
                f"Using field types directly.",
            )
            return {}

    def _get_field_types(self, cls: type) -> list[type]:
        """Get all field types for a class.

        Args:
            cls: Class to get field types from

        Returns:
            List of field types
        """
        try:
            type_hints = self._get_type_hints(cls)
            children = fields_dict(cls)
            return [
                type_hints.get(name, field.type) for name, field in children.items()
            ]
        except Exception as e:
            log.warning(f"Could not get field types for {cls.__name__}: {e}")
            return []

    # ========================================================================
    # Lookup Methods
    # ========================================================================

    def get_all(self) -> list[type[T]]:
        """Get all registered classes.

        Returns:
            List of all registered element classes
        """
        return self.classes

    def class_by_name(self, name: str) -> type[T] | None:
        """Get a class by its Python class name.

        Args:
            name: Python class name to search for

        Returns:
            Matching class or None if not found
        """
        for cls in self.classes:
            if cls.__name__ == name:
                return cls
        return None

    def items_by_name(self, tag_name: str) -> list[type[T]]:
        """Get all classes registered with a specific XML tag name.

        Args:
            tag_name: XML tag name to search for

        Returns:
            List of classes that use this tag name (sorted by name for determinism)
        """
        tag_name = tag_name.strip()
        matching_classes = [cls for cls in self.classes_keys if tag_name in self.classes_keys[cls]]
        # Sort by qualified name for deterministic behavior
        return sorted(matching_classes, key=lambda c: (c.__module__, c.__qualname__))

    def items_by_defname(self, defname: str) -> list[type[T]]:
        """Get leaf classes with a specific default name.

        Returns classes that have the given default name and no subclasses
        (leaf classes in the inheritance hierarchy).

        Args:
            defname: Default name to search for

        Returns:
            List of matching leaf classes (sorted by name for determinism)
        """
        matching = [
            cls
            for cls in self.get_all()
            if cls.default_name == defname and not cls.__subclasses__()
        ]
        # Sort by qualified name for deterministic behavior
        return sorted(matching, key=lambda c: (c.__module__, c.__qualname__))

    def leaves(self) -> list[type[T]]:
        """Get all leaf classes (classes with no subclasses).

        Returns:
            List of all leaf element classes
        """
        return [cls for cls in self.get_all() if not cls.__subclasses__()]

    def union_by_defname(self, defname: str) -> type | None:
        """Create a Union type of all classes with a specific name.

        Args:
            defname: Default name to search for

        Returns:
            Union type of matching classes, or None if no matches
        """
        items = self.items_by_name(defname)
        if not items:
            return None
        if len(items) == 1:
            return items[0]
        return create_union_type(tuple(items))

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def clear(self) -> None:
        """Clear all registered classes and mappings."""
        self.classes.clear()
        self.classes_keys.clear()
