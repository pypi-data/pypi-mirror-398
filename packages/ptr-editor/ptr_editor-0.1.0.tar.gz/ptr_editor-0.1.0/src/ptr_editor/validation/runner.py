"""
Validation runner for executing validators on object hierarchies.

This module provides the engine for running validators, including
recursive validation of nested objects.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from attrs import define, field, fields, has
from loguru import logger as log

if TYPE_CHECKING:
    from ptr_editor.validation.ruleset_registry import RuleRegistry
    from ptr_editor.validation.validator import Validator

from .result import Issue, Result

# Type alias for ID resolver function
IdResolver = Callable[[Any], str | None]


def default_id_resolver(obj: Any) -> str | None:
    """
    Default ID resolver that checks common attributes.

    Tries to find a human-readable identifier by checking:
    - id property/attribute
    - unique_id attribute
    - name attribute

    Args:
        obj: Object to get ID from

    Returns:
        Human-readable ID string, or None if not found
    """
    # Try common ID attributes in order of preference
    for attr_name in ("id", "unique_id", "name"):
        try:
            value = getattr(obj, attr_name, None)
            if value is not None and value != "":
                return str(value)
        except Exception:  # noqa: S110
            # Some properties might raise exceptions, just skip them
            pass
    return None


@define
class Runner:
    """
    Validation runner that executes validators on objects.

    Handles recursive validation of nested structures and
    prevents infinite loops from circular references.

    Args:
        recursive: Enable recursive validation of nested objects
        registry: Ruleset registry for looking up validators
        skip_private_attrs: Skip attributes starting with underscore
        skip_attrs_names: List of attribute names to skip
        include_ids: Include human-readable IDs in paths when available
        id_resolver: Function to extract ID from objects (uses default if None)
    """

    recursive: bool = field(default=True)
    registry: RuleRegistry | None = field(default=None)
    skip_private_attrs: bool = field(default=False)
    skip_attrs_names: list[str] = field(factory=lambda: ["_parent"])
    include_ids: bool = field(default=True)
    id_resolver: IdResolver | None = field(default=None)
    _active_ruleset: Any = field(default=None, init=False)  # Store active ruleset during validation

    def run(
        self,
        obj: Any,
        validators: list[Validator],
        path: str = "root",
        result: Result | None = None,
        _visited: set[int] | None = None,
        ruleset: Any = None,  # Accept ruleset parameter
    ) -> Result:
        """
        Run validators on an object and optionally its children.

        Args:
            obj: Object to validate
            validators: List of validators to run
            path: Path to object in hierarchy
            result: Existing result to add to (creates new if None)
            _visited: Internal parameter for tracking visited objects (do not use)
            ruleset: Active ruleset for recursive validation

        Returns:
            Validation result with all issues found
        """
        # Store ruleset for use in recursive validation
        if ruleset is not None:
            self._active_ruleset = ruleset
            
        # Initialize for new validation run
        if result is None:
            result = Result()
            _visited = set()

        # Ensure we have a visited set
        if _visited is None:
            _visited = set()

        if self._is_visited(obj, _visited):
            return result

        self._mark_visited(obj, _visited)

        # Format path with ID if available
        formatted_path = self._format_path_with_id(path, obj)

        # If no validators provided but we have a registry and ruleset,
        # get validators from registry for this object type
        if not validators and self.registry is not None and self._active_ruleset is not None:
            applicable_rules = self.registry.get_applicable_rules_for_type(
                type(obj),
                self._active_ruleset,
            )
            validators = [rule.validator for rule, _override in applicable_rules]

        self._run_validators(obj, validators, formatted_path, result)

        if self.recursive:
            self._validate_children(obj, formatted_path, result, _visited)

        return result

    def _format_path_with_id(self, path: str, obj: Any) -> str:
        """
        Add ID to path if available and enabled.

        Args:
            path: Base path
            obj: Object to get ID from

        Returns:
            Path with ID appended if available
        """
        obj_id = self._get_object_id(obj)
        if obj_id:
            return f"{path} (id={obj_id!r})"
        return path

    def _get_object_id(self, obj: Any) -> str | None:
        """
        Get human-readable ID from object using the configured resolver.

        Args:
            obj: Object to get ID from

        Returns:
            Human-readable ID string, or None if not found or disabled
        """
        if not self.include_ids:
            return None

        resolver = self.id_resolver or default_id_resolver
        try:
            return resolver(obj)
        except Exception as e:
            log.debug(f"ID resolver failed for {type(obj).__name__}: {e}")
            return None

    def _format_path_segment(self, base: str, segment: str, obj: Any | None = None) -> str:
        """
        Format a path segment, optionally including object ID.

        Args:
            base: Base path
            segment: Segment to append (e.g., "field_name" or "[0]")
            obj: Object at this path (for ID resolution)

        Returns:
            Formatted path string
        """
        path = f"{base}.{segment}" if not segment.startswith("[") else f"{base}{segment}"

        # Try to add human-readable ID if enabled and object provided
        if obj is not None:
            obj_id = self._get_object_id(obj)
            if obj_id:
                # Format as: path (id="value")
                path = f"{path} (id={obj_id!r})"

        return path

    def _is_visited(self, obj: Any, visited: set[int]) -> bool:
        """Check if object was already visited."""
        return id(obj) in visited

    def _mark_visited(self, obj: Any, visited: set[int]) -> None:
        """Mark object as visited."""
        visited.add(id(obj))

    def _run_validators(
        self,
        obj: Any,
        validators: list[Validator],
        path: str,
        result: Result,
    ) -> None:
        """Execute all validators on an object."""
        for validator in validators:
            log.debug(f"Running {validator} on {type(obj).__name__} at {path}")
            try:
                issues = validator(obj, path)
                result.extend(issues)
            except BaseException as e:  # noqa: BLE001
                log.exception(f"Validator raised exception at {path}")
                result.add(
                    Issue.critical(
                        f"Validator error: {e}",
                        path,
                        str(validator),
                        obj,
                    ),
                )

    def _validate_children(
        self,
        obj: Any,
        path: str,
        result: Result,
        visited: set[int],
    ) -> None:
        """Recursively validate child objects."""
        if not has(type(obj)):
            return

        for attr in fields(type(obj)):
            if self._should_skip_field(attr.name):
                continue

            field_value = getattr(obj, attr.name, None)
            if field_value is None:
                continue

            child_path = self._format_path_segment(path, attr.name, field_value)

            if self._is_sequence(field_value):
                self._validate_sequence(field_value, path, attr.name, result, visited)
            elif has(type(field_value)):
                self._validate_single_child(field_value, child_path, result, visited)

    def _should_skip_field(self, field_name: str) -> bool:
        """Check if a field should be skipped during validation."""
        if self.skip_private_attrs and field_name.startswith("_"):
            log.opt(lazy=True).trace(f"Skipping private attribute: {field_name}")
            return True

        if field_name in self.skip_attrs_names:
            log.opt(lazy=True).trace(f"Skipping attribute: {field_name}")
            return True

        return False

    def _is_sequence(self, value: Any) -> bool:
        """Check if value is a non-string sequence."""
        return isinstance(value, Sequence) and not isinstance(value, str)

    def _validate_sequence(
        self,
        sequence: Sequence,
        base_path: str,
        attr_name: str,
        result: Result,
        visited: set[int],
    ) -> None:
        """Validate all items in a sequence."""
        for i, item in enumerate(sequence):
            if item is None or not has(item):
                continue

            # Format path with index and optionally ID
            item_path = self._format_path_segment(
                base_path,
                f"{attr_name}[{i}]",
                item,
            )

            if self._is_visited(item, visited):
                log.debug(f"Skipping visited {type(item).__name__} at {item_path}")
                continue

            log.debug(f"Visiting {type(item).__name__} at {item_path}")
            self._validate_single_child(item, item_path, result, visited)

    def _validate_single_child(
        self,
        child: Any,
        path: str,
        result: Result,
        visited: set[int],
    ) -> None:
        """Validate a single child object."""
        if self._is_visited(child, visited):
            log.debug(f"Skipping visited {type(child).__name__} at {path}")
            return

        self._mark_visited(child, visited)

        # Run validators if registry is available
        if self.registry is not None and self._active_ruleset is not None:
            # Get applicable rules for this child type using the active ruleset
            applicable_rules = self.registry.get_applicable_rules_for_type(
                type(child),
                self._active_ruleset,
            )

            # Extract validators from rules (no wrapping for recursive validation)
            validators = [rule.validator for rule, _override in applicable_rules]

            if validators:
                log.debug(
                    f"Found {len(validators)} validators for "
                    f"{type(child).__name__} at {path}",
                )
                self._run_validators(child, validators, path, result)

        # Recurse to children
        self._validate_children(child, path, result, visited)
