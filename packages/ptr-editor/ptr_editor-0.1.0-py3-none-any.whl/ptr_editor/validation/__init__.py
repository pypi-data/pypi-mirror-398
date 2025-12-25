"""
Modern validation framework for PTR elements.

A clean, composable validation system with clear separation of concerns:
- **Validators**: Simple rules that check conditions
- **Result**: Issue reporting and display
- **Runner**: Execution engine for validators
- **Registry**: Type-based validator organization

Quick Start
-----------

Example 1: Simple validation with predicates::

    from ptr_editor.validation import check, validate

    # Define validators
    start_exists = check(
        lambda obj: obj.start is not None,
        "Start time must be defined"
    )

    end_exists = check(
        lambda obj: obj.end is not None,
        "End time must be defined"
    )

    time_order = check(
        lambda obj: obj.start < obj.end,
        "Start must be before end"
    )

    # Validate an object
    result = validate(my_block, [start_exists, end_exists, time_order])
    if not result.ok:
        print(result)  # Pretty output
        for error in result.errors():
            print(error)

Example 2: Registry-based validation::

    from ptr_editor.validation import Registry, check, check_field

    # Create registry
    registry = Registry()

    # Register validators for a type
    registry.for_type(TimedBlock)\\
        .add(check_field("start", lambda x: x is not None, "Start required"))\\
        .add(check_field("end", lambda x: x is not None, "End required"))\\
        .add(check(lambda obj: obj.start < obj.end, "Start before end"))

    # Validate
    result = registry.validate(my_block)

Example 3: Composable validation with combinators::

    from ptr_editor.validation import all_of, any_of, check

    # Combine validators
    validator = all_of(
        check(lambda obj: obj.start is not None, "Start required"),
        check(lambda obj: obj.end is not None, "End required"),
        any_of(
            check(lambda obj: obj.method == "NADIR", "Method NADIR"),
            check(lambda obj: obj.method == "LIMB", "Method LIMB"),
            message="Method must be NADIR or LIMB"
        )
    )

    result = validate(my_obj, [validator])

Architecture
------------

The validation system is designed with clear separation:

1. **Validators** (``validator.py``):
   - Simple callables: ``(obj, path) -> list[Issue]``
   - ``check()``: Validate predicates
   - ``check_field()``: Validate specific fields
   - BaseValidator for custom validators

2. **Combinators** (``combinators.py``):
   - ``all_of()``: All must pass
   - ``any_of()``: At least one must pass
   - ``one_of()``: Exactly one must pass
   - ``not_()``: Invert validation
   - ``optional()``: Conditional validation

3. **Results** (``result.py``):
   - ``Issue``: Single validation problem
   - ``Result``: Collection of issues
   - Severity levels: INFO, WARNING, ERROR, CRITICAL
   - Pretty printing and HTML output

4. **Runner** (``runner.py``):
   - Executes validators on objects
   - Handles recursive validation
   - Prevents circular references

5. **Registry** (``registry.py``):
   - Organize validators by type
   - Type hierarchy support
   - Fluent registration API
"""

# Import ptr_validators submodule for convenience
from . import ptr_validators
from .combinators import (
    AllOf,
    AnyOf,
    Not,
    OneOf,
    Optional,
    all_of,
    any_of,
    not_,
    one_of,
    optional,
)
from .result import Issue, Result, Severity
from .runner import Runner
from .ruleset_registry import (
    RuleRegistry,
    RuleOverride,
    RulesetConfig,
    ValidationRule,
)
from .validator import (
    BaseValidator,
    FieldValidator,
    PredicateValidator,
    Validator,
    check,
    check_field,
)

__all__ = [
    # Core types
    "Validator",
    "BaseValidator",
    "PredicateValidator",
    "FieldValidator",
    "Issue",
    "Result",
    "Severity",
    "Runner",
    # Rule-based validation
    "ValidationRule",
    "RuleOverride",
    "RulesetConfig",
    "RuleRegistry",
    # Validator creation
    "check",
    "check_field",
    # Combinator classes
    "AllOf",
    "AnyOf",
    "OneOf",
    "Not",
    "Optional",
    # Combinator functions
    "all_of",
    "any_of",
    "one_of",
    "not_",
    "optional",
    # PTR-specific validators
    "ptr_validators",
]
