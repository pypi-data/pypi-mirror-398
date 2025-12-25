# PTR Editor Validation Framework

A modern, composable validation framework for PTR elements with clean separation of concerns and declarative rule configuration.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Architecture](#architecture)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [PTR-Specific Validators](#ptr-specific-validators)

## Overview

The validation framework provides a flexible, reusable system for validating PTR elements. It features:

- **Simple validator functions** based on predicates
- **Composable combinators** for building complex validation logic
- **Rule-based configuration** for organizing validators by type
- **Declarative rulesets** for different validation scenarios (strict, lenient, etc.)
- **Recursive validation** for nested object hierarchies
- **Rich reporting** with severity levels, paths, and pretty output
- **Jupyter integration** with HTML display and pandas export

### Key Features

- 🔍 **Type-aware**: Validators apply to specific types with inheritance support
- 🔄 **Composable**: Combine validators using `all_of`, `any_of`, `one_of`, `not_`, `optional`
- 📋 **Rule-based**: Register rules once, reference in multiple rulesets
- 🏷️ **Tagged**: Organize rules by tags (timing, critical, metadata, etc.)
- 🔁 **Recursive**: Automatically validate nested structures
- 📊 **Reportable**: Export to pandas, HTML, or pretty-print console output

## Quick Start

### Simple Validation

```python
from ptr_editor.validation import check, check_field, Result

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
from ptr_editor.validation import Runner, Result

runner = Runner()
result = runner.run(my_block, [start_exists, end_exists, time_order])

if not result.ok:
    print(result)  # Pretty output
    for error in result.errors():
        print(error)
```

### Using the Rule Registry (Recommended)

```python
from ptr_editor.validation import RuleRegistry, RulesetConfig, ValidationRule
from ptr_editor.validation import check, Severity
from ptr_editor.elements.blocks import TimedBlock

# Create registry
registry = RuleRegistry()

# Register rules with IDs, tags, and metadata
registry.register_rule(ValidationRule(
    rule_id="timing.start-before-end",
    validator=check(lambda obj: obj.start < obj.end, "Start before end"),
    description="Start time must be before end time",
    default_severity=Severity.ERROR,
    tags=["timing", "critical"],
    applicable_types=[TimedBlock],
))

# Create a ruleset
strict = RulesetConfig("strict")
strict.include_rules_with_tags(["critical"])

# Validate
result = registry.validate(my_block, ruleset=strict, recursive=True)

if not result.ok:
    print(result)
```

### Using PTR Validators

```python
from ptr_editor.validation.ptr_validators import (
    create_default_ptr_validation_registry,
    create_default_ruleset,
    create_strict_ruleset,
)

# Get pre-configured registry with all PTR rules
registry = create_default_ptr_validation_registry()

# Use default ruleset (all PTR rules)
default_ruleset = create_default_ruleset()
result = registry.validate(my_timeline, ruleset=default_ruleset, recursive=True)

# Or use strict ruleset (only critical rules)
strict_ruleset = create_strict_ruleset()
result = registry.validate(my_timeline, ruleset=strict_ruleset, recursive=True)

if not result.ok:
    print(result)
    # View in pandas
    df = result.as_pandas()
    display(df)
```

## Core Concepts

### 1. Validators

Validators are simple callables that check conditions and return issues:

```python
from typing import Any
from ptr_editor.validation import Issue

def my_validator(obj: Any, path: str = "root") -> list[Issue]:
    """A validator is just a callable that returns issues."""
    if not some_condition(obj):
        return [Issue.error("Something is wrong", path)]
    return []
```

The framework provides convenient factory functions:

```python
from ptr_editor.validation import check, check_field

# Predicate-based validator
validator = check(
    lambda obj: obj.value > 0,
    "Value must be positive"
)

# Field-specific validator
validator = check_field(
    "start",
    lambda x: x is not None,
    "Start time must be defined"
)
```

### 2. Combinators

Combine validators to build complex logic:

```python
from ptr_editor.validation import all_of, any_of, one_of, not_, optional

# All must pass
validator = all_of(
    check(lambda obj: obj.start is not None, "Start required"),
    check(lambda obj: obj.end is not None, "End required"),
)

# At least one must pass
validator = any_of(
    check(lambda obj: obj.method == "NADIR", "Method NADIR"),
    check(lambda obj: obj.method == "LIMB", "Method LIMB"),
    message="Method must be NADIR or LIMB"
)

# Exactly one must pass
validator = one_of(
    check(lambda obj: obj.type == "A", "Type A"),
    check(lambda obj: obj.type == "B", "Type B"),
)

# Invert condition
validator = not_(
    check(lambda obj: obj.deprecated, "Is deprecated"),
    message="Must not be deprecated"
)

# Conditional validation
validator = optional(
    check(lambda obj: obj.value > 0, "Value must be positive"),
    when=lambda obj: obj.use_value
)
```

### 3. Results and Issues

Validation results contain issues with severity levels:

```python
from ptr_editor.validation import Result, Issue, Severity

result = Result()

# Add issues with different severities
result.add(Issue.info("FYI: Optional field missing", path="root.metadata"))
result.add(Issue.warning("Non-critical issue", path="root.name"))
result.add(Issue.error("Validation failed", path="root.value"))
result.add(Issue.critical("Fatal error", path="root"))

# Query results
print(result.ok)  # False (has errors)
print(result.has_warnings)  # True
print(len(result))  # 4 issues total

# Get specific issues
errors = result.errors()  # ERROR and CRITICAL
warnings = result.warnings()  # WARNING only
infos = result.infos()  # INFO only

# Pretty print
print(result)

# Export to pandas
df = result.as_pandas()

# HTML output (Jupyter)
display(result)  # Automatically uses _repr_html_()
```

### 4. Validation Rules

Rules are reusable validators with metadata:

```python
from ptr_editor.validation import ValidationRule, Severity
from ptr_editor.validation import check

rule = ValidationRule(
    rule_id="timing.start-before-end",
    validator=check(lambda obj: obj.start < obj.end, "Start before end"),
    description="Start time must be before end time",
    default_severity=Severity.ERROR,
    tags=["timing", "critical"],
    applicable_types=[TimedBlock],
)
```

### 5. Rulesets

Rulesets are declarative configurations that reference rules:

```python
from ptr_editor.validation import RulesetConfig, Severity

# Create base ruleset
default = RulesetConfig("default")
default.include_rules_with_tags(["ptr"])

# Create strict ruleset
strict = RulesetConfig("strict")
strict.include_rules_with_tags(["critical"])

# Create lenient ruleset by extending strict
lenient = RulesetConfig("lenient", extends=strict)
lenient.exclude_rule("timing.min-duration")
lenient.include_rule("obs.metadata-exists", severity=Severity.WARNING)
```

### 6. Rule Registry

The registry manages rules and executes validation:

```python
from ptr_editor.validation import RuleRegistry

registry = RuleRegistry()

# Register rules
registry.register_rule(rule1)
registry.register_rule(rule2)

# Query rules
all_rules = registry.list_rules()
timing_rules = registry.list_rules(tags=["timing"])
specific_rule = registry.get_rule("timing.start-before-end")

# Validate with a ruleset
result = registry.validate(my_object, ruleset=my_ruleset, recursive=True)

# View registry in Jupyter
display(registry)  # Shows table of all rules
```

## Architecture

The framework has a clean layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                     │
│  (PTR-specific validators, convenience functions)       │
│              ptr_validators.py                          │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 Rule Management Layer                   │
│  (Registry, rulesets, rule configuration)               │
│           ruleset_registry.py                           │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Execution Layer                       │
│  (Validation runner, recursive traversal)               │
│                  runner.py                              │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Logic Layer                           │
│  (Validators, combinators)                              │
│        validator.py, combinators.py                     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Result Layer                          │
│  (Issue tracking, reporting, output)                    │
│              result.py, html.py                         │
└─────────────────────────────────────────────────────────┘
```

### Module Overview

- **`validator.py`**: Core validator protocol and base validators
- **`combinators.py`**: Composition of validators (all_of, any_of, etc.)
- **`result.py`**: Issue and Result classes for reporting
- **`runner.py`**: Execution engine for validators with recursion
- **`ruleset_registry.py`**: Rule-based validation system
- **`ptr_validators.py`**: PTR-specific validation rules
- **`html.py`**: HTML rendering for Jupyter notebooks

## Usage Examples

### Example 1: Simple Field Validation

```python
from ptr_editor.validation import check_field, Runner, Result

# Create validators
validators = [
    check_field("name", lambda x: x is not None, "Name is required"),
    check_field("age", lambda x: x >= 0, "Age must be non-negative"),
]

# Validate
runner = Runner()
result = runner.run(person, validators)

if not result.ok:
    for error in result.errors():
        print(error)
```

### Example 2: Complex Validation with Combinators

```python
from ptr_editor.validation import check, all_of, any_of, optional

# Build complex validator
validator = all_of(
    check(lambda obj: obj.start is not None, "Start required"),
    check(lambda obj: obj.end is not None, "End required"),
    check(lambda obj: obj.start < obj.end, "Start before end"),
    any_of(
        check(lambda obj: obj.method == "NADIR", "NADIR method"),
        check(lambda obj: obj.method == "LIMB", "LIMB method"),
        message="Method must be NADIR or LIMB"
    ),
    optional(
        check(lambda obj: obj.priority > 0, "Priority must be positive"),
        when=lambda obj: hasattr(obj, "priority")
    )
)

runner = Runner()
result = runner.run(my_block, [validator])
```

### Example 3: Registry with Multiple Rulesets

```python
from ptr_editor.validation import RuleRegistry, RulesetConfig, ValidationRule
from ptr_editor.validation import check, Severity

# Create and configure registry
registry = RuleRegistry()

# Register rules
registry.register_rule(ValidationRule(
    rule_id="timing.start-exists",
    validator=check_field("start", lambda x: x is not None, "Start required"),
    description="Start time must be defined",
    tags=["timing", "critical"],
    applicable_types=[TimedBlock],
))

registry.register_rule(ValidationRule(
    rule_id="timing.min-duration",
    validator=check(
        lambda obj: obj.end - obj.start >= timedelta(minutes=2),
        "Duration must be at least 2 minutes"
    ),
    description="Block must have minimum duration",
    tags=["timing", "duration"],
    applicable_types=[TimedBlock],
))

# Create strict ruleset (only critical)
strict = RulesetConfig("strict")
strict.include_rules_with_tags(["critical"])

# Create default ruleset (all timing rules)
default = RulesetConfig("default")
default.include_rules_with_tags(["timing"])

# Create lenient ruleset (critical + warnings for duration)
lenient = RulesetConfig("lenient", extends=strict)
lenient.include_rule("timing.min-duration", severity=Severity.WARNING)

# Validate with different rulesets
strict_result = registry.validate(my_block, ruleset=strict)
default_result = registry.validate(my_block, ruleset=default)
lenient_result = registry.validate(my_block, ruleset=lenient)
```

### Example 4: Recursive Validation

```python
from ptr_editor.validation.ptr_validators import (
    create_default_ptr_validation_registry,
    create_default_ruleset,
)

# Get registry with all PTR rules
registry = create_default_ptr_validation_registry()
ruleset = create_default_ruleset()

# Validate timeline recursively (validates all nested blocks)
result = registry.validate(
    my_timeline,
    ruleset=ruleset,
    recursive=True  # Validates nested ObsBlocks, SlewBlocks, etc.
)

# Results include issues from all nested objects
if not result.ok:
    for error in result.errors():
        print(f"{error.path}: {error.message}")
```

### Example 5: Custom Rule Override

```python
from ptr_editor.validation import RulesetConfig, Severity

# Create custom ruleset with overrides
custom = RulesetConfig("custom")
custom.include_rules_with_tags(["ptr"])

# Override specific rule to be a warning instead of error
custom.include_rule(
    "timing.min-duration",
    severity=Severity.WARNING,
    custom_message="Duration is shorter than recommended"
)

# Disable a rule
custom.include_rule("obs.metadata-exists", enabled=False)

result = registry.validate(my_timeline, ruleset=custom, recursive=True)
```

### Example 6: Human-Readable Paths with IDs

```python
from ptr_editor.validation import RuleRegistry

registry = RuleRegistry()
registry.include_ids = True  # Enable ID display in paths (default)

# Now validation paths will include IDs when available:
# root (id='TIMELINE_001').obs_blocks[0] (id='OBS_001')
# root (id='TIMELINE_001').obs_blocks[1] (id='SLEW_001')

result = registry.validate(my_timeline, ruleset=ruleset, recursive=True)
for error in result.errors():
    print(error.path)  # Shows readable path with IDs
```

## API Reference

### Core Validator Functions

#### `check(predicate, message, severity=Issue.error, name="")`

Create a validator from a predicate function.

**Parameters:**
- `predicate`: Function that returns True if valid
- `message`: Error message if validation fails
- `severity`: Issue factory (default: `Issue.error`)
- `name`: Optional name for the validator

**Returns:** Validator function

#### `check_field(field_name, predicate, message, severity=Issue.error, name="")`

Create a validator for a specific field.

**Parameters:**
- `field_name`: Name of the field to check
- `predicate`: Function that returns True if field value is valid
- `message`: Error message if validation fails
- `severity`: Issue factory (default: `Issue.error`)
- `name`: Optional name for the validator

**Returns:** Validator function

### Combinators

#### `all_of(*validators, name="")`

Require all validators to pass. Returns issues from all that fail.

#### `any_of(*validators, message="At least one condition must be satisfied", name="")`

Require at least one validator to pass. Returns issue only if all fail.

#### `one_of(*validators, message="Exactly one condition must be satisfied", name="")`

Require exactly one validator to pass.

#### `not_(validator, message="Condition must not be true", name="")`

Invert a validator. Passes if validator fails, fails if validator passes.

#### `optional(validator, when, name="")`

Make a validator conditional based on a predicate.

### Result Classes

#### `Issue(severity, message, path="root", source="", obj=None)`

Represents a single validation issue.

**Class methods:**
- `Issue.info(message, path, source, obj)`: Create info issue
- `Issue.warning(message, path, source, obj)`: Create warning
- `Issue.error(message, path, source, obj)`: Create error
- `Issue.critical(message, path, source, obj)`: Create critical issue

#### `Result(issues=[])`

Container for validation results.

**Properties:**
- `ok`: True if no errors or critical issues
- `has_warnings`: True if any warnings
- `has_errors`: True if any errors or critical issues

**Methods:**
- `add(issue)`: Add an issue
- `extend(issues)`: Add multiple issues
- `merge(other)`: Merge another result
- `errors()`: Get all errors and critical issues
- `warnings()`: Get all warnings
- `infos()`: Get all info issues
- `by_severity(severity)`: Get issues of specific severity
- `as_pandas()`: Export to pandas DataFrame
- `_repr_html_()`: HTML representation for Jupyter

### Rule Management

#### `ValidationRule(rule_id, validator, description, default_severity=Severity.ERROR, tags=None, applicable_types=None)`

A reusable validation rule with metadata.

**Parameters:**
- `rule_id`: Unique identifier (e.g., "timing.start-before-end")
- `validator`: The validator function
- `description`: Human-readable description
- `default_severity`: Default severity level
- `tags`: Tags for categorizing rules
- `applicable_types`: Types this rule can validate

#### `RulesetConfig(name, extends=None)`

Declarative configuration for a validation ruleset.

**Methods:**
- `include_rule(rule_id, severity=None, enabled=True, custom_message=None)`: Include specific rule
- `include_rules_with_tags(tags)`: Include all rules with specified tags
- `exclude_rule(rule_id)`: Exclude a rule
- `get_effective_rules(registry)`: Get all effective rules including inherited

#### `RuleRegistry()`

Central registry for validation rules.

**Properties:**
- `recursive`: Enable/disable recursive validation
- `include_ids`: Enable/disable human-readable IDs in paths

**Methods:**
- `register_rule(rule)`: Register a validation rule
- `get_rule(rule_id)`: Get rule by ID
- `find_rules_by_tag(tag)`: Find rules with specific tag
- `list_rules(tags=None)`: List all rules, optionally filtered
- `validate(obj, path="root", recursive=None, ruleset)`: Validate object
- `as_pandas()`: Export registry to pandas DataFrame

### Runner

#### `Runner(recursive=True, registry=None, skip_private_attrs=False, skip_attrs_names=["_parent"], include_ids=True)`

Validation runner for executing validators.

**Parameters:**
- `recursive`: Enable recursive validation
- `registry`: Rule registry for type-based lookup
- `skip_private_attrs`: Skip attributes starting with underscore
- `skip_attrs_names`: List of attribute names to skip
- `include_ids`: Include human-readable IDs in paths

**Methods:**
- `run(obj, validators, path="root", result=None)`: Run validators on object

## PTR-Specific Validators

The `ptr_validators` module provides pre-configured validators for PTR elements.

### Registered Rules

#### TimedBlock Rules

- `ptr.timing.start-exists`: Start time must be defined
- `ptr.timing.end-exists`: End time must be defined
- `ptr.timing.start-before-end`: Start before end time
- `ptr.timing.positive-duration`: Duration must be positive
- `ptr.timing.min-duration`: Duration must be at least 2 minutes

Tags: `timing`, `critical`, `duration`, `ptr`

#### ObsBlock Rules

- `ptr.obs.attitude-defined`: Attitude must be defined
- `ptr.obs.metadata-exists`: Metadata should exist
- `ptr.obs.min-slew-after`: Sufficient slew time after block

Tags: `obs`, `metadata`, `timing`, `slew`, `ptr`

#### Timeline Rules

- `ptr.timeline.unique-block-ids`: All blocks must have unique IDs
- `ptr.timeline.has-blocks`: Timeline must contain blocks
- `ptr.timeline.slews-at-odd-indices`: SlewBlocks between observations

Tags: `timeline`, `critical`, `slew`, `ptr`

### Convenience Functions

#### `create_default_ptr_validation_registry()`

Create a registry with all PTR rules pre-registered.

#### `create_default_ruleset()`

Create a ruleset that includes all PTR rules.

#### `create_strict_ruleset()`

Create a ruleset with only critical rules.

#### `validate_timed_block(block, recursive=False)`

Validate a TimedBlock using default PTR validators.

#### `validate_obs_block(block, recursive=False)`

Validate an ObsBlock using default PTR validators.

### Usage

```python
from ptr_editor.validation.ptr_validators import (
    create_default_ptr_validation_registry,
    create_default_ruleset,
    create_strict_ruleset,
)

# Get pre-configured registry
registry = create_default_ptr_validation_registry()

# Use with different rulesets
default = create_default_ruleset()
strict = create_strict_ruleset()

result = registry.validate(my_timeline, ruleset=default, recursive=True)
```

## Best Practices

1. **Use the Rule Registry**: For production code, use the rule-based system with rulesets rather than ad-hoc validators.

2. **Tag Your Rules**: Organize rules with meaningful tags (critical, timing, metadata, etc.) for flexible ruleset composition.

3. **Create Reusable Rulesets**: Define named rulesets (strict, lenient, default) that can be reused across your application.

4. **Enable Recursive Validation**: For complex hierarchies like timelines, use `recursive=True` to validate all nested objects.

5. **Use Human-Readable IDs**: Enable `include_ids=True` (default) to get readable validation paths with object IDs.

6. **Export for Analysis**: Use `result.as_pandas()` to export validation results for analysis, filtering, or reporting.

7. **Customize Severity**: Use ruleset overrides to adjust severity levels for different validation contexts.

8. **Compose Validators**: Use combinators to build complex validation logic from simple predicates.

9. **Document Your Rules**: Provide clear descriptions when registering rules to help users understand what's being validated.

10. **Test Your Validators**: Write unit tests for custom validators to ensure they work correctly.

## Contributing

When adding new validators:

1. Create the validator function using `check()` or `check_field()`
2. Register it as a `ValidationRule` with unique ID and appropriate tags
3. Add tests for the validator
4. Document the rule in the module docstring
5. Consider which rulesets should include it by default

## License

See project LICENSE file.
