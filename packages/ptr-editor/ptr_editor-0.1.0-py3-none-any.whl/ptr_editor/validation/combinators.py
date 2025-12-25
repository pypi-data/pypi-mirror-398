"""
Validator combinators for composing validation rules.

This module provides functions to combine validators in various ways,
enabling powerful composition of validation logic.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from attrs import define, field

from .result import Issue
from .validator import BaseValidator, Validator


@define
class AllOf(BaseValidator):
    """
    Combinator that requires all validators to pass.

    Returns issues from all validators that fail.

    Example:
        validator = AllOf([
            check(lambda obj: obj.start is not None, "Start required"),
            check(lambda obj: obj.end is not None, "End required"),
        ])
    """

    validators: list[Validator]
    name: str = field(default="all_of")

    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """Run all validators and collect all issues."""
        issues = []
        for validator in self.validators:
            issues.extend(validator(obj, path))
        return issues


@define
class AnyOf(BaseValidator):
    """
    Combinator that requires at least one validator to pass.

    Only returns issues if all validators fail.

    Example:
        validator = AnyOf([
            check(lambda obj: obj.method == "A", "Method A"),
            check(lambda obj: obj.method == "B", "Method B"),
        ], message="Must use method A or B")
    """

    validators: list[Validator]
    message: str = "At least one condition must be satisfied"
    name: str = field(default="any_of", init=False)

    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """Return issue only if all validators fail."""
        for validator in self.validators:
            issues = validator(obj, path)
            if not issues:  # At least one passed
                return []

        # All failed
        return [Issue.error(self.message, path, self.name, obj)]


@define
class Not(BaseValidator):
    """
    Combinator that inverts a validator.

    Passes if the inner validator fails, fails if it passes.

    Example:
        validator = Not(
            check(lambda obj: obj.deprecated, "Is deprecated"),
            message="Must not be deprecated"
        )
    """

    validator: Validator
    message: str = "Condition must not be true"
    name: str = field(default="not", init=False)

    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """Return issue if inner validator passes."""
        issues = self.validator(obj, path)
        if not issues:  # Inner validator passed, so we fail
            return [Issue.error(self.message, path, self.name, obj)]
        return []


@define
class OneOf(BaseValidator):
    """
    Combinator that requires exactly one validator to pass.

    Example:
        validator = OneOf([
            check(lambda obj: obj.type == "A", "Type A"),
            check(lambda obj: obj.type == "B", "Type B"),
        ], message="Must have exactly one valid type")
    """

    validators: list[Validator]
    message: str = "Exactly one condition must be satisfied"
    name: str = field(default="one_of", init=False)

    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """Return issue unless exactly one validator passes."""
        passed_count = sum(
            1 for validator in self.validators if not validator(obj, path)
        )

        if passed_count == 1:
            return []

        if passed_count == 0:
            return [
                Issue.error(
                    f"{self.message} (none passed)",
                    path,
                    self.name,
                    obj,
                ),
            ]
        return [
            Issue.error(
                f"{self.message} (multiple passed)",
                path,
                self.name,
                obj,
            ),
        ]


@define
class Optional(BaseValidator):
    """
    Makes a validator optional based on a condition.

    Only runs the validator if the condition is true.

    Example:
        validator = Optional(
            check(lambda obj: obj.value > 0, "Value must be positive"),
            when=lambda obj: obj.use_value
        )
    """

    validator: Validator
    when: Callable[[Any], bool]
    name: str = field(default="optional", init=False)

    def validate(self, obj: Any, path: str = "root") -> list[Issue]:
        """Run validator only if condition is met."""
        try:
            if self.when(obj):
                return self.validator(obj, path)
        except (AttributeError, TypeError, KeyError) as e:
            return [
                Issue.critical(
                    f"Optional condition error: {e}",
                    path,
                    self.name,
                    obj,
                ),
            ]
        return []


# Convenience functions for creating combinators


def all_of(*validators: Validator, name: str = "") -> Validator:
    """
    Require all validators to pass.

    Args:
        *validators: Validators that must all pass
        name: Optional name for the combinator (ignored, kept for compatibility)

    Returns:
        Combined validator

    Example:
        validator = all_of(
            check(lambda obj: obj.x > 0, "X must be positive"),
            check(lambda obj: obj.y > 0, "Y must be positive"),
        )
    """

    pars = {}
    if name:
        pars["name"] = name

    return AllOf(list(validators), **pars)


def any_of(
    *validators: Validator,
    message: str = "At least one condition must be satisfied",
    name: str = "",
) -> Validator:
    """
    Require at least one validator to pass.

    Args:
        *validators: Validators, at least one must pass
        message: Error message if all fail
        name: Optional name for the combinator (ignored, kept for compatibility)

    Returns:
        Combined validator

    Example:
        validator = any_of(
            check(lambda obj: obj.method == "A", "Method A"),
            check(lambda obj: obj.method == "B", "Method B"),
            message="Must use method A or B"
        )
    """
    return AnyOf(list(validators), message)


def one_of(
    *validators: Validator,
    message: str = "Exactly one condition must be satisfied",
    name: str = "",
) -> Validator:
    """
    Require exactly one validator to pass.

    Args:
        *validators: Validators, exactly one must pass
        message: Error message if not exactly one passes
        name: Optional name for the combinator (ignored, kept for compatibility)

    Returns:
        Combined validator

    Example:
        validator = one_of(
            check(lambda obj: obj.type == "A", "Type A"),
            check(lambda obj: obj.type == "B", "Type B"),
        )
    """
    return OneOf(list(validators), message)


def not_(
    validator: Validator,
    message: str = "Condition must not be true",
    name: str = "",
) -> Validator:
    """
    Invert a validator.

    Args:
        validator: Validator to invert
        message: Error message if original validator passes
        name: Optional name for the combinator (ignored, kept for compatibility)

    Returns:
        Inverted validator

    Example:
        validator = not_(
            check(lambda obj: obj.deprecated, "Is deprecated"),
            message="Must not be deprecated"
        )
    """
    return Not(validator, message)


def optional(
    validator: Validator,
    when: Callable[[Any], bool],
    name: str = "",
) -> Validator:
    """
    Make a validator conditional.

    Args:
        validator: Validator to run conditionally
        when: Predicate that determines if validator should run
        name: Optional name for the combinator (ignored, kept for compatibility)

    Returns:
        Conditional validator

    Example:
        validator = optional(
            check(lambda obj: obj.value > 0, "Value must be positive"),
            when=lambda obj: obj.use_value
        )
    """
    return Optional(validator, when)
