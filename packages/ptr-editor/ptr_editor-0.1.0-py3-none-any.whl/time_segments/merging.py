"""
Declarative Segment Merging with Conflict Resolution.

A configurable approach to merging time segments with conflict detection and resolution.

Design Principles
-----------------
- **Declarative**: Define merge behavior through strategy configuration
- **Transparent**: Each operation records what was done and why via Action classes
- **Conflict Tracking**: Unresolved conflicts are captured for reporting
- **Extensible**: Easy to add new resolution strategies
- **Progressive**: Try multiple strategies in sequence until conflict is resolved
- **Action-Based**: All operations are tracked via proper Action objects (ADD, DELETE, UPDATE, REPLACE)

Action Types
------------
The merger uses a comprehensive Action class hierarchy to track all operations:

- **AddAction**: Adding a new segment
- **DeleteAction**: Removing an existing segment
- **UpdateAction**: Replacing a segment with an updated version (from a match)
- **ReplaceAction**: Replacing segment(s) without a match (time overlap)
- **SkipAction**: Skipping an operation
- **MergeAction**: Merging multiple segments into one

Each Action tracks:
- What segments were affected
- Why the action was taken
- Human-readable description

Basic Usage
-----------
```python
# Single strategy
merger = SegmentMerger(
    strategy="merge"
)
result = (
    merger.insert(
        collection,
        new_segment,
    )
)

# Multiple strategies (try in order until one succeeds)
merger = (
    SegmentMerger(
        strategies=[
            "skip",
            "merge",
            "force",
        ]
    )
)
result = (
    merger.insert(
        collection,
        new_segment,
    )
)

# Check results
if result.conflicts:
    print(
        f"Unresolved conflicts: {len(result.conflicts)}"
    )
for (
    action
) in result.actions:
    print(
        f"{action}"
    )  # Uses Action.__str__ for description
```

DiffResult-Based Merging
-------------------------
Apply changes from a DiffResult (from TimelineDiffer) to a collection:

```python
from ptr_editor.diffing.matcher import (
    BlockMatcher,
    IDMatcher,
    TimingMatcher,
)
from ptr_editor.diffing.timeline_differ_simple import (
    TimelineDiffer,
    make_timeline_differ,
)

# Match blocks
matcher = (
    BlockMatcher()
)
matcher.add_rule(
    IDMatcher("id")
    & TimingMatcher(
        60
    ),
    priority=0,
)
match_result = matcher.match(
    current_blocks,
    incoming_blocks,
)

# Get diff
differ = make_timeline_differ(
    include_temporal=True
)
diff_result = (
    differ.diff(
        match_result
    )
)

# Apply diff to collection
merger = DiffBasedMerger()
merge_result = merger.apply(
    current_collection,
    diff_result,
)

# Check what happened
print(
    merge_result.summary()
)
for action in merge_result.actions:
    if isinstance(
        action,
        UpdateAction,
    ):
        print(
            f"Updated {action.old_segment.id}: {action.changes}"
        )
    elif isinstance(
        action,
        AddAction,
    ):
        print(
            f"Added {action.segment.id}"
        )
    elif isinstance(
        action,
        DeleteAction,
    ):
        print(
            f"Deleted {action.segment.id}"
        )
```

The DiffBasedMerger systematically:
1. Deletes segments removed in incoming timeline (DeleteAction)
2. Updates changed segments (UpdateAction with change details)
3. Adds new segments (AddAction)

Available Strategies
--------------------
- ErrorStrategy: Raise error on conflict (strict)
- SkipStrategy: Skip insertion if conflict exists
- ReplaceStrategy: Remove conflicting segments, insert new one
- SafeReplaceStrategy: Replace only if attribute values match (safe update)
- MergeStrategy: Merge all overlapping segments into one
- ForceStrategy: Insert regardless of conflicts

Multi-Strategy Pattern
----------------------
When multiple strategies are provided, the merger tries them in sequence:

```python
# Progressive: Try skip first, then merge, finally force
merger = (
    SegmentMerger(
        strategies=[
            "skip",
            "merge",
            "force",
        ]
    )
)
result = (
    merger.insert(
        collection,
        segment,
    )
)

# Result tells you which strategy was used
print(
    f"Resolved using: {result.strategy_used}"
)

# Or use convenience factory
merger = make_progressive_merger()  # skip -> merge -> force

# Conservative: Try skip first, then error
merger = make_conservative_merger()  # skip -> error
try:
    result = merger.insert(
        collection,
        segment,
    )
except ValueError:
    print(
        "Could not insert without creating conflicts"
    )
```

This is similar to BlockMatcher's prioritized rules - each strategy is
attempted until one successfully resolves the conflict.

Real-World Example
------------------
```python
# Batch insertion with progressive strategy
merger = make_progressive_merger()

for (
    new_segment
) in new_segments:
    result = merger.insert(
        existing_collection,
        new_segment,
    )

    if (
        result.strategy_used
        == "skip"
    ):
        print(
            f"Skipped {new_segment.id} - already covered"
        )
    elif (
        result.strategy_used
        == "merge"
    ):
        print(
            f"Merged {new_segment.id} with existing segments"
        )
    elif (
        result.strategy_used
        == "force"
    ):
        print(
            f"Force-inserted {new_segment.id} - created overlap"
        )

    # Check for any unresolved conflicts
    for conflict in result.conflicts:
        print(
            f"Warning: {conflict}"
        )
```

Custom Strategies
-----------------
Implement the MergeStrategy protocol to create custom conflict resolution:

```python
@define
class CustomStrategy:
    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[
            TimeSegmentMixin
        ],
        merger: SegmentMerger
        | None = None,
    ) -> MergeResolution:
        # Custom logic here
        ...

    def name(
        self,
    ) -> str:
        return (
            "custom"
        )
```

Registering Custom Strategies
------------------------------
Users can register custom strategies globally without modifying the code:

```python
from attrs import (
    define,
)
from time_segments.merging import (
    register_strategy,
    MergeStrategy,
    MergeResolution,
    MergeAction,
    SegmentMerger,
)


@define
class ConditionalMergeStrategy:
    '''Merge only if overlap exceeds threshold.'''

    threshold: float = 0.5  # 50% overlap required

    def resolve(
        self,
        segment,
        overlapping,
        merger=None,
    ):
        # Calculate overlap percentage
        # If > threshold, merge; otherwise skip
        for overlap_seg in overlapping:
            overlap_pct = calculate_overlap_percentage(
                segment,
                overlap_seg,
            )
            if (
                overlap_pct
                >= self.threshold
            ):
                # Merge logic
                merged = segment.copy()
                merged.start = min(
                    segment.start,
                    overlap_seg.start,
                )
                merged.end = max(
                    segment.end,
                    overlap_seg.end,
                )
                return MergeResolution(
                    success=True,
                    actions=[
                        MergeAction(
                            ...
                        )
                    ],
                    segments_to_remove=[
                        overlap_seg
                    ],
                    segments_to_add=[
                        merged
                    ],
                )

        # Skip if threshold not met
        return MergeResolution(
            success=True,
            actions=[
                ...
            ],
        )

    def name(self):
        return "conditional_merge"


# Register once at application startup
register_strategy(
    "conditional_merge",
    ConditionalMergeStrategy,
)

# Use anywhere in your application
merger = SegmentMerger(
    strategy="conditional_merge"
)
merger = SegmentMerger(
    strategies=[
        "conditional_merge",
        "merge",
        "force",
    ]
)
result = (
    merger.insert(
        collection,
        segment,
    )
)

# List all available strategies
from time_segments.merging import (
    list_strategies,
)

print(
    f"Available: {list_strategies()}"
)
# ['error', 'skip', 'replace', 'merge', 'force', 'conditional_merge']
```

Customizing SafeReplaceStrategy
--------------------------------
The SafeReplaceStrategy can be customized to check different attributes:

```python
from time_segments.merging import (
    make_safe_replace_strategy,
    register_safe_replace_variant,
    SegmentMerger,
)

# Method 1: Create instance directly
strategy = make_safe_replace_strategy(
    attr_name="designer"
)
merger = SegmentMerger(
    strategy=strategy
)
result = (
    merger.insert(
        collection,
        segment,
    )
)

# Method 2: Use in strategy list
merger = SegmentMerger(
    strategies=[
        make_safe_replace_strategy(
            attr_name="name"
        ),
        "merge",
        "force",
    ]
)

# Method 3: Register a named variant for reuse
register_safe_replace_variant(
    "safe_replace_by_designer",
    attr_name="designer",
)

# Now use it by name anywhere
merger = make_merger(
    "safe_replace_by_designer"
)
merger = make_merger(
    [
        "safe_replace_by_designer",
        "merge",
        "force",
    ]
)

# Control mismatch behavior
strategy = make_safe_replace_strategy(
    attr_name="id",
    skip_if_mismatch=False,  # Raise error instead of skip
)
```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from attrs import define, field

from loguru import logger as log

if TYPE_CHECKING:
    from .segment_mixin import TimeSegmentMixin


# ============================================================================
# 1. ACTION CLASSES - Base actions and their combinations
# ============================================================================


@define
class Action:
    """
    Base class for merge actions.

    All actions track what operation was performed and provide
    human-readable descriptions.
    """

    description: str = field(default="")

    def action_type(self) -> str:
        """Return the type of this action."""
        return self.__class__.__name__

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.action_type()}: {self.description}"


@define
class AddAction(Action):
    """
    Action representing addition of a new segment.

    Attributes:
        segment: The segment being added
        reason: Why it was added (e.g., "new in incoming timeline")
    """

    segment: TimeSegmentMixin = field(default=None)
    reason: str = field(default="")

    def __attrs_post_init__(self):
        """Set default description if not provided."""
        if not self.description:
            seg_id = _get_segment_id(self.segment)
            object.__setattr__(
                self,
                "description",
                f"Added segment '{seg_id}'{f': {self.reason}' if self.reason else ''}",
            )


@define
class DeleteAction(Action):
    """
    Action representing deletion of an existing segment.

    Attributes:
        segment: The segment being deleted
        reason: Why it was deleted (e.g., "removed in incoming timeline")
    """

    segment: TimeSegmentMixin = field(default=None)
    reason: str = field(default="")

    def __attrs_post_init__(self):
        """Set default description if not provided."""
        if not self.description:
            seg_id = _get_segment_id(self.segment)
            object.__setattr__(
                self,
                "description",
                f"Deleted segment '{seg_id}'{f': {self.reason}' if self.reason else ''}",
            )


@define
class UpdateAction(Action):
    """
    Action representing update of an existing segment.

    This is a composite of DELETE + ADD where both segments were part
    of a match (same logical entity, different content).

    Attributes:
        old_segment: The original segment being replaced
        new_segment: The new segment replacing it
        match: Optional Match object that paired them
        changes: Optional list of detected changes
    """

    old_segment: TimeSegmentMixin = field(default=None)
    new_segment: TimeSegmentMixin = field(default=None)
    match: object = field(default=None)  # Match object from matcher
    changes: list[str] = field(factory=list)

    def __attrs_post_init__(self):
        """Set default description if not provided."""
        if not self.description:
            seg_id = _get_segment_id(self.old_segment)
            changes_str = f" ({', '.join(self.changes)})" if self.changes else ""
            object.__setattr__(
                self,
                "description",
                f"Updated segment '{seg_id}'{changes_str}",
            )


@define
class ReplaceAction(Action):
    """
    Action representing replacement without a match.

    This is a composite of DELETE + ADD where segments were NOT matched
    but the new one overrides the same time period.

    Attributes:
        old_segments: The segments being removed (may overlap same time)
        new_segment: The new segment taking their place
        reason: Why replacement occurred (e.g., "time overlap")
    """

    old_segments: list[TimeSegmentMixin] = field(factory=list)
    new_segment: TimeSegmentMixin = field(default=None)
    reason: str = field(default="")

    def __attrs_post_init__(self):
        """Set default description if not provided."""
        if not self.description:
            new_id = _get_segment_id(self.new_segment)
            old_ids = _get_segment_ids(self.old_segments)
            object.__setattr__(
                self,
                "description",
                f"Replaced {len(self.old_segments)} segment(s) {old_ids} "
                f"with '{new_id}'{f': {self.reason}' if self.reason else ''}",
            )


@define
class SkipAction(Action):
    """
    Action representing skipping an operation.

    Attributes:
        segment: The segment that was skipped
        reason: Why it was skipped
    """

    segment: TimeSegmentMixin = field(default=None)
    reason: str = field(default="")

    def __attrs_post_init__(self):
        """Set default description if not provided."""
        if not self.description:
            seg_id = _get_segment_id(self.segment)
            object.__setattr__(
                self,
                "description",
                f"Skipped segment '{seg_id}'{f': {self.reason}' if self.reason else ''}",
            )


@define
class MergeAction(Action):
    """
    Action representing merging multiple segments into one.

    Attributes:
        merged_segments: The segments being merged
        result_segment: The resulting merged segment
    """

    merged_segments: list[TimeSegmentMixin] = field(factory=list)
    result_segment: TimeSegmentMixin = field(default=None)

    def __attrs_post_init__(self):
        """Set default description if not provided."""
        if not self.description:
            merged_ids = _get_segment_ids(self.merged_segments)
            result_id = _get_segment_id(self.result_segment)
            object.__setattr__(
                self,
                "description",
                f"Merged {len(self.merged_segments)} segment(s) {merged_ids} "
                f"into '{result_id}'",
            )


# ============================================================================
# 2. HELPER FUNCTIONS
# ============================================================================


def _get_segment_id(segment: TimeSegmentMixin) -> str:
    """Extract segment ID or return 'unknown'."""
    return str(segment.id)  # it must exists


def _get_segment_ids(segments: Sequence[TimeSegmentMixin]) -> list[str]:
    """Extract IDs from a sequence of segments."""
    return [_get_segment_id(s) for s in segments]


def _to_mutable_list(collection: Sequence[TimeSegmentMixin]) -> list[TimeSegmentMixin]:
    """Convert a sequence to a mutable list if needed."""
    return list(collection) if not isinstance(collection, list) else collection


# ============================================================================
# 3. RESULT CLASSES - Conflict tracking and merge results
# ============================================================================


@define
class MergeConflict:
    """Record of an unresolved conflict during merge operation."""

    segment: TimeSegmentMixin
    overlapping: list[TimeSegmentMixin]
    reason: str
    strategy_attempted: str

    def __str__(self) -> str:
        """Human-readable conflict description."""
        seg_id = _get_segment_id(self.segment)
        overlap_ids = _get_segment_ids(self.overlapping)
        return (
            f"Conflict: Segment '{seg_id}' overlaps with {len(self.overlapping)} "
            f"segment(s) {overlap_ids}. Reason: {self.reason}"
        )


@define
class MergeResolution:
    """
    Result of attempting to resolve a conflict.

    Attributes:
        success: Whether resolution was successful
        actions: List of Action objects describing what was done
        segments_to_remove: Segments to be removed from collection
        segments_to_add: Segments to be added to collection
        conflict: Optional MergeConflict if resolution failed
        error_message: Optional error message if resolution failed
    """

    success: bool
    actions: list[Action] = field(factory=list)
    segments_to_remove: list[TimeSegmentMixin] = field(factory=list)
    segments_to_add: list[TimeSegmentMixin] = field(factory=list)
    conflict: MergeConflict | None = None
    error_message: str | None = None


@define
class MergeResult:
    """
    Complete result of a merge operation.

    Attributes:
        success: Whether the operation succeeded
        actions: List of Action objects describing all operations performed
        conflicts: List of unresolved conflicts
        segments_added: Segments added to collection
        segments_removed: Segments removed from collection
        strategy_used: Name of strategy used
    """

    success: bool
    actions: list[Action] = field(factory=list)
    conflicts: list[MergeConflict] = field(factory=list)
    segments_added: list[TimeSegmentMixin] = field(factory=list)
    segments_removed: list[TimeSegmentMixin] = field(factory=list)
    strategy_used: str = ""

    @property
    def conflicting_blocks(self) -> Sequence[TimeSegmentMixin]:
        """Get list of segments involved in conflicts."""
        return [conflict.segment for conflict in self.conflicts]

    @property
    def has_conflicts(self) -> bool:
        """Check if there are unresolved conflicts."""
        return len(self.conflicts) > 0

    @property
    def action_count(self) -> int:
        """Number of actions taken."""
        return len(self.actions)

    def summary(self) -> str:
        """Human-readable summary of the merge operation."""
        lines = [
            "Merge Operation Summary",
            "=" * 60,
            f"Strategy: {self.strategy_used}",
            f"Success: {self.success}",
            f"Actions taken: {self.action_count}",
            f"Segments added: {len(self.segments_added)}",
            f"Segments removed: {len(self.segments_removed)}",
            f"Unresolved conflicts: {len(self.conflicts)}",
        ]

        if self.actions:
            lines.append("\nActions:")
            lines.extend(f"  - {action.description}" for action in self.actions)

        if self.conflicts:
            lines.append("\nConflicts:")
            lines.extend(f"  - {conflict}" for conflict in self.conflicts)

        return "\n".join(lines)

    def report(self):
        """Print detailed report to stdout."""
        import sys

        sys.stdout.write(self.summary() + "\n")

    def _repr_html_(self):
        """
        HTML representation for Jupyter notebooks.

        This method is automatically called by Jupyter/IPython to display
        rich HTML output when the object is the last expression in a cell.

        Returns:
            HTML string with summary statistics and action information
        """
        # Status indicator
        status_emoji = "✅" if self.success else "❌"
        status_text = "Success" if self.success else "Failed"
        status_color = (
            "var(--jp-success-color1, #28a745)"
            if self.success
            else "var(--jp-error-color1, #dc3545)"
        )

        # Build compact HTML display
        html = """
    <div style="border: 1px solid var(--jp-border-color2, #e0e0e0);
                border-radius: 4px;
                padding: 12px;
                margin: 8px 0;
                font-size: 0.9em;">
        <div style="margin-bottom: 10px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
            <strong style="font-size: 1.1em;">🔄 Merge Result</strong>
        </div>
"""

        html += f"""
        <div style="margin-bottom: 12px;">
            <span style="margin-right: 16px; white-space: nowrap;">
                <span style="margin-right: 4px;">{status_emoji}</span>
                <span style="color: {status_color};
                             font-weight: 500;">{status_text}</span>
            </span>
        </div>
"""

        # Summary metrics
        html += """
        <div style="margin-bottom: 12px;">
"""

        metrics = [
            (f"{len(self.segments_added)} added", "➕"),
            (f"{len(self.segments_removed)} removed", "➖"),
            (f"{self.action_count} actions", "📝"),
        ]

        if self.has_conflicts:
            metrics.append((f"{len(self.conflicts)} conflicts", "⚠️"))

        for text, symbol in metrics:
            html += f"""
            <span style="margin-right: 16px; white-space: nowrap;">
                <span style="margin-right: 4px;">{symbol}</span>
                <span>{text}</span>
            </span>
"""

        html += """
        </div>
"""

        # Strategy used
        html += f"""
        <div style="margin-bottom: 12px; font-size: 0.85em; opacity: 0.8;">
            Strategy: <span style="font-family: monospace;
                                   background: var(--jp-layout-color2, #f7f7f7);
                                   color: var(--jp-content-font-color1, inherit);
                                   padding: 2px 6px;
                                   border-radius: 3px;">{self.strategy_used}</span>
        </div>
"""

        # Actions taken
        if self.actions:
            html += f"""
        <details style="margin-bottom: 12px;" open>
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                📋 Actions Taken ({len(self.actions)})
            </summary>
            <div style="margin-left: 16px; font-size: 0.85em;">
"""
            for _i, action in enumerate(self.actions, 1):  # Show all actions
                action_icon = {
                    "insert": "➕",
                    "remove": "➖",
                    "merge": "🔗",
                    "skip": "⏭️",
                    "failed": "❌",
                    "strategy_selection": "🔍",
                }.get(action.action_type, "•")

                html += f"""
                <div style="margin-bottom: 4px;">
                    <span style="margin-right: 4px;">{action_icon}</span>
                    <span>{action.description}</span>
                </div>
"""

            html += """
            </div>
        </details>
"""

        # Segments added
        if self.segments_added:
            html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                ➕ Segments Added ({len(self.segments_added)})
            </summary>
            <div style="margin-left: 16px; font-size: 0.85em;">
"""
            for seg in self.segments_added:  # Show all segments
                seg_id = _get_segment_id(seg)
                seg_start = getattr(seg, "start", "N/A")
                seg_end = getattr(seg, "end", "N/A")
                html += f"""
                <div style="margin-bottom: 4px;">
                    <strong>{seg_id}</strong>: {seg_start} → {seg_end}
                </div>
"""

            html += """
            </div>
        </details>
"""

        # Segments removed
        if self.segments_removed:
            html += f"""
        <details style="margin-bottom: 12px;">
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px;">
                ➖ Segments Removed ({len(self.segments_removed)})
            </summary>
            <div style="margin-left: 16px; font-size: 0.85em;">
"""
            for seg in self.segments_removed:  # Show all segments
                seg_id = _get_segment_id(seg)
                seg_start = getattr(seg, "start", "N/A")
                seg_end = getattr(seg, "end", "N/A")
                html += f"""
                <div style="margin-bottom: 4px;">
                    <strong>{seg_id}</strong>: {seg_start} → {seg_end}
                </div>
"""

            html += """
            </div>
        </details>
"""

        # Conflicts - use Jupyter's error colors with proper fallbacks
        if self.conflicts:
            html += f"""
        <details style="margin-bottom: 12px;" open>
            <summary style="cursor: pointer; font-weight: 500; margin-bottom: 6px; color: var(--jp-error-color1, #dc3545);">
                ⚠️ Unresolved Conflicts ({len(self.conflicts)})
            </summary>
            <div style="margin-left: 16px; font-size: 0.85em;">
"""
            for conflict in self.conflicts:  # Show all conflicts
                seg_id = _get_segment_id(conflict.segment)
                html += f"""
                <div style="margin-bottom: 8px; padding: 8px; background: var(--jp-layout-color2, var(--jp-cell-editor-background, #f7f7f7)); color: var(--jp-content-font-color1, inherit); border-left: 3px solid var(--jp-error-color1, #dc3545); border-radius: 3px;">
                    <div style="font-weight: 500; margin-bottom: 4px;">
                        Segment: {seg_id}
                    </div>
                    <div style="opacity: 0.8;">{conflict.reason}</div>
                    <div style="margin-top: 4px; font-size: 0.9em; opacity: 0.7;">
                        Strategy attempted: {conflict.strategy_attempted}
                    </div>
                </div>
"""

            html += """
            </div>
        </details>
"""

        # Footer with usage hint
        html += """
        <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--jp-border-color2, #e0e0e0); font-size: 0.85em; opacity: 0.7;">
            <span>Use <code style="padding: 1px 4px; border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 2px; font-size: 0.9em;">.summary()</code> for text summary or <code style="padding: 1px 4px; border: 1px solid var(--jp-border-color2, #e0e0e0); border-radius: 2px; font-size: 0.9em;">.report()</code> for detailed report</span>
        </div>
    </div>
"""

        return html

    def __str__(self) -> str:
        """String representation."""
        status = "success" if self.success else "failed"
        return (
            f"MergeResult({status}, {self.action_count} actions, "
            f"{len(self.conflicts)} conflicts)"
        )


# ============================================================================
# 2. STRATEGY PROTOCOL AND IMPLEMENTATIONS
# ============================================================================


class MergeStrategy(Protocol):
    """Protocol for merge conflict resolution strategies."""

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger,
    ) -> MergeResolution:
        """
        Resolve conflict between segment and overlapping segments.

        Args:
            segment: The segment being inserted
            overlapping: List of segments that overlap with it
            merger: The merger instance (for context/utilities)

        Returns:
            MergeResolution with the result of conflict resolution
        """
        ...

    def name(self) -> str:
        """Return human-readable name for this strategy."""
        ...


@define
class ErrorStrategy:
    """Raise error when conflicts are detected."""

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger | None = None,
    ) -> MergeResolution:
        """Raise error on conflict."""
        del merger  # Unused but required by protocol
        seg_id = _get_segment_id(segment)
        overlap_ids = _get_segment_ids(overlapping)

        error_msg = (
            f"Segment '{seg_id}' overlaps with {len(overlapping)} existing "
            f"segment(s): {overlap_ids}. Use a different conflict resolution "
            f"strategy to handle overlaps."
        )

        conflict = MergeConflict(
            segment=segment,
            overlapping=overlapping,
            reason="Overlap detected with error strategy",
            strategy_attempted=self.name(),
        )

        return MergeResolution(
            success=False,
            conflict=conflict,
            error_message=error_msg,
        )

    def name(self) -> str:
        return "error"


@define
class SkipStrategy:
    """Skip insertion when conflicts are detected."""

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger | None = None,
    ) -> MergeResolution:
        """Skip insertion on conflict."""
        del merger, overlapping  # Unused but required by protocol

        action = SkipAction(
            segment=segment,
            reason="overlap detected",
        )

        return MergeResolution(
            success=True,
            actions=[action],
        )

    def name(self) -> str:
        return "skip"


@define
class ReplaceStrategy:
    """Replace all conflicting segments with the new one."""

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger | None = None,
    ) -> MergeResolution:
        """Remove overlapping segments and insert new one."""
        del merger  # Unused but required by protocol

        replace_action = ReplaceAction(
            old_segments=list(overlapping),
            new_segment=segment,
            reason="time overlap replacement",
        )

        return MergeResolution(
            success=True,
            actions=[replace_action],
            segments_to_remove=list(overlapping),
            segments_to_add=[segment],
        )

    def name(self) -> str:
        return "replace"


@define
class SafeReplaceStrategy:
    """
    Replace overlapping segments only if they have matching attribute values.

    This strategy checks a specified attribute (default: 'designer') on the new
    segment and all overlapping segments. It only performs the replacement
    if all overlapping segments have the same value for that attribute.

    This is useful when you want to update segments with the same identity
    but avoid accidentally replacing unrelated segments that happen to overlap.

    Attributes:
        attr_name: Name of attribute to check for equality (default: "id")
        skip_if_mismatch: If True, skip insertion on mismatch; if False, fail
                         with error (default: True)
    """

    attr_name: str = "designer"
    skip_if_mismatch: bool = True

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger | None = None,
    ) -> MergeResolution:
        """Replace overlapping segments only if attribute values match."""
        del merger  # Unused but required by protocol
        seg_value = getattr(segment, self.attr_name, None)
        seg_id = _get_segment_id(segment)

        # Check if all overlapping segments have the same attribute value
        mismatches = []
        for overlap_seg in overlapping:
            overlap_value = getattr(overlap_seg, self.attr_name, None)
            if overlap_value != seg_value:
                overlap_id = _get_segment_id(overlap_seg)
                mismatches.append((overlap_id, overlap_value))

        # If there are mismatches, handle based on skip_if_mismatch setting
        if mismatches:
            mismatch_desc = ", ".join(f"{oid}({val})" for oid, val in mismatches)
            reason = (
                f"Segment '{seg_id}' has {self.attr_name}={seg_value}, but "
                f"overlapping segment(s) have different values: {mismatch_desc}"
            )

            if self.skip_if_mismatch:
                # Skip insertion
                action = SkipAction(
                    segment=segment,
                    reason=reason,
                )
                return MergeResolution(
                    success=True,
                    actions=[action],
                )

            # Fail with conflict
            conflict = MergeConflict(
                segment=segment,
                overlapping=overlapping,
                reason=reason,
                strategy_attempted=self.name(),
            )
            return MergeResolution(
                success=False,
                conflict=conflict,
                error_message=reason,
            )

        # All overlapping segments have matching attribute values - safe to replace
        update_action = ReplaceAction(
            old_segments=list(overlapping),
            new_segment=segment,
            reason=f"safe replacement with matching {self.attr_name}={seg_value}",
        )

        return MergeResolution(
            success=True,
            actions=[update_action],
            segments_to_remove=list(overlapping),
            segments_to_add=[segment],
        )

    def name(self) -> str:
        return "safe_replace"


@define
class MergeSegmentsStrategy:
    """Merge the new segment with all overlapping ones into a single segment.
    Not really implemented in anyway, just a placeholder.
    """

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger | None = None,
    ) -> MergeResolution:
        """Merge all overlapping segments into one."""
        del merger  # Unused but required by protocol

        # Create merged segment
        merged = segment.copy()

        # Expand to encompass all overlapping segments
        for seg in overlapping:
            if seg.start is not None and (
                merged.start is None or seg.start < merged.start
            ):
                merged.start = seg.start
            if seg.end is not None and (merged.end is None or seg.end > merged.end):
                merged.end = seg.end

        merge_action = MergeAction(
            merged_segments=[segment, *overlapping],
            result_segment=merged,
        )

        return MergeResolution(
            success=True,
            actions=[merge_action],
            segments_to_remove=list(overlapping),
            segments_to_add=[merged],
        )

    def name(self) -> str:
        return "merge"


@define
class ForceStrategy:
    """Insert segment regardless of conflicts (creates overlaps)."""

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger | None = None,
    ) -> MergeResolution:
        """Force insertion despite conflicts."""
        del merger  # Unused but required by protocol

        action = AddAction(
            segment=segment,
            reason=f"forced insertion despite {len(overlapping)} overlap(s) with {', '.join(_get_segment_id(s) for s in overlapping)}",
        )

        return MergeResolution(
            success=True,
            actions=[action],
            segments_to_add=[segment],
        )

    def name(self) -> str:
        return "force"


@define
class CombinedStrategy:
    """Try multiple strategies in sequence until one succeeds.

    This strategy encapsulates the multi-strategy pattern, trying each
    strategy in order until one successfully resolves the conflict.

    Attributes:
        strategies: Sequence of strategies to try in order
    """

    strategies: Sequence[MergeStrategy] = field(factory=list)

    def resolve(
        self,
        segment: TimeSegmentMixin,
        overlapping: list[TimeSegmentMixin],
        merger: SegmentMerger | None = None,
    ) -> MergeResolution:
        """Try strategies in sequence until one succeeds."""
        if not self.strategies:
            return MergeResolution(
                success=False,
                error_message="No strategies configured",
            )

        attempted_names = []
        all_conflicts = []

        for strategy in self.strategies:
            strategy_name = strategy.name()
            attempted_names.append(strategy_name)

            resolution = strategy.resolve(segment, overlapping, merger)

            if resolution.success:
                # Add info about which strategies were tried
                if len(attempted_names) > 1:
                    info_action = Action(
                        description=(
                            f"Tried {len(attempted_names)} strategies: "
                            f"{', '.join(attempted_names)}. "
                            f"Resolved with '{strategy_name}'"
                        ),
                    )
                    resolution.actions.insert(0, info_action)
                return resolution

            # Strategy didn't succeed, record conflict if present
            if resolution.conflict:
                all_conflicts.append(resolution.conflict)

            # If this strategy raises an error and it's the last one, propagate it
            if resolution.error_message and strategy == self.strategies[-1]:
                return MergeResolution(
                    success=False,
                    error_message=resolution.error_message,
                    conflict=resolution.conflict,
                )

        # All strategies failed
        return MergeResolution(
            success=False,
            error_message=(
                f"All {len(attempted_names)} strategies failed: "
                f"{', '.join(attempted_names)}"
            ),
            conflict=all_conflicts[0] if all_conflicts else None,
        )

    def name(self) -> str:
        strategy_names = [s.name() for s in self.strategies]
        return f"combined[{','.join(strategy_names)}]"


# ============================================================================
# 3. STRATEGY REGISTRY - Allows user-defined strategies
# ============================================================================


@define
class StrategyRegistry:
    """
    Global registry for merge strategies.

    Allows users to register custom strategies without modifying core code.

    Example:
        ```python
        from time_segments.merging import (
            register_strategy,
        )


        @define
        class MyCustomStrategy:
            def resolve(
                self,
                segment,
                overlapping,
                merger=None,
            ):
                # Custom logic here
                ...

            def name(self):
                return "my_custom"


        # Register it
        register_strategy(
            "my_custom",
            MyCustomStrategy,
        )

        # Use it
        merger = SegmentMerger(
            strategy="my_custom"
        )
        ```
    """

    _strategies: dict[str, type[MergeStrategy] | MergeStrategy] = field(factory=dict)

    def __attrs_post_init__(self):
        """Initialize registry with built-in strategies."""
        self._strategies.update({
            "error": ErrorStrategy,
            "skip": SkipStrategy,
            "replace": ReplaceStrategy,
            # "safe_replace": SafeReplaceStrategy,
            "merge": MergeSegmentsStrategy,
            "force": ForceStrategy,
        })

    def register(
        self,
        name: str,
        strategy: type[MergeStrategy] | MergeStrategy,
        *,
        overwrite: bool = False,
    ) -> None:
        """
        Register a strategy.

        Args:
            name: Name to register the strategy under
            strategy: Strategy class or instance
            overwrite: Allow overwriting existing strategies (default: False)

        Raises:
            ValueError: If strategy name already exists and overwrite=False

        Example:
            ```python
            registry.register(
                "my_strategy",
                MyStrategyClass,
            )
            # Or with instance
            registry.register(
                "my_strategy",
                MyStrategyClass(),
            )
            ```
        """
        if name in self._strategies and not overwrite:
            msg = (
                f"Strategy '{name}' already registered. "
                f"Use overwrite=True to replace it."
            )
            raise ValueError(msg)

        self._strategies[name] = strategy

    def unregister(self, name: str) -> None:
        """
        Unregister a strategy.

        Args:
            name: Name of strategy to unregister

        Raises:
            KeyError: If strategy not found
        """
        if name not in self._strategies:
            msg = f"Strategy '{name}' not found in registry"
            raise KeyError(msg)

        del self._strategies[name]

    def get(self, name: str) -> MergeStrategy:
        """
        Get a strategy instance by name.

        Args:
            name: Name of registered strategy

        Returns:
            Strategy instance (creates new instance if class was registered)

        Raises:
            ValueError: If strategy not found
        """
        if name not in self._strategies:
            available = list(self._strategies.keys())
            msg = (
                f"Unknown strategy: '{name}'. "
                f"Available strategies: {available}. "
                f"Use register_strategy() to add custom strategies."
            )
            raise ValueError(msg)

        strategy = self._strategies[name]

        # If it's a class, instantiate it
        if isinstance(strategy, type):
            return strategy()

        # If it's already an instance, return it
        return strategy

    def list_strategies(self) -> list[str]:
        """
        List all registered strategy names.

        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())

    def is_registered(self, name: str) -> bool:
        """
        Check if a strategy is registered.

        Args:
            name: Strategy name to check

        Returns:
            True if registered, False otherwise
        """
        return name in self._strategies


# Global registry instance
_global_registry = StrategyRegistry()


def register_strategy(
    name: str,
    strategy: type[MergeStrategy] | MergeStrategy,
    *,
    overwrite: bool = False,
) -> None:
    """
    Register a custom merge strategy globally.

    This allows you to define custom strategies and use them by name
    throughout your application without modifying the core code.

    Args:
        name: Name to register the strategy under
        strategy: Strategy class or instance implementing MergeStrategy protocol
        overwrite: Allow overwriting existing strategies (default: False)

    Raises:
        ValueError: If strategy name already exists and overwrite=False

    Example:
        ```python
        from attrs import (
            define,
        )
        from time_segments.merging import (
            register_strategy,
            MergeStrategy,
            MergeResolution,
            MergeAction,
            SegmentMerger,
        )


        @define
        class ConditionalMergeStrategy:
            '''Merge only if overlap is significant.'''

            threshold: float = 0.5  # 50% overlap required

            def resolve(
                self,
                segment,
                overlapping,
                merger=None,
            ):
                # Calculate overlap percentage
                # If > threshold, merge; otherwise skip
                ...

            def name(self):
                return "conditional_merge"


        # Register it
        register_strategy(
            "conditional_merge",
            ConditionalMergeStrategy,
        )

        # Use it anywhere
        merger = SegmentMerger(
            strategy="conditional_merge"
        )
        merger = SegmentMerger(
            strategies=[
                "conditional_merge",
                "force",
            ]
        )
        ```
    """
    _global_registry.register(name, strategy, overwrite=overwrite)


def unregister_strategy(name: str) -> None:
    """
    Unregister a strategy from the global registry.

    Args:
        name: Name of strategy to unregister

    Raises:
        KeyError: If strategy not found
    """
    _global_registry.unregister(name)


def list_strategies() -> list[str]:
    """
    List all registered strategy names.

    Returns:
        List of available strategy names

    Example:
        ```python
        strategies = list_strategies()
        print(
            f"Available: {strategies}"
        )
        # ['error', 'skip', 'replace', 'merge', 'force', 'my_custom']
        ```
    """
    return _global_registry.list_strategies()


def get_strategy(name: str) -> MergeStrategy:
    """
    Get a strategy instance by name.

    Args:
        name: Name of registered strategy

    Returns:
        Strategy instance

    Raises:
        ValueError: If strategy not found
    """
    return _global_registry.get(name)


# ============================================================================
# 4. MERGER CLASS - Orchestrates the merge operation
# ============================================================================


@define
class SegmentMerger:
    """
    Orchestrates segment insertion with conflict resolution.

    The merger detects conflicts and delegates resolution to a single
    configured strategy. For multi-strategy behavior, use CombinedStrategy.

    Attributes:
        strategy: The conflict resolution strategy to use. Can be a string
            (e.g., "error", "skip", "merge", "force") or a MergeStrategy instance.
        log_conflicts: If True (default), log warnings when conflicts occur.
            Set to False to suppress conflict warnings.

    Example:
        ```python
        # Single strategy
        merger = SegmentMerger(
            strategy="merge"
        )
        result = (
            merger.insert(
                collection,
                new_segment,
            )
        )

        # Disable conflict logging
        merger = SegmentMerger(
            strategy="skip",
            log_conflicts=False,
        )

        # Multiple strategies (using CombinedStrategy)
        merger = SegmentMerger(
            strategy=CombinedStrategy(
                strategies=[
                    SkipStrategy(),
                    MergeSegmentsStrategy(),
                    ForceStrategy(),
                ]
            )
        )
        result = (
            merger.insert(
                collection,
                new_segment,
            )
        )

        # Or use convenience function
        merger = (
            make_merger(
                [
                    "skip",
                    "merge",
                    "force",
                ]
            )
        )
        result = (
            merger.insert(
                collection,
                new_segment,
            )
        )
        ```
    """

    strategy: MergeStrategy | str = field(default="error")
    log_conflicts: bool = field(default=True, kw_only=True)
    _strategy_instance: MergeStrategy = field(init=False)

    def __attrs_post_init__(self):
        """Initialize strategy instance."""
        if isinstance(self.strategy, str):
            self._strategy_instance = get_strategy(self.strategy)
        else:
            self._strategy_instance = self.strategy

    def _log_conflict(self, conflict: MergeConflict) -> None:
        """Log a conflict as a warning if logging is enabled."""
        if self.log_conflicts:
            log.warning(f"Merge conflict: {conflict}")

    def _log_conflicts(self, conflicts: list[MergeConflict]) -> None:
        """Log multiple conflicts as warnings if logging is enabled."""
        if self.log_conflicts:
            for conflict in conflicts:
                log.warning(f"Merge conflict: {conflict}")

    def _handle_insert_error(
        self,
        segment: TimeSegmentMixin,
        error: ValueError,
    ) -> MergeConflict:
        """Create a conflict from an insertion error."""
        conflict = MergeConflict(
            segment=segment,
            overlapping=[],
            reason=str(error),
            strategy_attempted=self._strategy_instance.name(),
        )
        self._log_conflict(conflict)
        return conflict

    def _determine_insertion_index(
        self,
        segments_list: list[TimeSegmentMixin],
        segments_to_add: list[TimeSegmentMixin],
        segments_to_remove: list[TimeSegmentMixin],
    ) -> int | None:
        """
        Determine the best insertion index for new segments.

        Strategy:
        1. If segments are removed, use position of first removed segment
        2. For segments with defined start times, insert in temporal order
        3. For segments without start times, try to preserve relative order
           from the removed segments or append at end

        Args:
            segments_list: Current list of segments
            segments_to_add: Segments to be added
            segments_to_remove: Segments being removed

        Returns:
            Index where segments should be inserted, or None to append at end
        """
        if not segments_to_add:
            return None

        # Strategy 1: If removing segments, preserve position of first removed
        if segments_to_remove:
            for seg in segments_to_remove:
                if seg in segments_list:
                    idx = segments_list.index(seg)
                    log.debug(
                        f"Inserting at index {idx} (position of removed segment '{_get_segment_id(seg)}')"
                    )
                    return idx

        # Strategy 2: For segments with defined start times, find temporal position
        first_new_seg = segments_to_add[0]
        if hasattr(first_new_seg, "start") and first_new_seg.start is not None:
            # Find the right position based on start time
            for i, existing_seg in enumerate(segments_list):
                if hasattr(existing_seg, "start") and existing_seg.start is not None:
                    if first_new_seg.start < existing_seg.start:
                        log.debug(
                            f"Inserting at index {i} (temporal order: {first_new_seg.start} < {existing_seg.start})"
                        )
                        return i
                elif hasattr(existing_seg, "start") and existing_seg.start is None:
                    # Existing segment has no start time - ambiguous case
                    log.warning(
                        f"Ambiguous insertion position: new segment '{_get_segment_id(first_new_seg)}' "
                        f"has start time {first_new_seg.start} but existing segment "
                        f"'{_get_segment_id(existing_seg)}' has no start time. "
                        f"Inserting before the unspecified segment."
                    )
                    return i

            # All existing segments have earlier start times or no segments with start times
            log.debug(
                f"Appending segment '{_get_segment_id(first_new_seg)}' at end (latest start time)"
            )
            return None  # Append at end

        # Strategy 3: New segment has no start time - try to infer from context
        if segments_to_remove:
            # Check if removed segments had start times to infer position
            removed_with_times = [
                seg
                for seg in segments_to_remove
                if hasattr(seg, "start") and seg.start is not None
            ]

            if removed_with_times:
                # Use the earliest removed segment's temporal position
                earliest_removed = min(removed_with_times, key=lambda s: s.start)
                for i, existing_seg in enumerate(segments_list):
                    if (
                        hasattr(existing_seg, "start")
                        and existing_seg.start is not None
                        and earliest_removed.start <= existing_seg.start
                    ):
                        log.info(
                            f"Inserting segment '{_get_segment_id(first_new_seg)}' (no start time) "
                            f"at index {i} based on removed segment's temporal position"
                        )
                        return i

        # Strategy 4: No temporal or contextual information - log ambiguity and append
        log.warning(
            f"Ambiguous insertion position for segment '{_get_segment_id(first_new_seg)}' "
            f"with no start time and no contextual information. Appending at end."
        )
        return None  # Append at end

    def insert(
        self,
        collection: Sequence[TimeSegmentMixin],
        segment: TimeSegmentMixin,
    ) -> MergeResult:
        """
        Insert a segment into a collection with conflict resolution.

        Args:
            collection: Sequence of TimeSegmentMixin segments
            segment: The segment to insert

        Returns:
            MergeResult with details of what happened

        Raises:
            ValueError: If strategy fails with an error
        """
        # Convert to list if needed for mutability
        segments_list = _to_mutable_list(collection)

        # Find overlapping segments
        overlapping = [seg for seg in segments_list if seg.intersects(segment)]

        # No conflict - simple insertion
        if not overlapping:
            # Determine where to insert based on temporal ordering
            insert_index = self._determine_insertion_index(
                segments_list,
                [segment],
                [],
            )

            if insert_index is not None:
                segments_list.insert(insert_index, segment)
            else:
                segments_list.append(segment)

            action = AddAction(
                segment=segment,
                reason="no conflicts detected",
            )
            return MergeResult(
                success=True,
                actions=[action],
                segments_added=[segment],
                strategy_used="no_conflict",
            )

        # Conflict detected - resolve using strategy
        resolution = self._strategy_instance.resolve(segment, overlapping, self)

        # If strategy raises an error, propagate it
        if resolution.error_message:
            raise ValueError(resolution.error_message)

        # Apply resolution
        if resolution.success:
            # Remove segments first
            for seg in resolution.segments_to_remove:
                if seg in segments_list:
                    segments_list.remove(seg)

            # Determine insertion position
            insert_index = self._determine_insertion_index(
                segments_list,
                resolution.segments_to_add,
                resolution.segments_to_remove,
            )

            # Insert new segments at determined position
            if insert_index is not None:
                for i, seg in enumerate(resolution.segments_to_add):
                    segments_list.insert(insert_index + i, seg)
            else:
                # Append at end
                segments_list.extend(resolution.segments_to_add)

            return MergeResult(
                success=True,
                actions=resolution.actions,
                segments_added=resolution.segments_to_add,
                segments_removed=resolution.segments_to_remove,
                strategy_used=self._strategy_instance.name(),
            )

        # Resolution failed
        conflicts = [resolution.conflict] if resolution.conflict else []
        self._log_conflicts(conflicts)
        return MergeResult(
            success=False,
            actions=resolution.actions,
            conflicts=conflicts,
            strategy_used=self._strategy_instance.name(),
        )

    def insert_many(
        self,
        collection: Sequence[TimeSegmentMixin],
        segments: Sequence[TimeSegmentMixin],
    ) -> MergeResult:
        """
        Insert multiple segments into a collection.

        Args:
            collection: Sequence of TimeSegmentMixin segments
            segments: Sequence of segments to insert

        Returns:
            MergeResult aggregating all insertions
        """
        all_actions = []
        all_conflicts = []
        all_added = []
        all_removed = []
        overall_success = True

        for segment in segments:
            try:
                result = self.insert(collection, segment)
                all_actions.extend(result.actions)
                all_conflicts.extend(result.conflicts)
                all_added.extend(result.segments_added)
                all_removed.extend(result.segments_removed)
                if not result.success:
                    overall_success = False
            except ValueError as e:
                all_conflicts.append(self._handle_insert_error(segment, e))
                overall_success = False

        return MergeResult(
            success=overall_success,
            actions=all_actions,
            conflicts=all_conflicts,
            segments_added=all_added,
            segments_removed=all_removed,
            strategy_used=self._strategy_instance.name(),
        )

    def replace(
        self,
        collection: list[TimeSegmentMixin] | object,
        replacements: Sequence[
            tuple[Sequence[TimeSegmentMixin], Sequence[TimeSegmentMixin]]
        ],
        strategy: MergeStrategy | str | None = None,
    ) -> MergeResult:
        """
        Replace segments in a collection with new ones.

        Each replacement is a tuple of (old_segments, new_segments).
        All old segments are deleted first, then new segments are inserted
        using the specified strategy.

        Args:
            collection: Either a list of segments or an object with _segments_ attr
            replacements: Sequence of (old_segments, new_segments) tuples
            strategy: Strategy to use for insertions (default: "error")
                     Can be a strategy name or instance. Use "force" to allow
                     overlaps with remaining segments.

        Returns:
            MergeResult with details of all operations

        Example:
            ```python
            # Replace single segment
            merger = (
                SegmentMerger()
            )
            result = merger.replace(
                collection,
                [
                    (
                        [
                            old_segment
                        ],
                        [
                            new_segment
                        ],
                    )
                ],
            )

            # Replace multiple with overlap handling
            merger = (
                SegmentMerger()
            )
            result = merger.replace(
                collection,
                [
                    (
                        [
                            old_seg1,
                            old_seg2,
                        ],
                        [
                            new_seg1
                        ],
                    ),
                    (
                        [
                            old_seg3
                        ],
                        [
                            new_seg2,
                            new_seg3,
                        ],
                    ),
                ],
                strategy="force",  # Allow overlaps
            )

            # Check results
            if result.success:
                print(
                    f"Replaced {len(result.segments_removed)} segments"
                )
            else:
                print(
                    f"Conflicts: {result.conflicts}"
                )
            ```
        """
        # Convert to list if needed for mutability
        segments_list = _to_mutable_list(collection)

        # Create a temporary merger with the specified strategy for insertions
        insert_strategy = "error" if strategy is None else strategy

        insert_merger = SegmentMerger(
            strategy=insert_strategy,
            log_conflicts=self.log_conflicts,
        )

        all_actions: list[Action] = []
        all_conflicts: list[MergeConflict] = []
        all_added: list[TimeSegmentMixin] = []
        all_removed: list[TimeSegmentMixin] = []
        overall_success = True

        # Process each replacement
        for old_segments, new_segments in replacements:
            # Convert to lists if needed
            old_list = list(old_segments)
            new_list = list(new_segments)

            # Delete old segments first
            for old_seg in old_list:
                if old_seg in segments_list:
                    segments_list.remove(old_seg)
                    action = DeleteAction(
                        segment=old_seg,
                        reason="replaced with new segment(s)",
                    )
                    all_actions.append(action)
                    all_removed.append(old_seg)
                else:
                    # Segment not found - create conflict
                    seg_id = _get_segment_id(old_seg)
                    conflict = MergeConflict(
                        segment=old_seg,
                        overlapping=[],
                        reason=f"Segment '{seg_id}' not found in collection for replacement",
                        strategy_attempted="replace",
                    )
                    all_conflicts.append(conflict)
                    overall_success = False

            # Insert new segments using the specified strategy
            for new_seg in new_list:
                try:
                    result = insert_merger.insert(segments_list, new_seg)
                    all_actions.extend(result.actions)
                    all_conflicts.extend(result.conflicts)
                    all_added.extend(result.segments_added)
                    all_removed.extend(result.segments_removed)
                    if not result.success:
                        overall_success = False
                except ValueError as e:
                    # Error strategy raised exception
                    conflict = MergeConflict(
                        segment=new_seg,
                        overlapping=[],
                        reason=str(e),
                        strategy_attempted=insert_strategy
                        if isinstance(insert_strategy, str)
                        else "custom",
                    )
                    self._log_conflict(conflict)
                    all_conflicts.append(conflict)
                    overall_success = False

        strategy_name = (
            insert_strategy if isinstance(insert_strategy, str) else "custom"
        )
        return MergeResult(
            success=overall_success,
            actions=all_actions,
            conflicts=all_conflicts,
            segments_added=all_added,
            segments_removed=all_removed,
            strategy_used=f"replace_with_{strategy_name}",
        )


# ============================================================================
# 5. DIFF-BASED MERGER - Apply DiffResult to collection
# ============================================================================


@define
class DiffBasedMerger:
    """
    Merger that applies changes from a DiffResult to a collection.

    This merger systematically processes additions, deletions, and changes
    from a diff operation, creating proper Action objects for tracking.

    Attributes:
        protect_designer: If True, prevent deletion of blocks when incoming
                         block has a different designer (default: True)
        designer_attr: Attribute name to check for designer (default: "designer")
        log_conflicts: If True (default), log warnings when conflicts occur.
            Set to False to suppress conflict warnings.

    Example:
        ```python
        # Get diff from matcher result
        matcher = (
            BlockMatcher()
        )
        matcher.add_rule(
            IDMatcher("id")
            & TimingMatcher(
                60
            ),
            priority=0,
        )
        match_result = matcher.match(
            current_blocks,
            incoming_blocks,
        )

        differ = (
            TimelineDiffer(
                checkers=[
                    ...
                ]
            )
        )
        diff_result = (
            differ.diff(
                match_result
            )
        )

        # Apply diff with designer protection
        merger = DiffBasedMerger(
            protect_designer=True
        )
        merge_result = merger.apply(
            current_collection,
            diff_result,
        )

        # Check what happened
        print(
            merge_result.summary()
        )
        for conflict in merge_result.conflicts:
            print(
                f"Conflict: {conflict}"
            )
        ```
    """

    protect_designer: bool = True
    designer_attr: str = "designer"
    log_conflicts: bool = field(default=True, kw_only=True)

    def _log_conflict(self, conflict: MergeConflict) -> None:
        """Log a conflict as a warning if logging is enabled."""
        if self.log_conflicts:
            log.warning(f"Merge conflict: {conflict}")

    def apply(
        self,
        collection: Sequence[TimeSegmentMixin],
        diff_result: object,  # DiffResult from timeline_differ_simple.py
    ) -> MergeResult:
        """
        Apply a DiffResult to a collection.

        Args:
            collection: Sequence of TimeSegmentMixin segments
            diff_result: DiffResult from TimelineDiffer.diff()

        Returns:
            MergeResult describing all operations performed
        """
        # Convert to list if needed for mutability
        segments_list: list[TimeSegmentMixin] = (
            list(collection) if not isinstance(collection, list) else collection
        )

        actions: list[Action] = []
        conflicts: list[MergeConflict] = []
        all_added: list[TimeSegmentMixin] = []
        all_removed: list[TimeSegmentMixin] = []

        # Process deletions
        for deleted_block in diff_result.deletions:
            if deleted_block in segments_list:
                # Check if deletion is safe (designer protection)
                if self.protect_designer:
                    deleted_designer = getattr(deleted_block, self.designer_attr, None)

                    # Cannot delete if designer is unknown (None)
                    if deleted_designer is None:
                        conflict = MergeConflict(
                            segment=deleted_block,
                            overlapping=[],
                            reason=(
                                f"Deletion blocked: block has no {self.designer_attr} "
                                f"attribute, unsafe to delete"
                            ),
                            strategy_attempted="designer_protected_deletion",
                        )
                        self._log_conflict(conflict)
                        conflicts.append(conflict)

                        action = SkipAction(
                            segment=deleted_block,
                            reason=f"deletion skipped: {conflict.reason}",
                        )
                        actions.append(action)
                        continue

                    # Check if any additions have different designer
                    conflicting_additions = [
                        add_block
                        for add_block in diff_result.additions
                        if getattr(add_block, self.designer_attr, None)
                        != deleted_designer
                    ]

                    if conflicting_additions:
                        # Not safe to delete - different designer wants to add
                        conflict = MergeConflict(
                            segment=deleted_block,
                            overlapping=conflicting_additions,
                            reason=(
                                f"Deletion blocked: block has {self.designer_attr}="
                                f"'{deleted_designer}' but incoming blocks from different "
                                f"designer(s) detected"
                            ),
                            strategy_attempted="designer_protected_deletion",
                        )
                        self._log_conflict(conflict)
                        conflicts.append(conflict)

                        action = SkipAction(
                            segment=deleted_block,
                            reason=f"deletion skipped: {conflict.reason}",
                        )
                        actions.append(action)
                        continue

                # Safe to delete
                segments_list.remove(deleted_block)
                action = DeleteAction(
                    segment=deleted_block,
                    reason="removed in incoming timeline",
                )
                actions.append(action)
                all_removed.append(deleted_block)
            else:
                log.warning(
                    f"Block {getattr(deleted_block, 'id', 'unknown')} "
                    f"marked for deletion but not found in collection",
                )

        # Process changes (updates)
        for update_record in diff_result.changes:
            old_block = update_record.current_block
            new_block = update_record.incoming_block

            # Check if update is safe (designer protection)
            if self.protect_designer:
                old_designer = getattr(old_block, self.designer_attr, None)
                new_designer = getattr(new_block, self.designer_attr, None)

                # Cannot update if either designer is unknown (None)
                if old_designer is None or new_designer is None:
                    conflict = MergeConflict(
                        segment=new_block,
                        overlapping=[old_block],
                        reason=(
                            f"Update blocked: {self.designer_attr} attribute missing "
                            f"(current: {old_designer}, incoming: {new_designer}), "
                            f"unsafe to update"
                        ),
                        strategy_attempted="designer_protected_update",
                    )
                    self._log_conflict(conflict)
                    conflicts.append(conflict)

                    action = SkipAction(
                        segment=new_block,
                        reason=f"update skipped: {conflict.reason}",
                    )
                    actions.append(action)
                    continue

                # Cannot update if designers differ
                if old_designer != new_designer:
                    # Not safe to update - different designer
                    conflict = MergeConflict(
                        segment=new_block,
                        overlapping=[old_block],
                        reason=(
                            f"Update blocked: current block has {self.designer_attr}="
                            f"'{old_designer}' but incoming has '{new_designer}'"
                        ),
                        strategy_attempted="designer_protected_update",
                    )
                    self._log_conflict(conflict)
                    conflicts.append(conflict)

                    action = SkipAction(
                        segment=new_block,
                        reason=f"update skipped: {conflict.reason}",
                    )
                    actions.append(action)
                    continue

            if old_block in segments_list:
                # Find position and replace
                idx = segments_list.index(old_block)
                segments_list[idx] = new_block

                action = UpdateAction(
                    old_segment=old_block,
                    new_segment=new_block,
                    match=update_record.match,
                    changes=update_record.get_changes(),
                )
                actions.append(action)
                all_removed.append(old_block)
                all_added.append(new_block)
            else:
                log.warning(
                    f"Block {getattr(old_block, 'id', 'unknown')} "
                    f"marked for update but not found in collection",
                )

        # Process additions
        for added_block in diff_result.additions:
            # Check for time overlaps with existing blocks
            overlapping = []
            if (
                hasattr(added_block, "start")
                and hasattr(added_block, "end")
                and added_block.start is not None
                and added_block.end is not None
            ):
                for existing_block in segments_list:
                    if (
                        hasattr(existing_block, "start")
                        and hasattr(existing_block, "end")
                        and existing_block.start is not None
                        and existing_block.end is not None
                    ):
                        # Check if blocks overlap in time
                        if not (
                            added_block.end <= existing_block.start
                            or added_block.start >= existing_block.end
                        ):
                            overlapping.append(existing_block)

            # If there are overlapping blocks, check if insertion is safe
            if overlapping:
                # Check designer protection
                if self.protect_designer:
                    added_designer = getattr(added_block, self.designer_attr, None)

                    # Check if any overlapping block has different designer
                    different_designers = [
                        existing
                        for existing in overlapping
                        if getattr(existing, self.designer_attr, None) != added_designer
                    ]

                    if different_designers or added_designer is None:
                        # Not safe to add - overlaps with different designer(s)
                        overlap_designers = [
                            getattr(e, self.designer_attr, "unknown")
                            for e in different_designers
                        ]
                        conflict = MergeConflict(
                            segment=added_block,
                            overlapping=overlapping,
                            reason=(
                                f"Addition blocked: new block{' with no designer' if added_designer is None else f' from {added_designer}'} "
                                f"overlaps with block(s) from different designer(s): "
                                f"{', '.join(str(d) for d in set(overlap_designers))}"
                            ),
                            strategy_attempted="designer_protected_addition",
                        )
                        self._log_conflict(conflict)
                        conflicts.append(conflict)

                        action = SkipAction(
                            segment=added_block,
                            reason=f"addition skipped: {conflict.reason}",
                        )
                        actions.append(action)
                        continue
                else:
                    # No protection, but still create conflict for time overlap
                    conflict = MergeConflict(
                        segment=added_block,
                        overlapping=overlapping,
                        reason=(
                            f"Addition creates time overlap with {len(overlapping)} "
                            f"existing block(s)"
                        ),
                        strategy_attempted="unprotected_overlap_detection",
                    )
                    self._log_conflict(conflict)
                    conflicts.append(conflict)

                    action = SkipAction(
                        segment=added_block,
                        reason=f"addition skipped: {conflict.reason}",
                    )
                    actions.append(action)
                    continue

            # Safe to add - use merger's insertion logic for proper positioning
            merger = SegmentMerger(strategy="force")
            insert_index = merger._determine_insertion_index(
                segments_list,
                [added_block],
                [],
            )

            if insert_index is not None:
                segments_list.insert(insert_index, added_block)
            else:
                segments_list.append(added_block)

            action = AddAction(
                segment=added_block,
                reason="new in incoming timeline",
            )
            actions.append(action)
            all_added.append(added_block)

        return MergeResult(
            success=len(conflicts) == 0,
            actions=actions,
            conflicts=conflicts,
            segments_added=all_added,
            segments_removed=all_removed,
            strategy_used="diff_based"
            + ("_designer_protected" if self.protect_designer else ""),
        )


# ============================================================================
# 6. CONVENIENCE FUNCTIONS
# ============================================================================


def make_merger(
    strategy: str | Sequence[str] | MergeStrategy | None = None,
) -> SegmentMerger:
    """
    Create a SegmentMerger with the specified strategy or strategies.

    Args:
        strategy: Single strategy name, list of strategy names, or strategy instance.
                  If a list is provided, creates a CombinedStrategy that tries
                  each strategy in order until one succeeds.

    Returns:
        Configured SegmentMerger instance

    Example:
        ```python
        # Single strategy
        merger = (
            make_merger(
                "merge"
            )
        )
        result = (
            merger.insert(
                collection,
                segment,
            )
        )

        # Multiple strategies (tries in order)
        merger = (
            make_merger(
                [
                    "skip",
                    "merge",
                    "force",
                ]
            )
        )
        result = (
            merger.insert(
                collection,
                segment,
            )
        )

        # Strategy instance
        merger = make_merger(
            SafeReplaceStrategy(
                attr_name="designer"
            )
        )
        result = (
            merger.insert(
                collection,
                segment,
            )
        )

        # Default (error strategy)
        merger = (
            make_merger()
        )
        ```
    """
    if strategy is None:
        return SegmentMerger(strategy="error")

    if isinstance(strategy, str):
        return SegmentMerger(strategy=strategy)

    if isinstance(strategy, Sequence):
        # Convert list of strategy names to CombinedStrategy
        strategy_instances = [
            get_strategy(s) if isinstance(s, str) else s for s in strategy
        ]
        return SegmentMerger(strategy=CombinedStrategy(strategies=strategy_instances))

    # Strategy instance provided directly
    return SegmentMerger(strategy=strategy)


def make_progressive_merger() -> SegmentMerger:
    """
    Create a merger that tries progressively more permissive strategies.

    Tries: skip -> replace -> force

    This is useful for batch insertions where you want to avoid conflicts
    when possible, but ensure all segments are eventually inserted.

    Returns:
        Configured SegmentMerger with progressive strategies

    Example:
        ```python
        merger = make_progressive_merger()
        for (
            segment
        ) in new_segments:
            result = merger.insert(
                collection,
                segment,
            )
        ```
    """
    return make_merger(["skip", "replace", "force"])


def make_conservative_merger() -> SegmentMerger:
    """
    Create a merger that tries conservative strategies before failing.

    Tries: skip -> error

    This is useful when you want to avoid conflicts but get explicit
    notification when they cannot be avoided.

    Returns:
        Configured SegmentMerger with conservative strategies

    Example:
        ```python
        merger = make_conservative_merger()
        try:
            result = merger.insert(
                collection,
                segment,
            )
        except (
            ValueError
        ) as e:
            print(
                f"Could not insert: {e}"
            )
        ```
    """
    return make_merger(["skip", "error"])


def make_safe_replace_strategy(
    attr_name: str = "id",
    skip_if_mismatch: bool = False,
) -> SafeReplaceStrategy:
    """
    Create a customized SafeReplaceStrategy with specific attribute checking.

    This is useful when you want to customize which attribute is checked
    for equality before allowing replacement.

    Args:
        attr_name: Name of attribute to check for equality (default: "id")
        skip_if_mismatch: If True, skip on mismatch; if False, raise error

    Returns:
        Configured SafeReplaceStrategy instance

    Example:
        ```python
        # Check 'name' attribute instead of 'id'
        strategy = make_safe_replace_strategy(
            attr_name="name"
        )
        merger = SegmentMerger(
            strategy=strategy
        )
        result = (
            merger.insert(
                collection,
                segment,
            )
        )

        # Or use directly in strategy list
        merger = SegmentMerger(
            strategies=[
                make_safe_replace_strategy(
                    attr_name="name"
                ),
                "merge",
                "force",
            ]
        )
        ```
    """
    return SafeReplaceStrategy(
        attr_name=attr_name,
        skip_if_mismatch=skip_if_mismatch,
    )


def register_safe_replace_variant(
    name: str,
    attr_name: str = "id",
    skip_if_mismatch: bool = True,
) -> None:
    """
    Register a customized SafeReplaceStrategy variant with a custom name.

    This allows you to create and register a pre-configured safe replace
    strategy that can be used by name throughout your application.

    Args:
        name: Name to register the strategy under
        attr_name: Attribute to check for equality (default: "id")
        skip_if_mismatch: If True, skip on mismatch; if False, raise error

    Example:
        ```python
        # Register a variant that checks 'designer' attribute
        register_safe_replace_variant(
            "safe_replace_by_designer",
            attr_name="designer",
        )

        # Now use it by name
        merger = make_merger(
            "safe_replace_by_designer"
        )
        merger = make_merger(
            [
                "safe_replace_by_designer",
                "merge",
                "force",
            ]
        )
        ```
    """
    strategy = SafeReplaceStrategy(
        attr_name=attr_name,
        skip_if_mismatch=skip_if_mismatch,
    )
    register_strategy(name, strategy, overwrite=True)


def insert_with_strategy(
    collection: Sequence[TimeSegmentMixin],
    segment: TimeSegmentMixin,
    strategy: str = "error",
) -> MergeResult:
    """
    Convenience function to insert a segment with a single strategy.

    Args:
        collection: Sequence of TimeSegmentMixin segments
        segment: Segment to insert
        strategy: Conflict resolution strategy

    Returns:
        MergeResult with details of operation

    Example:
        ```python
        result = insert_with_strategy(
            collection,
            new_segment,
            strategy="merge",
        )
        ```
    """
    merger = make_merger(strategy=strategy)
    return merger.insert(collection, segment)


def insert_with_strategies(
    collection: Sequence[TimeSegmentMixin],
    segment: TimeSegmentMixin,
    strategies: Sequence[str],
) -> MergeResult:
    """
    Convenience function to insert a segment with multiple fallback strategies.

    Args:
        collection: Sequence of TimeSegmentMixin segments
        segment: Segment to insert
        strategies: List of strategy names to try in order

    Returns:
        MergeResult with details of operation

    Example:
        ```python
        result = insert_with_strategies(
            collection,
            new_segment,
            strategies=[
                "skip",
                "merge",
                "force",
            ],
        )
        print(
            f"Resolved with: {result.strategy_used}"
        )
        ```
    """
    merger = make_merger(list(strategies))
    return merger.insert(collection, segment)
