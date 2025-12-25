from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from typing import Literal, Protocol, runtime_checkable

from attrs import define, field
from loguru import logger as log

from ptr_editor.agm_config import AGMConfiguration


def _get_agm_configuration():
    """Lazy import to avoid circular dependencies."""
    from ptr_editor.services.quick_access import get_agm_configuration

    return get_agm_configuration()


class UnknownAGMDefinitionError(ValueError):
    """Raised when an AGM definition is not found."""

    def __init__(self, definition_types: str | Sequence[str], name: str):
        if isinstance(definition_types, str):
            self.definition_types = [definition_types]
        else:
            self.definition_types = list(definition_types)
        self.name = name
        types_str = " or ".join(self.definition_types)
        super().__init__(f"Unknown AGM {types_str}: '{name}'")


AGMDefinitionType = Literal["direction", "object", "frame", "surface"]
AGMDefinitionTypes = AGMDefinitionType | Sequence[AGMDefinitionType]


@runtime_checkable
class HasRef(Protocol):
    """Protocol for objects that have a str ref attribute."""

    ref: str


@define
class AgmConfigValidator:
    cfg: AGMConfiguration = field(factory=lambda: _get_agm_configuration())
    enabled: bool = field(default=True)

    def validate(
        self,
        definition_types: AGMDefinitionTypes,
        name: str | HasRef,
    ) -> None:
        log.opt(lazy=True).trace(
            f"Validating AGM definition for types {definition_types} and name {name}",
        )
        """
        Validate that an AGM definition exists in at least one of the specified types.

        Args:
            definition_types: The type(s) of AGM definition to validate against
            name: The name to validate (str) or an object with a ref attribute

        Raises:
            UnknownAGMDefinitionError: If the definition is not found in any
                of the types
        """
        # Skip validation if disabled
        if not self.enabled:
            log.opt(lazy=True).trace("AGM validation is disabled, skipping validation.")
            return

        # Extract the actual name string from the input
        if isinstance(name, str):
            actual_name = name
        elif isinstance(name, HasRef):
            actual_name = name.ref
        else:
            msg = f"Expected str or object with ref attribute, got {type(name)}"
            raise TypeError(msg)

        # Convert single type to sequence for uniform handling
        if isinstance(definition_types, str):
            types_to_check = [definition_types]
        else:
            types_to_check = list(definition_types)

        validators = {
            "direction": self.cfg.is_known_agm_direction,
            "object": self.cfg.is_known_agm_object,
            "frame": self.cfg.is_known_agm_frame,
            "surface": self.cfg.is_known_agm_surface,
        }

        # Check if the name is valid in any of the specified types
        for definition_type in types_to_check:
            if validators[definition_type](actual_name):
                return  # Found in at least one type, validation passes

        # Not found in any of the specified types

        log.error(
            f"AGM definition '{actual_name}' not found in currently loaded AGM configuration. Checked in: {types_to_check}",
        )
        raise UnknownAGMDefinitionError(definition_types, actual_name)


def get_agm_validator() -> AgmConfigValidator:
    """
    Get the global AGM validator instance from the registry.

    Returns:
        AgmConfigValidator: The global AGM validator instance.

    Example:
        >>> from ptr_editor.validator.agm_config_validator import (
        ...     get_agm_validator,
        ... )
        >>> validator = get_agm_validator()
        >>> validator.validate(
        ...     "direction",
        ...     "Sun",
        ... )
    """
    from ptr_editor.services.quick_access import get_agm_validator as _get_validator

    return _get_validator()


def validator_for(definition_types: AGMDefinitionTypes):
    """Factory method that returns an attrs validator for any definition type(s)."""

    def validator(_instance, _attribute, value):
        get_agm_validator().validate(definition_types, value)

    return validator


@contextmanager
def agm_validation_disabled():
    """
    Context manager to temporarily disable AGM validation.

    Example:
        with agm_validation_disabled():
            # AGM validation is disabled here
            obj = SomeClass(invalid_ref="nonexistent")
        # AGM validation is re-enabled here
    """
    validator = get_agm_validator()
    original_state = validator.enabled
    validator.enabled = False
    try:
        yield
    finally:
        validator.enabled = original_state


@contextmanager
def agm_validation_enabled():
    """
    Context manager to temporarily enable AGM validation.

    Example:
        with agm_validation_enabled():
            # AGM validation is enabled here
            obj = SomeClass(ref="valid_ref")
        # AGM validation returns to previous state here
    """
    validator = get_agm_validator()
    original_state = validator.enabled
    validator.enabled = True
    try:
        yield
    finally:
        validator.enabled = original_state


def disable_agm_validation():
    """Disable AGM validation globally."""
    get_agm_validator().enabled = False


def enable_agm_validation():
    """Enable AGM validation globally."""
    get_agm_validator().enabled = True


def is_known_agm_definition(definition_types: AGMDefinitionTypes):
    """
    Returns a function that checks if a given name is a known AGM definition
    of the specified type(s).
    """
    log.debug(
        "Generating validation function for AGM definition types: %s", definition_types,
    )
    return validator_for(definition_types)


def normalize_agm_name(definition_types: AGMDefinitionTypes | None = None):
    """
    Returns a function that normalizes AGM names to canonical casing.

    The returned function looks up the name in the AGM configuration and returns
    the canonical casing. If not found, returns the value unchanged.

    Args:
        definition_types: The type(s) of AGM definition to search in.
            If None, searches in all types (object, frame, direction, surface).
            Can be a single type or a sequence of types.

    Returns:
        A function that takes a string value and returns the normalized name.

    Example:
        >>> normalizer = normalize_agm_name(
        ...     [
        ...         "object",
        ...         "frame",
        ...     ]
        ... )
        >>> normalizer("sun")
        "Sun"
        >>> normalizer = normalize_agm_name()  # searches all types
        >>> normalizer("sun")
        "Sun"
    """
    # Convert to list of types to check
    if definition_types is None:
        types_to_check = None
    elif isinstance(definition_types, str):
        types_to_check = [definition_types]
    else:
        types_to_check = list(definition_types)

    log.debug(
        f"Generating normalization function for AGM definition types: {types_to_check}",
    )

    def normalizer(value: str | HasRef) -> str | HasRef:
        validator = get_agm_validator()

        if not validator.enabled:
            log.opt(lazy=True).trace(
                "skipping name resolution as validation against AGM is entirely disabled",
            )
            # Extract the actual name string from the input
            return value

        # Extract the actual name string from the input
        if isinstance(value, str):
            actual_name = value
        elif isinstance(value, HasRef):
            actual_name = value.ref
        else:
            log.debug(f"not a string or HasRef, returning as-is: {type(value)}")
            return str(value)

        log.debug(f"normalizing string {actual_name}")

        from ptr_editor.services.quick_access import get_agm_configuration

        agm_config = get_agm_configuration()
        normalized = agm_config.normalize_name(actual_name, types_to_check)

        if normalized != actual_name:
            log.debug(f"normalized {actual_name} to {normalized}")
        else:
            log.debug(f"item {actual_name} was not found in the current agm config")

        if isinstance(value, HasRef):
           value.ref = normalized
           log.debug(f"Updated HasRef object with new ref: {normalized}")
           return value

        return normalized

    return normalizer
