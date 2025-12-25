"""Validator factory for field type validation.

This module provides the ValidatorFactory class that creates validators
for field types, including support for ElementGenerator instances.
"""

from __future__ import annotations

from types import UnionType
from typing import (
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import attrs
from attrs import validators
from loguru import logger as log

from attrs_xml.core.sentinels import UNSET, _UnsetType


class ValidatorFactory:
    """Creates validators for field types.

    This factory analyzes type annotations and creates appropriate
    attrs validators, including support for ElementGenerator instances.
    """

    @staticmethod
    def create(annotation: type) -> Any:
        """Create a validator from a type annotation."""
        origin = get_origin(annotation)

        # Handle Literal types
        if origin is Literal:
            return validators.in_(get_args(annotation))

        # Handle Union types
        if origin in (Union, UnionType):
            return ValidatorFactory._create_union_validator(annotation)

        # Handle simple types
        if isinstance(annotation, type):
            return ValidatorFactory._create_generator_aware_validator(annotation)

        return None

    @staticmethod
    def _create_generator_aware_validator(expected_type: type) -> Any:
        """Create a validator that handles both regular instances and generators.

        Args:
            expected_type: The expected type for the field

        Returns:
            A validator that accepts either the expected type or a generator
            that will produce the expected type
        """
        from attrs_xml.core.protocols import ElementGenerator

        def generator_aware_validator(instance, attribute, value):
            # Check if it's a regular instance of the expected type
            if isinstance(value, expected_type):
                return

            # Check if it's a generator
            if isinstance(value, ElementGenerator):
                ValidatorFactory._validate_generator_type(
                    value,
                    expected_type,
                    instance,
                    attribute,
                )
                return

            # Neither expected type nor generator - raise error
            msg = (
                f"'{attribute.name}' must be {expected_type!r} or an "
                f"ElementGenerator that produces {expected_type!r} (got "
                f"{value!r} that is a {type(value)!r})."
            )
            raise TypeError(msg)

        return generator_aware_validator

    @staticmethod
    def _validate_generator_type(
        generator: Any,
        expected_type: type,
        instance: Any,
        attribute: attrs.Attribute,
    ) -> None:
        """Validate generator's _element_generate_ method return type.

        Args:
            generator: The generator instance to validate
            expected_type: The expected return type
            instance: The attrs instance being validated
            attribute: The attribute being validated
        """
        # Get the type hints for the generator's _element_generate_ method
        if not hasattr(generator, "_element_generate_"):
            msg = (
                f"Generator for '{attribute.name}' on {instance.__class__.__name__} "
                f"does not have '_element_generate_' method."
            )
            raise TypeError(msg)

        try:
            # Get type hints for the generator's method
            generate_method = getattr(type(generator), "_element_generate_", None)
            if generate_method is None:
                generate_method = generator._element_generate_

            type_hints = get_type_hints(generate_method)
            return_type = type_hints.get("return")

            if return_type is None or return_type is Any:
                log.warning(
                    f"Generator for field '{attribute.name}' on "
                    f"{instance.__class__.__name__} "
                    f"has '_element_generate_' method without a type annotation "
                    f"or typed as Any. Expected return type: {expected_type!r}. "
                    f"This may cause type validation issues.",
                )
                return

            # Check if the return type matches or is a subclass of expected type
            # Handle Union types in return annotation
            origin = get_origin(return_type)
            expected_origin = get_origin(expected_type)
            
            if origin in (Union, UnionType):
                return_types = get_args(return_type)
                # Check if any of the union types match the expected type
                if not any(
                    isinstance(rt, type) and issubclass(rt, expected_type)
                    for rt in return_types
                    if rt is not type(None)
                ):
                    log.warning(
                        f"Generator for field '{attribute.name}' on "
                        f"{instance.__class__.__name__} "
                        f"has '_element_generate_' returning {return_type!r}, "
                        f"which may not match expected type {expected_type!r}.",
                    )
            elif isinstance(return_type, type):
                # If expected_type is a Union, check if return_type matches any of its types
                if expected_origin in (Union, UnionType):
                    expected_types = get_args(expected_type)
                    if not any(
                        isinstance(et, type) and issubclass(return_type, et)
                        for et in expected_types
                        if et is not type(None)
                    ):
                        log.warning(
                            f"Generator for field '{attribute.name}' on "
                            f"{instance.__class__.__name__} "
                            f"has '_element_generate_' returning {return_type!r}, "
                            f"which does not match expected type {expected_type!r}.",
                        )
                elif not issubclass(return_type, expected_type):
                    log.warning(
                        f"Generator for field '{attribute.name}' on "
                        f"{instance.__class__.__name__} "
                        f"has '_element_generate_' returning {return_type!r}, "
                        f"which does not match expected type {expected_type!r}.",
                    )
            else:
                log.warning(
                    f"Generator for field '{attribute.name}' on "
                    f"{instance.__class__.__name__} "
                    f"has '_element_generate_' with complex return type "
                    f"{return_type!r}. "
                    f"Cannot validate against expected type {expected_type!r}.",
                )

        except (AttributeError, TypeError) as e:
            log.warning(
                f"Could not validate generator type for field '{attribute.name}' "
                f"on {instance.__class__.__name__}: {e}",
            )

    @staticmethod
    def _create_union_validator(annotation: type) -> Any:
        """Create validator for Union types."""
        from attrs_xml.core.protocols import ElementGenerator

        args = get_args(annotation)
        is_optional = type(None) in args
        has_unset = _UnsetType in args

        # Extract actual types (excluding None and UNSET)
        # Include both regular types and generic aliases (e.g., list[str])
        type_args = []
        simple_classes = []
        literal_values = []
        
        for a in args:
            if a is type(None) or a is _UnsetType:
                continue
            
            # Check if it's a Literal type
            if get_origin(a) is Literal:
                # Extract the literal values
                literal_values.extend(get_args(a))
                continue
            
            # Check if it's a simple type
            if isinstance(a, type):
                simple_classes.append(a)
                type_args.append(a)
            else:
                # It's a generic alias (e.g., list[str], dict[str, int])
                origin = get_origin(a)
                if origin is not None:
                    simple_classes.append(origin)
                    type_args.append(a)
        
        if not type_args and not literal_values:
            return None
        
        # Tuple of simple classes for isinstance checks
        classes = tuple(simple_classes) if simple_classes else None

        # Create generator-aware validator for union types
        def union_generator_aware_validator(instance, attribute, value):
            # Check literal values first if any
            if literal_values and value in literal_values:
                return
            
            # Check if it's a regular instance of any of the expected types
            if classes and isinstance(value, classes):
                return

            # Check if it's a generator
            if isinstance(value, ElementGenerator):
                # Validate against the full union type, not just the first type
                ValidatorFactory._validate_generator_type(
                    value,
                    annotation,  # Pass the full union, not just classes[0]
                    instance,
                    attribute,
                )
                return

            # Neither expected types nor generator - raise error
            expected_desc = []
            if classes:
                expected_desc.append(f"one of {classes!r}")
            if literal_values:
                expected_desc.append(f"one of {literal_values!r}")
            
            expected_str = " or ".join(expected_desc)
            
            msg = (
                f"'{attribute.name}' must be {expected_str} or an "
                f"ElementGenerator that produces one of those types "
                f"(got {value!r} that is a {type(value)!r})."
            )

            if value is None:
                msg += (
                    f" You might be trying to assign None to the non-optional field ({attribute.name}), "
                    f"or the xml file you are trying to load is missing this element rendering the file invalid."
                )

            raise TypeError(msg)

        # Wrap with optional if needed
        if is_optional:

            def optional_union_validator(instance, attribute, value):
                if value is None:
                    return
                union_generator_aware_validator(instance, attribute, value)

            base_validator = optional_union_validator
        else:
            base_validator = union_generator_aware_validator

        # Handle UNSET
        if has_unset:
            return ValidatorFactory._create_unset_aware_validator(base_validator)

        return base_validator

    @staticmethod
    def _create_unset_aware_validator(base_validator):
        """Create a validator that accepts UNSET or validates normally."""

        def unset_aware_validator(instance, attribute, value):
            if value is UNSET:
                log.warning(
                    f"Field '{attribute.name}' on {instance.__class__.__name__} "
                    f"is set to UNSET. This may cause issues during serialization.",
                )
                return
            base_validator(instance, attribute, value)

        return unset_aware_validator
