"""
Core validation abstractions.

This module defines the base validator protocol and common validator types.
Validators are simple callables that check conditions and return issues.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import Any, Protocol

from attrs import define, field

from .result import Issue


class Validator(Protocol):
    """
    Protocol for validators.

    A validator is any callable that takes an object and context,
    and returns a list of issues (or empty list if valid).
    """

    def __call__(self, obj: Any, path: str = "root") -> list[Issue]:
        """
        Validate an object.

        Args:
            obj: The object to validate
            path: Path to the object in the hierarchy

        Returns:
            List of issues found (empty if valid)
        """
        ...


# Type alias for simple validator functions
ValidatorFunc = Callable[[Any, str], list[Issue]]


from abc import ABC

@define
class BaseValidator(ABC):
    """
    Abstract base class for validators.

    Provides a structured way to create validators with
    better error handling and naming.
    """

    name: str = field(default='')

    def __attrs_post_init__(self) -> None:
        """Set default name to class name if not provided."""
        if not hasattr(self, "name") or not self.name:
            object.__setattr__(self, "name", self.__class__.__name__)

    @abstractmethod
    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """
        Validate an object.

        Args:
            obj: The object to validate
            path: Path to the object in the hierarchy

        Returns:
            List of issues found (empty if valid)
        """
        ...

    def __call__(self, obj: Any, path: str = "root") -> list[Issue]:
        """Make validator callable."""
        return self.validate(obj, path)


@define
class PredicateValidator(BaseValidator):
    """
    Validator based on a simple predicate function.

    Checks if a condition is true, reports an issue if false.
    
    The predicate can return either:
    - bool: True if valid, False if invalid (uses default message)
    - tuple[bool, str]: (is_valid, custom_message) for detailed error reporting

    Example:
        # Simple boolean predicate
        def check_positive(obj):
            return obj.value > 0

        validator = PredicateValidator(
            predicate=check_positive,
            message="Value must be positive",
            name="positive_value"
        )
        
        # Predicate with custom message
        def check_range(obj):
            if obj.value < 0:
                return False, f"Value {obj.value} is negative"
            if obj.value > 100:
                return False, f"Value {obj.value} exceeds maximum of 100"
            return True
            
        validator = PredicateValidator(
            predicate=check_range,
            message="Value must be in range",  # fallback message
            name="value_range"
        )
    """

    predicate: Callable[[Any], bool | tuple[bool, str]] = field()
    message: str = field()
    severity: Callable[..., Issue] = field(default=Issue.error, kw_only=True)
    name: str = field(default="", kw_only=True)

    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """Check if predicate holds."""
        try:
            result = self.predicate(obj)
            
            # Handle tuple return (bool, custom_message)
            if isinstance(result, tuple):
                is_valid, custom_message = result
                if not is_valid:
                    # Use custom message if validation failed
                    return [self.severity(custom_message, path, self.name, obj)]
            # Handle simple bool return
            elif not result:
                return [self.severity(self.message, path, self.name, obj)]
                
        except (AttributeError, TypeError, KeyError) as e:
            return [
                Issue.critical(
                    f"Validator error: {e}",
                    path,
                    self.name,
                    obj,
                ),
            ]
        return []


@define
class FieldValidator(BaseValidator):
    """
    Validator that checks a specific field of an object.
    
    The predicate can return either:
    - bool: True if valid, False if invalid (uses default message)
    - tuple[bool, str]: (is_valid, custom_message) for detailed error reporting

    Example:
        # Simple boolean predicate
        validator = FieldValidator(
            field_name="start",
            predicate=lambda x: x is not None,
            message="Start time must be defined"
        )
        
        # Predicate with custom message
        def check_start_time(start):
            if start is None:
                return False, "Start time is missing"
            if start < pd.Timestamp("2020-01-01"):
                return False, f"Start time {start} is before mission start"
            return True
            
        validator = FieldValidator(
            field_name="start",
            predicate=check_start_time,
            message="Start time validation failed"
        )
    """

    field_name: str = field()
    predicate: Callable[[Any], bool | tuple[bool, str]] = field()
    message: str = field()
    severity: Callable[..., Issue] = field(default=Issue.error, kw_only=True)
    name: str = field(default="", kw_only=True)

    def __attrs_post_init__(self) -> None:
        """Set default name based on field name if not provided."""
        if not self.name:
            object.__setattr__(self, "name", f"check_{self.field_name}")

    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """Check if field satisfies predicate."""
        try:
            if not hasattr(obj, self.field_name):
                return [
                    Issue.critical(
                        f"Object has no field '{self.field_name}'",
                        path,
                        self.name,
                        obj,
                    ),
                ]

            value = getattr(obj, self.field_name)
            result = self.predicate(value)
            
            # Handle tuple return (bool, custom_message)
            if isinstance(result, tuple):
                is_valid, custom_message = result
                if not is_valid:
                    return [self.severity(custom_message, path, self.name, obj)]
            # Handle simple bool return
            elif not result:
                return [self.severity(self.message, path, self.name, obj)]

        except (AttributeError, TypeError, KeyError) as e:
            return [
                Issue.critical(
                    f"Validator error: {e}",
                    path,
                    self.name,
                    obj,
                ),
            ]
        return []


def check(
    predicate: Callable[[Any], bool | tuple[bool, str]],
    message: str,
    severity: Callable[..., Issue] = Issue.error,
    name: str = "",
) -> Validator:
    """
    Create a simple validator from a predicate.
    
    The predicate can return either:
    - bool: True if valid, False if invalid (uses provided message)
    - tuple[bool, str]: (is_valid, custom_message) for detailed error reporting

    Args:
        predicate: Function that returns True/False or (bool, str) tuple
        message: Default error message if predicate fails (used for simple bool returns)
        severity: Issue factory (default: Issue.error)
        name: Optional name for the validator

    Returns:
        Validator function

    Example:
        # Simple boolean predicate
        validator = check(
            lambda obj: obj.start < obj.end,
            "Start must be before end"
        )
        
        # Predicate with detailed messages
        def check_timing(obj):
            if obj.start >= obj.end:
                return False, f"Start {obj.start} must be before end {obj.end}"
            return True
            
        validator = check(
            check_timing,
            "Invalid timing"  # fallback message
        )
    """
    return PredicateValidator(predicate, message, severity=severity, name=name)


def check_field(
    field_name: str,
    predicate: Callable[[Any], bool | tuple[bool, str]],
    message: str,
    name: str = "",
    severity: Callable[..., Issue] = Issue.error,
) -> Validator:
    """
    Create a validator for a specific field.
    
    The predicate can return either:
    - bool: True if valid, False if invalid (uses provided message)
    - tuple[bool, str]: (is_valid, custom_message) for detailed error reporting

    Args:
        field_name: Name of the field to check
        predicate: Function that returns True/False or (bool, str) tuple
        message: Default error message if predicate fails
        severity: Issue factory (default: Issue.error)
        name: Optional name for the validator

    Returns:
        Validator function

    Example:
        # Simple boolean predicate
        validator = check_field(
            "start",
            lambda x: x is not None,
            "Start time must be defined"
        )
        
        # Predicate with detailed messages
        def validate_start(start):
            if start is None:
                return False, "Start time is missing"
            if start < pd.Timestamp("2020-01-01"):
                return False, f"Start {start} is before mission start"
            return True
            
        validator = check_field(
            "start",
            validate_start,
            "Start time validation failed"
        )
    """
    return FieldValidator(field_name, predicate, message, severity=severity, name=name)
