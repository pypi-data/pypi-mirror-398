"""
Rule-based validation registry with declarative ruleset configuration.

This module provides a flexible validation system where:
- **Rules** are reusable validators registered once with unique IDs and tags
- **Rulesets** are declarative configurations that reference rules and override properties
- **Rule Registry** manages all rules and executes validation according to rulesets

Architecture:
    ValidationRule: A named, reusable validation rule with metadata
    RuleOverride: Configuration to override rule properties in a ruleset
    RulesetConfig: Declarative ruleset that references rules by ID or tag
    RuleRegistry: Central registry for rules and validation execution

Example:
    >>> # Register rules once
    >>> registry = RuleRegistry()
    >>> registry.register_rule(ValidationRule(
    ...     rule_id="timing.start-before-end",
    ...     validator=check(lambda obj: obj.start < obj.end, "Start before end"),
    ...     description="Start time must be before end time",
    ...     tags=["timing", "critical"],
    ...     applicable_types=[TimedBlock],
    ... ))
    >>>
    >>> # Create rulesets declaratively
    >>> strict = RulesetConfig("strict")
    >>> strict.include_rules_with_tags(["critical"])
    >>>
    >>> lenient = RulesetConfig("lenient")
    >>> lenient.include_rule("timing.start-before-end")
    >>> lenient.include_rule("timing.min-duration", severity=Severity.WARNING)
    >>>
    >>> # Validate
    >>> result = registry.validate(my_block, ruleset=strict)
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from loguru import logger

from .result import Issue, Result, Severity
from .runner import Runner
from .validator import (
    BaseValidator,
    FieldValidator,
    PredicateValidator,
    Validator,
)


class ValidationRule:
    """
    A reusable validation rule with unique ID and metadata.

    Rules are defined once and can be referenced in multiple rulesets.
    """

    def __init__(
        self,
        rule_id: str,
        validator: Validator,
        description: str,
        default_severity: Severity = Severity.ERROR,
        tags: list[str] | None = None,
        applicable_types: list[type] | None = None,
    ):
        """
        Initialize a validation rule.

        Args:
            rule_id: Unique identifier for the rule (e.g., "timing.start-before-end")
            validator: The actual validator function
            description: Human-readable description of what the rule checks
            default_severity: Default severity level (can be overridden in rulesets)
            tags: Tags for categorizing and finding rules (e.g., ["timing", "critical"])
            applicable_types: Types this rule can validate (empty = any type)
        """
        self.rule_id = rule_id
        self.validator = validator
        self.description = description
        self.default_severity = default_severity
        self.tags = set(tags or [])
        self.applicable_types = set(applicable_types or [])

    def __repr__(self) -> str:
        """String representation."""
        return f"ValidationRule('{self.rule_id}', tags={list(self.tags)})"


class RuleOverride:
    """
    Configuration to override rule properties in a ruleset.

    Allows changing severity, disabling rules, or providing custom messages.
    """

    def __init__(
        self,
        *,
        severity: Severity | Callable[..., Issue] | None = None,
        enabled: bool = True,
        custom_message: str | None = None,
    ):
        """
        Initialize rule override.

        Args:
            severity: Override severity (Severity enum or Issue factory like Issue.warning)
            enabled: Whether the rule is enabled in this ruleset
            custom_message: Custom error message (overrides validator's default)
        """
        self.severity = severity
        self.enabled = enabled
        self.custom_message = custom_message

    def __repr__(self) -> str:
        """String representation."""
        parts = []
        if not self.enabled:
            parts.append("disabled")
        if self.severity:
            parts.append(f"severity={self.severity}")
        if self.custom_message:
            parts.append("custom_message")
        return f"RuleOverride({', '.join(parts)})"


class RulesetConfig:
    """
    Declarative configuration for a validation ruleset.

    Rulesets reference rules by ID or tag and can override their properties.
    Supports inheritance for composition.
    """

    def __init__(self, name: str, extends: RulesetConfig | None = None):
        """
        Initialize ruleset configuration.

        Args:
            name: Name of the ruleset (e.g., "strict", "lenient", "default")
            extends: Parent ruleset to inherit from (optional)
        """
        self.name = name
        self.extends = extends
        self.rule_overrides: dict[str, RuleOverride] = {}
        self._included_tags: set[str] = set()
        self._excluded_rules: set[str] = set()

    def include_rule(
        self,
        rule_id: str,
        *,
        severity: Severity | Callable[..., Issue] | None = None,
        enabled: bool = True,
        custom_message: str | None = None,
    ) -> RulesetConfig:
        """
        Include a specific rule with optional overrides.

        Args:
            rule_id: ID of the rule to include
            severity: Override severity level
            enabled: Whether the rule is enabled
            custom_message: Custom error message

        Returns:
            Self for method chaining

        Example:
            >>> ruleset.include_rule("timing.min-duration", severity=Severity.WARNING)
        """
        self.rule_overrides[rule_id] = RuleOverride(
            severity=severity,
            enabled=enabled,
            custom_message=custom_message,
        )
        return self

    def include_rules_with_tags(self, tags: list[str]) -> RulesetConfig:
        """
        Include all rules that have any of the specified tags.

        Args:
            tags: List of tags to match

        Returns:
            Self for method chaining

        Example:
            >>> ruleset.include_rules_with_tags(["critical", "timing"])
        """
        self._included_tags.update(tags)
        return self

    def exclude_rule(self, rule_id: str) -> RulesetConfig:
        """
        Explicitly exclude a rule from this ruleset.

        Useful when extending another ruleset but wanting to remove specific rules.

        Args:
            rule_id: ID of the rule to exclude

        Returns:
            Self for method chaining

        Example:
            >>> lenient = RulesetConfig("lenient", extends=strict)
            >>> lenient.exclude_rule("timing.min-duration")
        """
        self._excluded_rules.add(rule_id)
        return self

    def get_effective_rules(self, registry: RuleRegistry) -> dict[str, RuleOverride | None]:
        """
        Get all effective rules for this ruleset, including inherited ones.

        Args:
            registry: Rule registry to resolve rule references

        Returns:
            Dictionary of rule_id -> RuleOverride (or None for default settings)
        """
        effective: dict[str, RuleOverride | None] = {}

        # Start with parent rules if extending
        if self.extends:
            effective.update(self.extends.get_effective_rules(registry))

        # Add rules by tag
        for tag in self._included_tags:
            for rule in registry.find_rules_by_tag(tag):
                if rule.rule_id not in effective:
                    effective[rule.rule_id] = None  # Use default settings

        # Apply explicit rule inclusions/overrides
        effective.update(self.rule_overrides)

        # Remove excluded rules
        for rule_id in self._excluded_rules:
            effective.pop(rule_id, None)

        return effective

    def __repr__(self) -> str:
        """String representation."""
        parts = [f"name='{self.name}'"]
        if self.extends:
            parts.append(f"extends='{self.extends.name}'")
        if self.rule_overrides:
            parts.append(f"{len(self.rule_overrides)} rules")
        if self._included_tags:
            parts.append(f"tags={list(self._included_tags)}")
        return f"RulesetConfig({', '.join(parts)})"


class RuleRegistry:
    """
    Central registry for validation rules.

    Manages rule registration, discovery, and validation execution.
    """

    def __init__(self):
        """Initialize empty rule registry."""
        self._rules: dict[str, ValidationRule] = {}
        self._rules_by_tag: dict[str, set[str]] = defaultdict(set)
        self._rules_by_type: dict[type, set[str]] = defaultdict(set)
        self._runner = Runner(registry=self)

    @property
    def recursive(self) -> bool:
        """Get recursive validation setting."""
        return self._runner.recursive

    @recursive.setter
    def recursive(self, value: bool) -> None:
        """Set recursive validation."""
        self._runner.recursive = value

    @property
    def include_ids(self) -> bool:
        """Get include_ids setting for human-readable IDs in paths."""
        return self._runner.include_ids

    @include_ids.setter
    def include_ids(self, value: bool) -> None:
        """Set include_ids to enable/disable human-readable IDs in paths."""
        self._runner.include_ids = value

    def register_rule(self, rule: ValidationRule) -> None:
        """
        Register a validation rule.

        Args:
            rule: The validation rule to register

        Example:
            >>> registry.register_rule(ValidationRule(
            ...     rule_id="timing.start-before-end",
            ...     validator=check(lambda obj: obj.start < obj.end, "Start before end"),
            ...     description="Start time must be before end time",
            ...     tags=["timing", "critical"],
            ...     applicable_types=[TimedBlock],
            ... ))
        """
        if rule.rule_id in self._rules:
            logger.warning(f"Rule '{rule.rule_id}' already registered, replacing")

        self._rules[rule.rule_id] = rule

        # Index by tags
        for tag in rule.tags:
            self._rules_by_tag[tag].add(rule.rule_id)

        # Index by applicable types (including parent classes)
        for obj_type in rule.applicable_types:
            for cls in obj_type.__mro__:
                self._rules_by_type[cls].add(rule.rule_id)

        logger.debug(f"Registered rule: {rule.rule_id}")

    def get_rule(self, rule_id: str) -> ValidationRule | None:
        """
        Get a rule by its ID.

        Args:
            rule_id: The rule identifier

        Returns:
            The rule, or None if not found
        """
        return self._rules.get(rule_id)

    def find_rules_by_tag(self, tag: str) -> list[ValidationRule]:
        """
        Find all rules with a specific tag.

        Args:
            tag: The tag to search for

        Returns:
            List of matching rules
        """
        rule_ids = self._rules_by_tag.get(tag, set())
        return [self._rules[rid] for rid in rule_ids if rid in self._rules]

    def list_rules(self, tags: list[str] | None = None) -> list[ValidationRule]:
        """
        List all registered rules, optionally filtered by tags.

        Args:
            tags: Optional list of tags to filter by (returns rules with ANY tag)

        Returns:
            List of matching rules
        """
        if tags is None:
            return list(self._rules.values())

        matching_rule_ids: set[str] = set()
        for tag in tags:
            matching_rule_ids.update(self._rules_by_tag.get(tag, set()))

        return [self._rules[rid] for rid in matching_rule_ids if rid in self._rules]

    def get_applicable_rules_for_type(
        self,
        obj_type: type,
        ruleset: RulesetConfig,
    ) -> list[tuple[ValidationRule, RuleOverride | None]]:
        """
        Get all rules applicable to a type according to a ruleset.

        Args:
            obj_type: The type to get rules for
            ruleset: The ruleset configuration

        Returns:
            List of (rule, override) tuples for applicable rules
        """
        effective_rules = ruleset.get_effective_rules(self)
        applicable: list[tuple[ValidationRule, RuleOverride | None]] = []

        for rule_id, override in effective_rules.items():
            # Skip if explicitly disabled
            if override and not override.enabled:
                continue

            rule = self.get_rule(rule_id)
            if rule is None:
                logger.warning(f"Rule '{rule_id}' referenced in ruleset but not registered")
                continue

            # Check if rule applies to this type
            if rule.applicable_types:
                # Rule has specific types - check if obj_type matches
                type_matches = any(
                    issubclass(obj_type, applicable_type)
                    for applicable_type in rule.applicable_types
                )
                if not type_matches:
                    continue
            # If no applicable_types specified, rule applies to all types

            applicable.append((rule, override))

        return applicable

    def validate(
        self,
        obj: Any,
        path: str = "root",
        *,
        recursive: bool | None = None,
        ruleset: RulesetConfig | str,
    ) -> Result:
        """
        Validate an object using a ruleset.

        Args:
            obj: Object to validate
            path: Path to object in hierarchy
            recursive: Override recursive setting (uses registry default if None)
            ruleset: Ruleset to use (name string or RulesetConfig object)

        Returns:
            Validation result

        Example:
            >>> strict = RulesetConfig("strict")
            >>> strict.include_rules_with_tags(["critical"])
            >>> result = registry.validate(my_block, ruleset=strict)
            >>> if not result.ok:
            ...     print(result)
        """
        # Resolve ruleset if string name given
        if isinstance(ruleset, str):
            raise ValueError(
                f"Ruleset name '{ruleset}' provided but ruleset objects must be passed directly. "
                f"Create with: RulesetConfig('{ruleset}')"
            )

        # Get applicable rules for this object's type
        applicable_rules = self.get_applicable_rules_for_type(type(obj), ruleset)

        # Create wrapped validators with overrides
        validators = []
        for rule, override in applicable_rules:
            validator = self._wrap_validator(rule, override)
            validators.append(validator)

        # Execute validation
        if recursive is not None:
            original = self._runner.recursive
            self._runner.recursive = recursive
            try:
                return self._runner.run(obj, validators, path, ruleset=ruleset)
            finally:
                self._runner.recursive = original
        else:
            return self._runner.run(obj, validators, path, ruleset=ruleset)

    def _wrap_validator(
        self,
        rule: ValidationRule,
        override: RuleOverride | None,
    ) -> Validator:
        """
        Wrap a validator with override settings.

        Args:
            rule: The validation rule
            override: Optional override settings

        Returns:
            Wrapped validator
        """
        base_validator = rule.validator

        # If no overrides, return as-is
        if override is None:
            return base_validator

        # Create wrapper that applies overrides
        def wrapped_validator(obj: Any, path: str = "root") -> list[Issue]:
            issues = base_validator(obj, path)

            if not issues:
                return []

            # Apply overrides to issues
            modified_issues = []
            for issue in issues:
                # Apply custom message if provided
                message = override.custom_message if override.custom_message else issue.message

                # Apply severity override if provided
                if override.severity:
                    if isinstance(override.severity, Severity):
                        # Convert Severity enum to Issue factory
                        severity_map = {
                            Severity.INFO: Issue.info,
                            Severity.WARNING: Issue.warning,
                            Severity.ERROR: Issue.error,
                            Severity.CRITICAL: Issue.critical,
                        }
                        issue_factory = severity_map.get(override.severity, Issue.error)
                    else:
                        # Already an Issue factory
                        issue_factory = override.severity

                    modified_issues.append(
                        issue_factory(message, issue.path, issue.source, issue.obj)
                    )
                else:
                    # Keep original severity but update message if needed
                    if override.custom_message:
                        # Reconstruct with new message
                        severity_map = {
                            Severity.INFO: Issue.info,
                            Severity.WARNING: Issue.warning,
                            Severity.ERROR: Issue.error,
                            Severity.CRITICAL: Issue.critical,
                        }
                        issue_factory = severity_map.get(issue.severity, Issue.error)
                        modified_issues.append(
                            issue_factory(message, issue.path, issue.source, issue.obj)
                        )
                    else:
                        modified_issues.append(issue)

            return modified_issues

        return wrapped_validator

    def get_validators(self, obj_type: type) -> list[Validator]:
        """
        Get validators for a type (used by Runner for recursive validation).

        This is called by the Runner during recursive validation.
        Returns empty list since we need a ruleset to determine which rules apply.

        Args:
            obj_type: Type to get validators for

        Returns:
            Empty list (recursive validation uses active ruleset)
        """
        # During recursive validation, the Runner will call this.
        # We can't return validators here without knowing which ruleset to use.
        # The initial validate() call handles the ruleset resolution.
        return []

    def as_pandas(self):
        """
        Generate a pandas DataFrame listing all registered rules.

        Returns:
            DataFrame with rule information
        """
        import pandas as pd

        records = []
        for rule in self._rules.values():
            # Get validator category
            validator = rule.validator
            if isinstance(validator, PredicateValidator):
                category = "Predicate"
                message = validator.message
                field = ""
            elif isinstance(validator, FieldValidator):
                category = "Field"
                message = validator.message
                field = validator.field_name
            elif isinstance(validator, BaseValidator):
                category = "Base"
                message = ""
                field = ""
            else:
                category = "Custom"
                message = ""
                field = ""

            applicable_types_str = ", ".join(
                t.__name__ for t in rule.applicable_types
            ) if rule.applicable_types else "Any"

            records.append({
                "Rule ID": rule.rule_id,
                "Description": rule.description,
                "Category": category,
                "Field": field,
                "Message": message,
                "Default Severity": rule.default_severity.value,
                "Tags": ", ".join(sorted(rule.tags)),
                "Applicable Types": applicable_types_str,
            })

        if not records:
            return pd.DataFrame(
                columns=[
                    "Rule ID",
                    "Description",
                    "Category",
                    "Field",
                    "Message",
                    "Default Severity",
                    "Tags",
                    "Applicable Types",
                ]
            )

        return pd.DataFrame(records)

    def _repr_html_(self):
        """HTML representation for Jupyter notebooks."""
        return self.as_pandas().to_html()

    def __repr__(self) -> str:
        """String representation."""
        return f"RuleRegistry({len(self._rules)} rules, {len(self._rules_by_tag)} tags: {list(self._rules_by_tag.keys())})"
