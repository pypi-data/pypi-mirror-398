"""
Production validators for PTR elements.

This module provides ready-to-use validation rules for common PTR element
validation patterns, using the new rule-based validation framework.

The module registers validation rules with unique IDs, tags, and metadata
that can be used in different rulesets.

Example:
    from ptr_editor.validation import RuleRegistry, RulesetConfig
    from ptr_editor.validation.ptr_validators import (
        create_default_registry,
        register_ptr_rules,
    )

    # Option 1: Get a pre-configured registry with default ruleset
    registry = create_default_registry()
    default_ruleset = RulesetConfig("default")
    default_ruleset.include_rules_with_tags(["ptr"])
    result = registry.validate(my_timeline, ruleset=default_ruleset)

    # Option 2: Register rules and create custom rulesets
    registry = RuleRegistry()
    register_ptr_rules(registry)

    strict = RulesetConfig("strict")
    strict.include_rules_with_tags(["critical"])

    lenient = RulesetConfig("lenient")
    lenient.include_rules_with_tags(["ptr"])
    lenient.exclude_rule("ptr.timing.min-duration")

    result = registry.validate(my_timeline, ruleset=strict, recursive=True)

    if not result.ok:
        for error in result.errors():
            print(error)
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

import pandas as pd

from ptr_editor.elements.blocks import ObsBlock, SlewBlock, TimedBlock
from ptr_editor.elements.timeline import Timeline

# Use relative imports to avoid circular import
from .result import Issue, Result, Severity
from .ruleset_registry import RuleRegistry, RulesetConfig, ValidationRule
from .validator import check, check_field

from loguru import logger as log

MINIMUM_BLOCK_DURATION_SECONDS = 120  # 2 minutes
MINIMUM_SLEW_DURATION_SECONDS = 120  # 2 minutes

# @runtime_checkable
# class _TimedItem:
#     """Placeholder for type hinting TimedItem.

#     pd.Timestamp also work as start or end values.
#     """

#     start: datetime
#     end: datetime


# =============================================================================
# TimedBlock Validators
# =============================================================================


def create_timed_block_validators() -> list:
    """
    Create validators for TimedBlock timing constraints.

    These validators check:
    - Both start and end times are defined
    - Start time is before end time
    - Duration is positive

    Returns:
        List of validators for TimedBlock
    """
    return [
        # Check that start time exists
        check_field(
            "start",
            lambda x: x is not None and isinstance(x, datetime),
            "Block must have a start time",
            name="start_exists",
        ),
        # Check that end time exists
        check_field(
            "end",
            lambda x: x is not None and isinstance(x, datetime),
            "Block must have an end time",
            name="end_exists",
        ),
        # Check time ordering
        check(
            lambda obj: (
                obj.start is not None and obj.end is not None and obj.start <= obj.end
            ),
            "Start time must be before end time",
            name="time_order",
        ),
        # Check positive duration
        check(
            lambda obj: (
                hasattr(obj, "start")
                and obj.start is not None
                and hasattr(obj, "end")
                and obj.end is not None
                and obj.end - obj.start > pd.Timedelta(0)
            ),
            "Block duration must be positive and non-zero",
            name="positive_duration",
        ),
        # Check minimum duration
        check(
            lambda obj: (
                hasattr(obj, "start")
                and obj.start is not None
                and hasattr(obj, "end")
                and obj.end is not None
                and obj.end - obj.start
                >= pd.Timedelta(seconds=MINIMUM_BLOCK_DURATION_SECONDS)
            ),
            "Block duration must be at least 2 minutes",
            name="minimum_duration",
        ),
    ]


# =============================================================================
# ObsBlock Validators
# =============================================================================


def create_obs_block_validators() -> list:
    """
    Create validators specific to ObsBlock elements.

    These validators check:
    - Attitude is defined (warning if missing)
    - Metadata exists (info if missing)
    - Slew time after this block is sufficient (if there's a next block)

    Returns:
        List of validators for ObsBlock
    """

    def _check_slew_after_block(obj: ObsBlock) -> bool:
        """Check that slew time after this block is at least minimum duration."""
        # If no parent timeline, we can't check slews
        if not hasattr(obj, "parent") or obj.parent is None:
            return True

        timeline: Timeline = obj.parent
        blocks = timeline.obs_blocks._segments_

        # Find this block's index in the timeline
        try:
            current_index = blocks.index(obj)
        except ValueError:
            # Block not in timeline (shouldn't happen, but be safe)
            return True

        # If this is the last block, no slew to check
        if current_index >= len(blocks) - 1:
            return True

        # Get the next block
        next_block = blocks[current_index + 1]

        # Calculate slew time
        slew_time = next_block.start - obj.end

        # Check if slew time is sufficient
        return slew_time >= pd.Timedelta(seconds=MINIMUM_SLEW_DURATION_SECONDS)

    return [
        # Check attitude exists (warning level)
        check_field(
            "attitude",
            lambda x: x is not None and x != "",
            "ObsBlock should have an attitude defined",
            severity=Issue.error,
            name="attitude_defined",
        ),
        # Check metadata exists (info level)
        check_field(
            "metadata",
            lambda x: x is not None,
            "ObsBlock should have metadata defined",
            severity=Issue.info,
            name="metadata_exists",
        ),
        # Check slew time after this block
        check(
            _check_slew_after_block,
            f"Slew time after block must be at least "
            f"{MINIMUM_SLEW_DURATION_SECONDS} seconds",
            name="minimum_slew_after_block",
        ),
    ]


# =============================================================================
# Timeline Validators
# =============================================================================


def create_timeline_validators() -> list:
    """
    Create validators for Timeline elements.

    These validators check:
    - Timeline has at least one block
    - Every other block (odd indices) is a SlewBlock

    Returns:
        List of validators for Timeline
    """

    def _check_length(obj: Timeline) -> bool:
        """Check that the timeline has at least one block."""
        return len(obj.obs_blocks) > 0

    def _check_slews_at_odd_indices(obj: Timeline) -> bool:
        """Check that every other block (odd indices: 1, 3, 5, ...) is a SlewBlock."""

        # Check odd indices (1, 3, 5, ...)
        return all(isinstance(obj[i], SlewBlock) for i in range(1, len(obj), 2))

    def _check_unique_ids(obj: Timeline) -> bool:
        """Check that all blocks in the timeline have unique IDs."""
        blocks = obj.obs_blocks
        ids = [block.id for block in blocks if hasattr(block, "id")]
        return len(ids) == len(set(ids))

    return [
        # Check timeline has at least one block
        check(
            _check_unique_ids,
            "All blocks in the timeline must have unique IDs",
            name="unique_block_ids",
        ),
        check(
            _check_length,
            "Timeline must contain at least one block",
            name="has_blocks",
        ),
        # Check that odd indices are SlewBlocks
        check(
            _check_slews_at_odd_indices,
            "Timeline is missing 1 or more SlewBlock(s) in between regular obs blocks. These will be added when saving automatically.",
            name="slews_at_odd_indices",
            severity=Issue.info,
        ),
    ]


# =============================================================================
# Rule Registration Functions
# =============================================================================


def register_timed_block_rules(registry: RuleRegistry) -> None:
    """
    Register validation rules for TimedBlock.

    Rules are registered with unique IDs and tags for flexible ruleset configuration.

    Args:
        registry: Rule registry to register rules with

    Example:
        >>> registry = (
        ...     RuleRegistry()
        ... )
        >>> register_timed_block_rules(
        ...     registry
        ... )
        >>> strict = (
        ...     RulesetConfig(
        ...         "strict"
        ...     )
        ... )
        >>> strict.include_rules_with_tags(
        ...     ["timing"]
        ... )
        >>> result = registry.validate(
        ...     my_block,
        ...     ruleset=strict,
        ... )
    """
    # Start time exists
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timing.start-exists",
            validator=check_field(
                "start",
                lambda x: x is not None and isinstance(x, datetime),
                "Block must have a start time",
                name="start_exists",
            ),
            description="Block must have a start time",
            default_severity=Severity.ERROR,
            tags=["timing", "critical", "ptr"],
            applicable_types=[TimedBlock],
        )
    )

    # End time exists
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timing.end-exists",
            validator=check_field(
                "end",
                lambda x: x is not None and isinstance(x, datetime),
                "Block must have an end time",
                name="end_exists",
            ),
            description="Block must have an end time",
            default_severity=Severity.ERROR,
            tags=["timing", "critical", "ptr"],
            applicable_types=[TimedBlock],
        )
    )

    # Time ordering
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timing.start-before-end",
            validator=check(
                lambda obj: (
                    obj.start is not None
                    and obj.end is not None
                    and obj.start <= obj.end
                ),
                "Start time must be before end time",
                name="time_order",
            ),
            description="Start time must be before or equal to end time",
            default_severity=Severity.ERROR,
            tags=["timing", "critical", "ptr"],
            applicable_types=[TimedBlock],
        )
    )

    # Positive duration
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timing.positive-duration",
            validator=check(
                lambda obj: (
                    hasattr(obj, "start")
                    and obj.start is not None
                    and hasattr(obj, "end")
                    and obj.end is not None
                    and obj.end - obj.start > pd.Timedelta(0)
                ),
                "Block duration must be positive and non-zero",
                name="positive_duration",
            ),
            description="Block duration must be positive and non-zero",
            default_severity=Severity.ERROR,
            tags=["timing", "duration", "ptr"],
            applicable_types=[TimedBlock],
        )
    )

    # Minimum duration
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timing.min-duration",
            validator=check(
                lambda obj: (
                    hasattr(obj, "start")
                    and obj.start is not None
                    and hasattr(obj, "end")
                    and obj.end is not None
                    and obj.end - obj.start
                    >= pd.Timedelta(seconds=MINIMUM_BLOCK_DURATION_SECONDS)
                ),
                "Block duration must be at least 2 minutes",
                name="minimum_duration",
            ),
            description=f"Block duration must be at least {MINIMUM_BLOCK_DURATION_SECONDS} seconds",
            default_severity=Severity.ERROR,
            tags=["timing", "duration", "ptr"],
            applicable_types=[TimedBlock],
        )
    )


def register_obs_block_rules(registry: RuleRegistry) -> None:
    """
    Register validation rules for ObsBlock.

    Args:
        registry: Rule registry to register rules with

    Example:
        >>> registry = (
        ...     RuleRegistry()
        ... )
        >>> register_obs_block_rules(
        ...     registry
        ... )
    """

    def _check_slew_after_block(obj: ObsBlock) -> bool | tuple[bool, str]:
        """Check that slew time after this block is at least minimum duration.

        Returns either bool or (bool, error_message) with specific timing details.
        """
        if not hasattr(obj, "parent") or obj.parent is None:
            return True

        timeline: Timeline = obj.parent  # type: ignore
        blocks = timeline.obs_blocks

        try:
            current_index = blocks.index(obj)
        except ValueError:
            log.debug(
                "ObsBlock not found in parent Timeline during slew time validation."
            )
            return True

        if current_index >= len(blocks) - 1:
            return True

        next_block = blocks[current_index + 1]
        slew_time = next_block.start - obj.end  # type: ignore
        min_slew = pd.Timedelta(seconds=MINIMUM_SLEW_DURATION_SECONDS)

        if slew_time >= min_slew:
            return True

        # Provide detailed error message with block IDs and actual times
        current_id = getattr(obj, "id", "current block")
        next_id = getattr(next_block, "id", "next block")
        error_msg = (
            f"Insufficient slew time between blocks '{current_id}' and '{next_id}': "
            f"{slew_time.total_seconds():.1f}s "
            f"(minimum required: {MINIMUM_SLEW_DURATION_SECONDS}s)"
        )
        return False, error_msg

    # Attitude defined
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.obs.attitude-defined",
            validator=check_field(
                "attitude",
                lambda x: x is not None and x != "",
                "ObsBlock should have an attitude defined",
                severity=Issue.error,
                name="attitude_defined",
            ),
            description="ObsBlock should have an attitude defined",
            default_severity=Severity.ERROR,
            tags=["obs", "metadata", "ptr"],
            applicable_types=[ObsBlock],
        )
    )

    # Metadata exists
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.obs.metadata-exists",
            validator=check_field(
                "metadata",
                lambda x: x is not None,
                "ObsBlock should have metadata defined",
                severity=Issue.info,
                name="metadata_exists",
            ),
            description="ObsBlock should have metadata defined",
            default_severity=Severity.INFO,
            tags=["obs", "metadata", "ptr"],
            applicable_types=[ObsBlock],
        )
    )

    # Minimum slew after block
    min_slew_msg = (
        f"Slew time after block must be at least "
        f"{MINIMUM_SLEW_DURATION_SECONDS} seconds"
    )
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.obs.min-slew-after",
            validator=check(
                _check_slew_after_block,
                min_slew_msg,
                name="minimum_slew_after_block",
            ),
            description=min_slew_msg,
            default_severity=Severity.ERROR,
            tags=["obs", "timing", "slew", "ptr"],
            applicable_types=[ObsBlock],
        )
    )


# Helper functions for timeline validation
def _check_timeline_length(obj: Timeline) -> bool:
    """Check that the timeline has at least one block."""
    return len(obj.obs_blocks) > 0


def _check_timeline_slews_at_odd_indices(obj: Timeline) -> bool:
    """Check that every other block (odd indices: 1, 3, 5, ...) is a SlewBlock."""
    return all(isinstance(obj[i], SlewBlock) for i in range(1, len(obj), 2))


def _check_timeline_unique_ids(obj: Timeline) -> bool | tuple[bool, str]:
    """Check that all ObsBlocks in the timeline have unique IDs.

    Returns either bool or (bool, error_message) with details about duplicates.
    """
    blocks = obj.obs_blocks
    # Only check ObsBlock instances for ID uniqueness
    ids = [
        block.id
        for block in blocks
        if isinstance(block, ObsBlock) and block.designer != "SOC"
    ]

    if len(ids) == len(set(ids)):
        return True

    # Count occurrences of each ID
    id_counts = Counter(ids)

    # Find IDs that appear more than once
    duplicates = {block_id: count for block_id, count in id_counts.items() if count > 1}

    # Create detailed error message
    if len(duplicates) == 1:
        block_id, count = next(iter(duplicates.items()))
        error_msg = f"Duplicate block ID found: '{block_id}' ({count})"
    else:
        dup_parts = [f"{block_id}' ({count})" for block_id, count in duplicates.items()]
        dup_list = "', '".join(dup_parts)
        error_msg = f"Duplicate block IDs found: '{dup_list}"

    return False, error_msg


def _check_timeline_sequential_timing(obj: Timeline) -> bool | tuple[bool, str]:
    """Check that blocks come one after another sequentially.

    Returns either bool or (bool, error_message) with details about offending blocks.
    """
    blocks = obj.obs_blocks
    min_blocks_for_sequence = 2

    if len(blocks) < min_blocks_for_sequence:
        return True

    for i in range(len(blocks) - 1):
        current_block = blocks[i]
        next_block = blocks[i + 1]

        if (
            not hasattr(current_block, "end")
            or current_block.end is None
            or not hasattr(next_block, "start")
            or next_block.start is None
        ):
            continue

        if next_block.start < current_block.end:
            current_id = getattr(current_block, "id", f"block_{i}")
            next_id = getattr(next_block, "id", f"block_{i + 1}")

            error_msg = (
                f"Block '{next_id}' starts ({next_block.start}) before "
                f"block '{current_id}' ends ({current_block.end}). "
                f"Blocks must be sequential."
            )
            return False, error_msg

    return True


def get_sequential_timing_issues(timeline: Timeline) -> list[str]:
    """Get detailed information about sequential timing issues.

    Returns a list of error messages identifying specific blocks with timing issues.

    Args:
        timeline: The timeline to check

    Returns:
        List of error messages, empty if no issues found
    """
    blocks = timeline.obs_blocks
    issues = []
    min_blocks_for_sequence = 2

    if len(blocks) < min_blocks_for_sequence:
        return issues

    for i in range(len(blocks) - 1):
        current_block = blocks[i]
        next_block = blocks[i + 1]

        if (
            not hasattr(current_block, "end")
            or current_block.end is None
            or not hasattr(next_block, "start")
            or next_block.start is None
        ):
            continue

        if next_block.start < current_block.end:
            current_id = getattr(current_block, "id", f"block_{i}")
            next_id = getattr(next_block, "id", f"block_{i + 1}")

            error_msg = (
                f"Block '{next_id}' starts ({next_block.start}) before "
                f"block '{current_id}' ends ({current_block.end}). "
                f"Blocks must be sequential."
            )
            issues.append(error_msg)

    return issues


def register_timeline_rules(registry: RuleRegistry) -> None:
    """
    Register validation rules for Timeline.

    Args:
        registry: Rule registry to register rules with

    Example:
        >>> registry = (
        ...     RuleRegistry()
        ... )
        >>> register_timeline_rules(
        ...     registry
        ... )
    """

    # Sequential timing rule
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timeline.sequential-timing",
            validator=check(
                _check_timeline_sequential_timing,
                "Blocks must come one after another without overlapping in time",
                name="sequential_timing",
            ),
            description="Blocks must be sequential - each block starts after previous ends",
            default_severity=Severity.ERROR,
            tags=["timeline", "timing", "critical", "ptr"],
            applicable_types=[Timeline],
        )
    )

    # Unique block IDs
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timeline.unique-block-ids",
            validator=check(
                _check_timeline_unique_ids,
                "All blocks in the timeline must have unique IDs",
                name="unique_block_ids",
            ),
            description="All blocks in the timeline must have unique IDs",
            default_severity=Severity.ERROR,
            tags=["timeline", "critical", "ptr"],
            applicable_types=[Timeline],
        )
    )

    # Timeline has blocks
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timeline.has-blocks",
            validator=check(
                _check_timeline_length,
                "Timeline must contain at least one block",
                name="has_blocks",
            ),
            description="Timeline must contain at least one block",
            default_severity=Severity.ERROR,
            tags=["timeline", "critical", "ptr"],
            applicable_types=[Timeline],
        )
    )

    # Slews at odd indices
    registry.register_rule(
        ValidationRule(
            rule_id="ptr.timeline.slews-at-odd-indices",
            validator=check(
                _check_timeline_slews_at_odd_indices,
                "Timeline is missing 1 or more SlewBlock(s) between obs blocks",
                name="slews_at_odd_indices",
                severity=Issue.info,
            ),
            description="SlewBlocks should be at odd indices between observation blocks",
            default_severity=Severity.INFO,
            tags=["timeline", "slew", "ptr"],
            applicable_types=[Timeline],
        )
    )


def register_ptr_rules(registry: RuleRegistry) -> RuleRegistry:
    """
    Register all PTR validation rules with a registry.

    This is the main function for setting up all PTR validation rules.

    Args:
        registry: Rule registry to register rules with

    Returns:
        The registry that was used (for chaining)

    Example:
        >>> from ptr_editor.validation import (
        ...     RuleRegistry,
        ...     RulesetConfig,
        ... )
        >>> from ptr_editor.validation.ptr_validators import (
        ...     register_ptr_rules,
        ... )
        >>>
        >>> registry = (
        ...     RuleRegistry()
        ... )
        >>> register_ptr_rules(
        ...     registry
        ... )
        >>>
        >>> # Create a strict ruleset
        >>> strict = (
        ...     RulesetConfig(
        ...         "strict"
        ...     )
        ... )
        >>> strict.include_rules_with_tags(
        ...     ["critical"]
        ... )
        >>>
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=strict,
        ...     recursive=True,
        ... )
    """
    register_timed_block_rules(registry)
    register_obs_block_rules(registry)
    register_timeline_rules(registry)

    return registry


def create_default_ptr_validation_registry() -> RuleRegistry:
    """
    Create a new rule registry with all PTR rules pre-registered.

    This is a convenience factory function that creates a registry
    with all PTR validation rules.

    Returns:
        A new RuleRegistry instance with all PTR rules registered

    Example:
        >>> from ptr_editor.validation import (
        ...     RulesetConfig,
        ... )
        >>> from ptr_editor.validation.ptr_validators import (
        ...     create_default_ptr_validation_registry,
        ... )
        >>>
        >>> registry = create_default_ptr_validation_registry()
        >>>
        >>> # Create rulesets
        >>> default = (
        ...     RulesetConfig(
        ...         "default"
        ...     )
        ... )
        >>> default.include_rules_with_tags(
        ...     ["ptr"]
        ... )
        >>>
        >>> strict = (
        ...     RulesetConfig(
        ...         "strict"
        ...     )
        ... )
        >>> strict.include_rules_with_tags(
        ...     ["critical"]
        ... )
        >>>
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=default,
        ...     recursive=True,
        ... )
    """
    registry = RuleRegistry()
    register_ptr_rules(registry)
    return registry


def create_default_ruleset() -> RulesetConfig:
    """
    Create a default ruleset that includes all PTR rules.

    Returns:
        A RulesetConfig configured with all PTR rules

    Example:
        >>> from ptr_editor.services import (
        ...     get_validation_registry,
        ... )
        >>> from ptr_editor.validation.ptr_validators import (
        ...     create_default_ruleset,
        ... )
        >>>
        >>> registry = get_validation_registry()
        >>> ruleset = create_default_ruleset()
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=ruleset,
        ...     recursive=True,
        ... )
    """
    ruleset = RulesetConfig("default")
    ruleset.include_rules_with_tags(["ptr"])
    return ruleset


def create_strict_ruleset() -> RulesetConfig:
    """
    Create a strict ruleset that only includes critical rules.

    Returns:
        A RulesetConfig configured with only critical rules

    Example:
        >>> from ptr_editor.services import (
        ...     get_validation_registry,
        ... )
        >>> from ptr_editor.validation.ptr_validators import (
        ...     create_strict_ruleset,
        ... )
        >>>
        >>> registry = get_validation_registry()
        >>> ruleset = create_strict_ruleset()
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=ruleset,
        ...     recursive=True,
        ... )
    """
    ruleset = RulesetConfig("strict")
    ruleset.include_rules_with_tags(["critical"])
    return ruleset


def get_ruleset(name: str | list[str]) -> RulesetConfig:
    """
    Create a ruleset by including all rules with specific tag(s).

    This is a convenience function that creates a RulesetConfig and includes
    all rules that have the specified tag(s).

    Args:
        name: The tag name(s) to filter rules by. Can be a single string or
            a list/iterable of strings. Common tags include:
            - "ptr": All PTR validation rules
            - "critical": Only critical/essential rules
            - "timing": Timing-related rules
            - "obs": ObsBlock-specific rules
            - "timeline": Timeline-specific rules
            - "slew": Slew-related rules
            - "metadata": Metadata validation rules
            - "duration": Duration-related rules

    Returns:
        A RulesetConfig configured with all rules matching the specified tag(s)

    Example:
        >>> from ptr_editor.services import (
        ...     get_validation_registry,
        ... )
        >>> from ptr_editor.validation.ptr_validators import (
        ...     get_ruleset,
        ... )
        >>>
        >>> registry = get_validation_registry()
        >>>
        >>> # Get all PTR rules
        >>> ptr_ruleset = (
        ...     get_ruleset(
        ...         "ptr"
        ...     )
        ... )
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=ptr_ruleset,
        ... )
        >>>
        >>> # Get only critical rules
        >>> critical_ruleset = (
        ...     get_ruleset(
        ...         "critical"
        ...     )
        ... )
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=critical_ruleset,
        ... )
        >>>
        >>> # Get only timing-related rules
        >>> timing_ruleset = (
        ...     get_ruleset(
        ...         "timing"
        ...     )
        ... )
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=timing_ruleset,
        ... )
        >>>
        >>> # Get rules with multiple tags
        >>> custom_ruleset = get_ruleset(
        ...     [
        ...         "timing",
        ...         "critical",
        ...     ]
        ... )
        >>> result = registry.validate(
        ...     my_timeline,
        ...     ruleset=custom_ruleset,
        ... )
    """
    # Convert single string to list for consistent handling
    if isinstance(name, str):
        tags = [name]
        ruleset_name = name
    else:
        tags = list(name)
        ruleset_name = "_".join(tags)

    ruleset = RulesetConfig(ruleset_name)
    ruleset.include_rules_with_tags(tags)
    return ruleset


# =============================================================================
# Convenience Functions
# =============================================================================


def validate_timed_block(block: TimedBlock, *, recursive: bool = False) -> Result:
    """
    Validate a TimedBlock using PTR validators.

    This is a convenience function that creates a temporary registry
    with all PTR rules and validates the block using a default ruleset.

    Args:
        block: The TimedBlock to validate
        recursive: Whether to validate nested objects

    Returns:
        ValidationResult with all issues found

    Example:
        >>> from ptr_editor.validation.ptr_validators import (
        ...     validate_timed_block,
        ... )
        >>> result = validate_timed_block(
        ...     my_block
        ... )
        >>> if not result.ok:
        ...     print(result)
    """
    registry = create_default_ptr_validation_registry()
    ruleset = RulesetConfig("default")
    ruleset.include_rules_with_tags(["ptr"])
    return registry.validate(block, ruleset=ruleset, recursive=recursive)


def validate_obs_block(block: ObsBlock, *, recursive: bool = False) -> Result:
    """
    Validate an ObsBlock using PTR validators.

    This is a convenience function that creates a temporary registry
    with all PTR rules and validates the block using a default ruleset.

    Args:
        block: The ObsBlock to validate
        recursive: Whether to validate nested objects

    Returns:
        ValidationResult with all issues found

    Example:
        >>> from ptr_editor.validation.ptr_validators import (
        ...     validate_obs_block,
        ... )
        >>> result = validate_obs_block(
        ...     my_obs_block
        ... )
        >>> if not result.ok:
        ...     for error in result.errors():
        ...         print(error)
    """
    registry = create_default_ptr_validation_registry()
    ruleset = RulesetConfig("default")
    ruleset.include_rules_with_tags(["ptr"])
    return registry.validate(block, ruleset=ruleset, recursive=recursive)
