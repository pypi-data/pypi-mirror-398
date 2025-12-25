"""Custom disambiguator for cattrs.
Based on the original one but modified to support renamed literals as discriminators.
This is needed as we rename literals to camel case to match XML attributes.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import MISSING
from functools import reduce
from operator import or_
from typing import TYPE_CHECKING, Any, Literal, get_args, get_origin

from attrs import NOTHING, AttrsInstance
from cattrs._compat import (
    adapted_fields,
    fields_dict,
    is_literal,
)
from cattrs.disambiguators import _overriden_name, _usable_attribute_names
from loguru import logger as log

if TYPE_CHECKING:
    from collections.abc import Callable

    from cattrs.converters import BaseConverter
    from cattrs.gen._consts import AttributeOverride


from cattrs._compat import (
    Mapping,
)


def custom_create_default_dis_func(
    converter: BaseConverter,
    *classes: type[AttrsInstance],
    use_literals: bool = True,
    overrides: (
        dict[str, AttributeOverride] | Literal["from_converter"]
    ) = "from_converter",
) -> Callable[[Mapping[Any, Any]], type[Any] | None]:
    """Given attrs classes or dataclasses, generate a disambiguation function.

    The function is based on unique fields without defaults or unique values.

    :param use_literals: Whether to try using fields annotated as literals for
        disambiguation.
    :param overrides: Attribute overrides to apply.

    .. versionchanged:: 24.1.0
        Dataclasses are now supported.
    """

    log.opt(lazy=True).trace(f"Creating default disambiguation function for classes: {classes}")
    log.opt(lazy=True).trace(f"converter: {converter}")
    log.opt(lazy=True).trace(f"use_literals: {use_literals}")
    log.opt(lazy=True).trace(f"overrides: {overrides}")
    if len(classes) < 2:
        msg = "At least two classes required."
        raise ValueError(msg)

    if overrides == "from_converter":
        overrides = [
            getattr(converter.get_structure_hook(c), "overrides", {}) for c in classes
        ]
    else:
        overrides = [overrides for _ in classes]

    # first, attempt for unique values
    literal_discriminated_classes = set()
    literal_discriminators = {}  # discriminator_name -> {value -> class}

    if use_literals:
        # Group classes by common literal fields they share
        # first get all possible discriminator names considering renames
        cls_candidates = []
        for cl, override in zip(classes, overrides, strict=False):
            field_names = set()
            for at in adapted_fields(get_origin(cl) or cl):
                if is_literal(at.type):
                    renamed = _overriden_name(at, override.get(at.name))
                    field_names.add(renamed)
            cls_candidates.append((cl, field_names))

        log.opt(lazy=True).trace(
            f"Literal field name candidates: {[(cl.__name__, fields) for cl, fields in cls_candidates]}",
        )

        # Find all unique discriminator field names
        all_discriminator_names = set()
        for _, field_names in cls_candidates:
            all_discriminator_names.update(field_names)

        log.opt(lazy=True).trace(f"All possible discriminator names: {all_discriminator_names}")

        # For each potential discriminator, find which classes have it
        # and build a mapping of literal values to classes
        # Sort discriminator names for deterministic behavior
        for discriminator in sorted(all_discriminator_names):
            classes_with_discriminator = [
                (cl, override)
                for (cl, field_names), override in zip(
                    cls_candidates, overrides, strict=False,
                )
                if discriminator in field_names
            ]

            if len(classes_with_discriminator) < 1:
                # Skip if no classes have this discriminator
                continue

            log.opt(lazy=True).trace(
                f"Discriminator '{discriminator}' found in {len(classes_with_discriminator)} classes",
            )

            # Build mapping of literal values to classes for this discriminator
            mapping = defaultdict(list)

            for cl, override in classes_with_discriminator:
                # Find original field name
                fields = fields_dict(get_origin(cl) or cl)
                original_name = None
                for field_name, field in fields.items():
                    if (
                        _overriden_name(field, override.get(field_name))
                        == discriminator
                    ):
                        original_name = field_name
                        break

                if original_name:
                    for key in get_args(fields[original_name].type):
                        mapping[key].append(cl)

            # Check if this discriminator can uniquely identify classes
            # (each literal value maps to exactly one class)
            if mapping and all(len(v) == 1 for v in mapping.values()):
                log.opt(lazy=True).trace(
                    f"Discriminator '{discriminator}' can discriminate {len(mapping)} classes",
                )
                # This is a good discriminator for this group
                literal_discriminators[discriminator] = {
                    k: v[0] for k, v in mapping.items()
                }
                literal_discriminated_classes.update(
                    mapping[k][0] for k in mapping.keys()
                )
            else:
                log.opt(lazy=True).trace(
                    f"Discriminator '{discriminator}' has ambiguous mappings, skipping",
                )

        log.opt(lazy=True).trace(
            f"Successfully discriminated {len(literal_discriminated_classes)} classes using literals",
        )
        log.opt(lazy=True).trace(f"Literal discriminators: {literal_discriminators}")

    # Classes that couldn't be discriminated by literals
    remaining_classes = [
        cl for cl in classes if cl not in literal_discriminated_classes
    ]
    log.opt(lazy=True).trace(
        f"Remaining classes to discriminate by unique keys: {[cl.__name__ for cl in remaining_classes]}",
    )

    # next, attempt for unique keys for remaining classes

    # NOTE: This could just as well work with just field availability and not
    #  uniqueness, returning Unions ... it doesn't do that right now.
    if remaining_classes:
        # Get the overrides corresponding to remaining classes
        remaining_with_overrides = [
            (cl, override)
            for cl, override in zip(classes, overrides, strict=False)
            if cl in remaining_classes
        ]
        cls_and_attrs = [
            (cl, *_usable_attribute_names(cl, override))
            for cl, override in remaining_with_overrides
        ]
    else:
        cls_and_attrs = []

    # For each class, attempt to generate a single unique required field.
    uniq_attrs_dict: dict[str, type] = {}

    # We start from classes with the largest number of unique fields
    # so we can do easy picks first, making later picks easier.
    cls_and_attrs.sort(key=lambda c_a: len(c_a[1]), reverse=True)

    fallback = None  # If none match, try this.

    for cl, cl_reqs, back_map in cls_and_attrs:
        # We do not have to consider classes we've already processed, since
        # they will have been eliminated by the match dictionary already.
        other_classes = [
            c_and_a
            for c_and_a in cls_and_attrs
            if c_and_a[0] is not cl and c_and_a[0] not in uniq_attrs_dict.values()
        ]
        other_reqs = reduce(or_, (c_a[1] for c_a in other_classes), set())
        uniq = cl_reqs - other_reqs

        # We want a unique attribute with no default.
        cl_fields = fields_dict(get_origin(cl) or cl)
        # Sort for deterministic iteration order
        for maybe_renamed_attr_name in sorted(uniq):
            orig_name = back_map[maybe_renamed_attr_name]
            default = cl_fields[orig_name].default

            if default in (NOTHING, MISSING):
                break
        else:
            if fallback is None:
                fallback = cl
                continue
            msg = f"{cl} has no usable non-default attributes"
            raise TypeError(msg)
        uniq_attrs_dict[maybe_renamed_attr_name] = cl

    log.opt(lazy=True).trace(f"Unique attribute discriminators: {uniq_attrs_dict}")
    log.opt(lazy=True).trace(f"Fallback class: {fallback}")

    # Build the combined disambiguation function
    if not literal_discriminators and not uniq_attrs_dict and fallback is None:
        msg = "Could not create a disambiguation function for the given classes"
        raise ValueError(msg)

    if fallback is None:

        def dis_func(data: Mapping[Any, Any]) -> type[AttrsInstance] | None:
            if not isinstance(data, Mapping):
                msg = "Only input mappings are supported"
                raise TypeError(msg)

            # First try literal discriminators
            for discriminator_name, value_map in literal_discriminators.items():
                if discriminator_name in data:
                    value = data[discriminator_name]
                    if value in value_map:
                        return value_map[value]

            # Then try unique attribute discriminators
            for k, v in uniq_attrs_dict.items():
                if k in data:
                    return v

            msg = "Couldn't disambiguate"
            raise ValueError(msg)

    else:

        def dis_func(data: Mapping[Any, Any]) -> type[AttrsInstance] | None:
            if not isinstance(data, Mapping):
                msg = "Only input mappings are supported"
                raise TypeError(msg)

            # First try literal discriminators
            for discriminator_name, value_map in literal_discriminators.items():
                if discriminator_name in data:
                    value = data[discriminator_name]
                    if value in value_map:
                        return value_map[value]

            # Then try unique attribute discriminators
            for k, v in uniq_attrs_dict.items():
                if k in data:
                    return v

            return fallback

    return dis_func
