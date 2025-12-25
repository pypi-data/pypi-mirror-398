"""Field transformer for element_define decorator.

This module provides the ElementFieldTransformer class that orchestrates
field transformations including converters, validators, and change tracking.
"""

from __future__ import annotations

import typing

import attrs
from attrs import validators
from loguru import logger as log

from attrs_xml.core.base_element import BaseElement, _set_child_parent
from attrs_xml.core.converter_factory import ConverterFactory
from attrs_xml.core.inspect import is_ptr_field
from attrs_xml.core.type_utils import TypeInfo, _get_field_type
from attrs_xml.core.validator_factory import ValidatorFactory
from attrs_xml.globals import are_defaults_disabled


class ElementFieldTransformer:
    """Handles all field transformations for element_define decorator.

    This class orchestrates the transformation of attrs fields, adding:
    - Default value wrapping (respects disable_defaults context)
    - Type converters
    - Type validators
    - Setattr hooks
    """

    def __call__(
        self,
        cls: type,
        fields: tuple[attrs.Attribute, ...],
    ) -> tuple[attrs.Attribute, ...]:
        """Transform all fields for the class."""
        return tuple(self._transform_field(cls, field) for field in fields)

    def _is_structural_factory(self, factory: callable) -> bool:
        """Check if a factory produces structural container types.
        
        Structural types (lists, dicts, BaseElement subclasses) should keep
        their defaults even when disable_defaults is active, to maintain
        object structure during deserialization.
        
        Args:
            factory: The factory function to check
            
        Returns:
            True if factory produces a structural type, False otherwise
        """
        # Check for built-in container types
        if factory in (list, dict, set, tuple):
            return True
        
        # Check if factory is a class that's a BaseElement subclass
        if isinstance(factory, type):
            try:
                from attrs_xml.core.base_element import BaseElement
                if issubclass(factory, BaseElement):
                    return True
            except (TypeError, ImportError):
                pass
        
        # Check if factory name suggests it's a container
        factory_name = getattr(factory, "__name__", "")
        if factory_name in ("list", "dict", "set", "tuple", "defaultdict"):
            return True
        
        return False

    def _wrap_default_with_check(self, field: attrs.Attribute) -> attrs.Attribute:
        """Wrap non-callable defaults in a factory that checks the disable flag.
        
        Only wraps simple configuration defaults (strings, numbers, enums, etc.).
        Structural containers (lists, dicts, BaseElement subclasses) keep their
        factory defaults to maintain object structure during deserialization.
        
        Fields with validators are also preserved - they typically represent
        required configuration with sensible defaults (like Literal types).
        
        This allows loading from files to distinguish between explicitly set
        configuration values and defaults, while preserving structural integrity.
        
        Internal fields (marked with cattrs_omit: True) are not affected.
        """
        # Skip if field has no default or already uses NOTHING
        if field.default is attrs.NOTHING:
            return field
        
        # Skip if default is explicitly None (not a real default)
        if field.default is None:
            return field
        
        # Skip internal fields that are omitted from serialization
        # These fields (like _parent, _cache) should keep their normal defaults
        if field.metadata.get("cattrs_omit", False):
            return field
        
        original_default = field.default
        
        # Handle Factory defaults
        if isinstance(original_default, attrs.Factory):
            # Check if factory produces a structural container type
            if self._is_structural_factory(original_default.factory):
                # Keep structural factories unchanged
                return field
            
            # Wrap configuration factories
            original_factory = original_default.factory
            takes_self = original_default.takes_self
            
            def wrapped_factory(self_or_none=None):
                if are_defaults_disabled():
                    return None
                if takes_self:
                    return original_factory(self_or_none)
                return original_factory()
            
            return field.evolve(
                default=attrs.Factory(wrapped_factory, takes_self=takes_self)
            )
        
        # Handle static defaults (non-callable)
        if not callable(original_default):
            # Only wrap simple scalar values (str, int, bool, etc.)
            # Skip mutable containers (list, dict, etc.) - though these should use Factory
            if isinstance(original_default, (list, dict, set, tuple)):
                # Don't wrap mutable defaults - they should use Factory anyway
                return field
            
            # Wrap simple scalar configuration values
            def wrapped_factory():
                if are_defaults_disabled():
                    return None
                return original_default
            
            return field.evolve(
                default=attrs.Factory(wrapped_factory, takes_self=False)
            )
        
        # If it's already a bare callable (unlikely), check if it's structural
        if self._is_structural_factory(original_default):
            return field
        
        # Wrap non-structural callables
        def wrapped_factory():
            if are_defaults_disabled():
                return None
            return original_default()
        
        return field.evolve(
            default=attrs.Factory(wrapped_factory, takes_self=False)
        )

    def _transform_field(self, cls: type, field: attrs.Attribute) -> attrs.Attribute:
        """Apply all transformations to a single field."""
        field = self._wrap_default_with_check(field)
        field = self._add_converter(cls, field)
        field = self._add_setattr(field)
        field = self._add_type_validator(cls, field)
        return field

    def _add_converter(self, cls: type, field: attrs.Attribute) -> attrs.Attribute:
        """Add converter to ptr fields.

        If the field already has a converter, it will be chained using attrs.converters.pipe
        so that:
        1. The existing converter runs first
        2. The auto-generated converter runs second

        This allows fields to define custom converters (e.g., for case normalization)
        that run before the type resolution converter.
        """
        if not is_ptr_field(field):
            return field

        field_type = _get_field_type(cls, field)
        if not field_type or field_type is typing.Any:
            return field

        type_info = TypeInfo(field_type)
        converter_factory = ConverterFactory(type_info)
        auto_converter = converter_factory.create()

        metadata = field.metadata.copy()

        converters = [auto_converter]

        # If there's already a converter, chain them using pipe
        if field.converter is not None:
            existing_converter = field.converter
            # Use attrs.converters.pipe to chain: existing_converter -> auto_converter
            converters.insert(0, existing_converter)

        # Check for post_converter in metadata
        if post_converter := metadata.get("post_converter", None):
            converters.append(post_converter)

        chained_converter = attrs.converters.pipe(*converters)

        return field.evolve(converter=chained_converter)

    def _add_setattr(self, field: attrs.Attribute) -> attrs.Attribute:
        """Add change tracking to fields."""
        original_setattr = field.on_setattr

        def _setattr(instance, attribute, value):
            if value is attrs.NOTHING:
                # Handle Factory defaults
                if isinstance(attribute.default, attrs.Factory):
                    factory = attribute.default.factory
                    if attribute.default.takes_self:
                        value = factory(instance)
                    else:
                        value = factory()

                else:
                    value = attribute.default

                log.debug(
                    f"Attribute default is {attribute.default} for {attribute.name}"
                )
                log.debug(
                    f"Setting field '{attribute.name}' to NOTHING on {type(instance).__name__} triggers default value: got {value}",
                )

                return value

            # Apply converter first
            if attribute.converter:
                value = attribute.converter(value)

            # Chain existing on_setattr
            if original_setattr:
                value = original_setattr(instance, attribute, value)

            # Run validator
            if attribute.validator:
                attribute.validator(instance, attribute, value)

            # Set parent relationship (but not for parent field to avoid recursion)
            if isinstance(value, BaseElement) and attribute.name != "_parent":
                _set_child_parent(value, instance)

            return value

        return field.evolve(on_setattr=_setattr)

    def _add_type_validator(self, cls: type, field: attrs.Attribute) -> attrs.Attribute:
        """Add type validator to field."""
        field_type = _get_field_type(cls, field)

        if field_type is None or field_type is typing.Any:
            return field

        type_validator = ValidatorFactory.create(field_type)

        if not type_validator:
            return field

        new_validator = (
            type_validator
            if field.validator is None
            else validators.and_(field.validator, type_validator)
        )

        return field.evolve(validator=new_validator)
