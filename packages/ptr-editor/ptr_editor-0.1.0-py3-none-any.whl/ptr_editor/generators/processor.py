"""Process any tree of attrs elements, looks for generators and expands them."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from typing import Any

import attrs
from attrs import define, field
from loguru import logger as log

from ptr_editor.core.tree_utils import walk_attrs_tree
from ptr_editor.generators.base import PtrElementGenerator


@define
class GeneratorProcessor:
    """Process attrs element trees and expand PtrElementGenerator instances.

    This processor walks through a tree of attrs-decorated objects, identifies
    any fields containing PtrElementGenerator instances, and replaces them with
    the actual PtrElement instances produced by calling their
    `_element_generate_()` method.

    The processing is done in two phases:
    1. Collect all generators in the tree
    2. Expand them in the correct order (depth-first)

    Example:
        processor = GeneratorProcessor()

        # Create an object with generators
        obs_block = ObsBlock(attitude=TrackAttitudeGenerator())

        # Expand all generators in the tree
        expanded = processor.process(obs_block)

        # Now expanded.attitude is a TrackAttitude instance,
        # not a generator
    """

    """Initialize the generator processor."""
    _visited: set[int] = field(
        factory=set,
        init=False,
    )  # Track visited objects to avoid cycles
    _generators: list[tuple[Any, str, PtrElementGenerator, int]] = field(
        factory=list,
        init=False,
    )  # (parent, field_name, generator, depth)

    def process(self, obj: Any) -> Any:
        """
        Process an object and expand all generators in its tree.

        Args:
            obj: The object to process

        Returns:
            The processed object with all generators expanded

        Note:
            This method modifies the object in-place by replacing generator
            instances with their generated values. It also returns the object
            for convenience.
        """
        log.info(f"Starting generator processing for {type(obj).__name__}")

        # Phase 1: Collect all generators
        self._visited = set()
        self._generators = []
        self._collect_generators(obj, depth=0)

        log.info(f"Found {len(self._generators)} generator(s) to expand")

        # Phase 2: Expand generators in depth-first order (deepest first)
        # This ensures nested generators are expanded before their parents
        self._generators.sort(key=lambda x: x[3], reverse=True)

        for parent, field_name, generator, depth in self._generators:
            self._expand_single_generator(parent, field_name, generator, depth)

        log.info(f"Completed generator processing for {type(obj).__name__}")
        return obj

    def _collect_generators(self, obj: Any, depth: int = 0) -> None:
        """
        Collect all generators in the tree.

        Args:
            obj: The object to scan for generators
            depth: Current depth in the tree (for ordering)
        """
        # Use walk_attrs_tree to traverse the object tree
        depth_map: dict[int, int] = {id(obj): depth}  # Track depth by object id

        def track_depth(parent: Any, _field_name: str, field_value: Any) -> None:
            """Track the depth of each object in the tree."""
            parent_id = id(parent)
            parent_depth = depth_map.get(parent_id, depth)

            # Set depth for the field value
            if field_value is not None and attrs.has(type(field_value)):
                depth_map[id(field_value)] = parent_depth + 1

            # Handle sequences - set depth for items
            if isinstance(field_value, Sequence) and not isinstance(field_value, str):
                for item in field_value:
                    if item is not None and attrs.has(type(item)):
                        depth_map[id(item)] = parent_depth + 1

        # First pass: walk tree and track depths
        for parent, field_name, field_value in walk_attrs_tree(
            obj,
            visit_func=track_depth,
            skip_none=False,
        ):
            parent_depth = depth_map.get(id(parent), depth)

            # Check if this field contains a generator
            if isinstance(field_value, PtrElementGenerator):
                log.debug(
                    f"Found generator at {type(parent).__name__}.{field_name} "
                    f"(depth {parent_depth})",
                )
                self._generators.append((parent, field_name, field_value, parent_depth))

            # Handle generators in sequences
            elif isinstance(field_value, Sequence) and not isinstance(
                field_value,
                str,
            ):
                for i, item in enumerate(field_value):
                    if isinstance(item, PtrElementGenerator):
                        log.debug(
                            f"Found generator in list at {type(parent).__name__}."
                            f"{field_name}[{i}] (depth {parent_depth})",
                        )
                        self._generators.append(
                            (parent, field_name, item, parent_depth),
                        )


    def _expand_single_generator(
        self,
        obj: Any,
        field_name: str,
        generator: PtrElementGenerator,
        depth: int,
    ) -> None:
        """
        Expand a single generator and update the field.

        Args:
            obj: The parent object containing the generator
            field_name: The field name where the generator is stored
            generator: The generator to expand
            depth: Depth in the tree (for logging)
        """
        log.info(
            f"Expanding generator at {type(obj).__name__}.{field_name} (depth {depth})",
        )
        expanded_value = generator._element_generate_()

        field_value = getattr(obj, field_name)

        # Handle generators in lists
        if isinstance(field_value, Sequence) and not isinstance(field_value, str):
            # Find and replace the generator in the list
            new_list = []
            modified = False
            for item in field_value:
                if item is generator:
                    # Check if the expanded value is itself a sequence
                    if isinstance(expanded_value, Sequence) and not isinstance(
                        expanded_value,
                        str,
                    ):
                        # Generator returned a list/iterable
                        # Flatten it into the parent list
                        log.debug(
                            f"Generator returned a sequence with "
                            f"{len(expanded_value)} items, flattening into list",
                        )
                        new_list.extend(expanded_value)
                    else:
                        # Generator returned a single item
                        new_list.append(expanded_value)
                    modified = True
                else:
                    new_list.append(item)

            if modified:
                # Convert back to original sequence type if needed
                if not isinstance(field_value, list):
                    with suppress(TypeError, ValueError):
                        new_list = type(field_value)(new_list)  # type: ignore[call-arg]
                setattr(obj, field_name, new_list)
                log.info(
                    f"Updated list field {type(obj).__name__}.{field_name} "
                    f"(now has {len(new_list)} items)",
                )
        else:
            # Direct field replacement
            setattr(obj, field_name, expanded_value)
            log.info(
                f"Expanded generator to {type(expanded_value).__name__} "
                f"at {type(obj).__name__}.{field_name}",
            )
