"""
Declarative Matching Pipeline for Time Segments.

A simple, priority-based approach to matching time segments using configurable rules.

Design Principles
-----------------
- **Declarative**: Define matching logic as readable rules with priorities
- **Composable**: Combine simple matchers (AND, OR, NOT) into complex conditions
- **Transparent**: Each match records which rule matched it
- **Incremental**: Process unmatched blocks with progressively looser criteria

Basic Usage
-----------
```python
# Create matcher and add rules (tried in priority order)
matcher = (
    BlockMatcher()
)
matcher.add_rule(
    IDMatcher("id")
    & TimingMatcher(
        0
    ),
    priority=0,
    description="Unique ID + Time",
)
matcher.add_rule(
    TimingMatcher(
        60
    ),
    priority=1,
    description="Time ±60s",
)

# Match blocks
(
    matches,
    unmatched_left,
    unmatched_right,
) = matcher.match(
    blocks1, blocks2
)

# View report
matcher.match_report(
    matches,
    len(blocks1),
    len(blocks2),
)
```

Operator Composition
--------------------
Matchers support Python operators for intuitive composition:

- `&` (AND): Both matchers must match
- `|` (OR): Either matcher can match
- `~` (NOT): Negate a matcher

Examples:
```python
# AND: ID must match AND timing within 60s
IDMatcher(
    "id"
) & TimingMatcher(
    60
)

# OR: Match by ID or ref
IDMatcher(
    "id"
) | IDMatcher("ref")

# NOT: Blocks that don't match exactly
~TimingMatcher(0)

# Complex: (ID or ref) AND timing within 60s
(
    IDMatcher("id")
    | IDMatcher(
        "ref"
    )
) & TimingMatcher(
    60
)
```

Available Matchers
------------------
- IDMatcher: Match by attribute (id, ref, etc.)
- TimingMatcher: Match by start/end times within tolerance
- EqualityMatcher: Match using __eq__ method
- DurationMatcher: Match by similar duration
- OverlapMatcher: Match by absolute time overlap
- PercentageOverlapMatcher: Match by percentage overlap
- LambdaMatcher: Match using custom function
- AndMatcher, OrMatcher, NotMatcher: Logical combinators
"""

from collections import Counter
from collections.abc import Callable
from typing import Protocol

from attrs import define, field

from ptr_editor.diffing.xml_diff_result import XmlDiffResult

# ============================================================================
# 1. MATCHER PROTOCOL WITH COMPOSITION SUPPORT
# ============================================================================


class MatcherCompositionMixin:
    """Mixin providing operator overloading for matcher composition."""

    def __and__(self, other):
        """Combine with AND logic using & operator."""
        return AndMatcher([self, other])

    def __or__(self, other):
        """Combine with OR logic using | operator."""
        return OrMatcher([self, other])

    def __invert__(self):
        """Negate using ~ operator."""
        return NotMatcher(self)


class Matcher(Protocol):
    """A matcher determines if two blocks match."""

    def matches(self, block1, block2) -> bool:
        """Return True if blocks match."""
        ...

    def name(self) -> str:
        """Return human-readable name for this matcher."""
        ...


# ============================================================================
# 2. BASIC MATCHERS (Building Blocks)
# ============================================================================


@define
class IDMatcher(MatcherCompositionMixin):
    """Match blocks by an identificator attribute."""

    attr: str = "id"

    def matches(self, block1, block2) -> bool:
        id1 = getattr(block1, self.attr, None)
        id2 = getattr(block2, self.attr, None)
        return id1 is not None and id2 is not None and id1 == id2

    def name(self) -> str:
        return f"{self.attr}"


@define
class TimingMatcher(MatcherCompositionMixin):
    """Match blocks by start/end times within tolerance."""

    tolerance_seconds: float = 0.0  # 0 = exact match

    def matches(self, block1, block2) -> bool:
        if not all(hasattr(b, "start") and hasattr(b, "end") for b in [block1, block2]):
            return False

        # Check if start/end are not None
        if block1.start is None or block1.end is None:
            return False
        if block2.start is None or block2.end is None:
            return False

        start_diff = abs((block1.start - block2.start).total_seconds())
        end_diff = abs((block1.end - block2.end).total_seconds())

        return (
            start_diff <= self.tolerance_seconds and end_diff <= self.tolerance_seconds
        )

    def name(self) -> str:
        if self.tolerance_seconds == 0:
            return "exact_timing"
        return f"timing_±{self.tolerance_seconds}s"


@define
class EqualityMatcher(MatcherCompositionMixin):
    """
    Match blocks using their __eq__ method.

    Args:
        exclude_attrs: Optional list of attribute names to exclude from comparison.
                      If provided, compares only non-excluded attributes.

    Example:
        # Exclude metadata from comparison
        EqualityMatcher(exclude_attrs=["metadata"])

        # Exclude multiple fields
        EqualityMatcher(exclude_attrs=["metadata", "timestamp", "version"])
    """

    exclude_attrs: list[str] | None = None

    def matches(self, block1, block2) -> bool:
        try:
            if not self.exclude_attrs:
                # No exclusions, use standard equality
                return block1 == block2

            # Compare all attributes except excluded ones
            # Use attrs.fields() if available, otherwise fall back to __dict__
            try:
                from attrs import fields as attrs_fields

                # Try to get attrs fields
                fields1 = {
                    f.name: getattr(block1, f.name)
                    for f in attrs_fields(type(block1))
                    if f.name not in self.exclude_attrs
                }
                fields2 = {
                    f.name: getattr(block2, f.name)
                    for f in attrs_fields(type(block2))
                    if f.name not in self.exclude_attrs
                }
                return fields1 == fields2
            except (TypeError, AttributeError):
                # Not an attrs class, use __dict__
                attrs1 = {
                    k: v
                    for k, v in block1.__dict__.items()
                    if k not in self.exclude_attrs
                }
                attrs2 = {
                    k: v
                    for k, v in block2.__dict__.items()
                    if k not in self.exclude_attrs
                }
                return attrs1 == attrs2
        except Exception:
            return False

    def name(self) -> str:
        if self.exclude_attrs:
            excluded = ",".join(self.exclude_attrs)
            return f"equality(exclude={excluded})"
        return "equality"


@define
class AndMatcher(MatcherCompositionMixin):
    """Match if ALL sub-matchers match (logical AND)."""

    matchers: list

    def matches(self, block1, block2) -> bool:
        return all(m.matches(block1, block2) for m in self.matchers)

    def name(self) -> str:
        return " + ".join(m.name() for m in self.matchers)


@define
class OrMatcher(MatcherCompositionMixin):
    """Match if ANY sub-matcher matches (logical OR)."""

    matchers: list

    def matches(self, block1, block2) -> bool:
        return any(m.matches(block1, block2) for m in self.matchers)

    def name(self) -> str:
        return " OR ".join(m.name() for m in self.matchers)


@define
class NotMatcher(MatcherCompositionMixin):
    """Negate a matcher (logical NOT)."""

    matcher: object  # Should be a Matcher, but using object to avoid circular reference

    def matches(self, block1, block2) -> bool:
        return not self.matcher.matches(block1, block2)

    def name(self) -> str:
        return f"NOT({self.matcher.name()})"

    def __invert__(self):
        """Double negation returns original matcher."""
        return self.matcher


# Custom matcher: Match by duration similarity
@define
class DurationMatcher(MatcherCompositionMixin):
    """Match blocks with similar duration."""

    tolerance_seconds: float = 0.0

    def matches(self, block1, block2) -> bool:
        if not all(hasattr(b, "start") and hasattr(b, "end") for b in [block1, block2]):
            return False

        dur1 = (block1.end - block1.start).total_seconds()
        dur2 = (block2.end - block2.start).total_seconds()

        return abs(dur1 - dur2) <= self.tolerance_seconds

    def name(self) -> str:
        if self.tolerance_seconds == 0:
            return "exact_duration"
        return f"duration_±{self.tolerance_seconds}s"


# Custom matcher: Match by overlap in time
@define
class OverlapMatcher(MatcherCompositionMixin):
    """Match blocks that overlap in time by at least a threshold."""

    min_overlap_seconds: float = 1.0

    def matches(self, block1, block2) -> bool:
        if not all(hasattr(b, "start") and hasattr(b, "end") for b in [block1, block2]):
            return False

        # Check if start/end are not None
        if block1.start is None or block1.end is None:
            return False
        if block2.start is None or block2.end is None:
            return False

        # Calculate overlap
        overlap_start = max(block1.start, block2.start)
        overlap_end = min(block1.end, block2.end)

        if overlap_end <= overlap_start:
            return False  # No overlap

        overlap_seconds = (overlap_end - overlap_start).total_seconds()
        return overlap_seconds >= self.min_overlap_seconds

    def name(self) -> str:
        return f"overlap≥{self.min_overlap_seconds}s"


# Custom matcher: Match by percentage overlap
@define
class PercentageOverlapMatcher(MatcherCompositionMixin):
    """
    Match blocks that overlap by at least a percentage threshold.

    The percentage is calculated based on the reference_strategy:
    - "min" (default): relative to the shorter block's duration
    - "max": relative to the longer block's duration
    - "avg": relative to the average
    - "both": both blocks must meet the threshold independently
    - "either": at least one block must meet the threshold

    Examples:
        # Default: 80% of shorter block must overlap
        PercentageOverlapMatcher(min_overlap_percentage=0.8)

        # 80% of longer block must overlap (more conservative)
        PercentageOverlapMatcher(min_overlap_percentage=0.8, reference_strategy="max")

        # Both blocks must have 80% overlap (most conservative)
        PercentageOverlapMatcher(min_overlap_percentage=0.8, reference_strategy="both")
    """

    min_overlap_percentage: float = 0.5  # 0.0 to 1.0 (50% default)
    reference_strategy: str = "min"  # "min", "max", "avg", "both", "either"

    def matches(self, block1, block2) -> bool:
        if not all(hasattr(b, "start") and hasattr(b, "end") for b in [block1, block2]):
            return False

        # Check if start/end are not None
        if block1.start is None or block1.end is None:
            return False
        if block2.start is None or block2.end is None:
            return False

        # Calculate overlap
        overlap_start = max(block1.start, block2.start)
        overlap_end = min(block1.end, block2.end)

        if overlap_end <= overlap_start:
            return False  # No overlap

        overlap_seconds = (overlap_end - overlap_start).total_seconds()

        # Calculate durations
        dur1 = (block1.end - block1.start).total_seconds()
        dur2 = (block2.end - block2.start).total_seconds()

        if dur1 <= 0 or dur2 <= 0:
            return False

        # Calculate overlap ratio based on strategy
        if self.reference_strategy == "min":
            # Use shorter duration as reference
            reference_duration = min(dur1, dur2)
            overlap_ratio = overlap_seconds / reference_duration
            return overlap_ratio >= self.min_overlap_percentage

        if self.reference_strategy == "max":
            # Use longer duration as reference
            reference_duration = max(dur1, dur2)
            overlap_ratio = overlap_seconds / reference_duration
            return overlap_ratio >= self.min_overlap_percentage

        if self.reference_strategy == "avg":
            # Use average duration as reference
            reference_duration = (dur1 + dur2) / 2
            overlap_ratio = overlap_seconds / reference_duration
            return overlap_ratio >= self.min_overlap_percentage

        if self.reference_strategy == "both":
            # Both blocks must meet threshold independently
            overlap_ratio1 = overlap_seconds / dur1
            overlap_ratio2 = overlap_seconds / dur2
            return (
                overlap_ratio1 >= self.min_overlap_percentage
                and overlap_ratio2 >= self.min_overlap_percentage
            )

        if self.reference_strategy == "either":
            # At least one block must meet threshold
            overlap_ratio1 = overlap_seconds / dur1
            overlap_ratio2 = overlap_seconds / dur2
            return (
                overlap_ratio1 >= self.min_overlap_percentage
                or overlap_ratio2 >= self.min_overlap_percentage
            )

        msg = (
            f"Invalid reference_strategy: {self.reference_strategy}. "
            "Must be one of: 'min', 'max', 'avg', 'both', 'either'"
        )
        raise ValueError(msg)

    def name(self) -> str:
        percentage = int(self.min_overlap_percentage * 100)
        if self.reference_strategy == "min":
            return f"overlap≥{percentage}%"
        return f"overlap≥{percentage}%({self.reference_strategy})"


# Lambda matcher for quick custom logic
@define
class LambdaMatcher(MatcherCompositionMixin):
    """Matcher from a lambda function."""

    func: Callable
    matcher_name: str = "custom"

    def matches(self, block1, block2) -> bool:
        return self.func(block1, block2)

    def name(self) -> str:
        return self.matcher_name


# ============================================================================
# 3. MATCHING RULE (Matcher + Priority)
# ============================================================================


@define
class MatchingRule:
    """A rule with a matcher and priority level."""

    matcher: Matcher
    priority: int = 0  # Lower = higher priority
    description: str = ""

    def __attrs_post_init__(self):
        if not self.description:
            self.description = self.matcher.name()


# ============================================================================
# 4. SIMPLE MATCHING ENGINE
# ============================================================================


@define
class UnmatchedBlock:
    """
    Wrapper for an unmatched block with diagnostic metadata.

    This class wraps a block that failed to match and stores information
    about overlapping blocks that were considered but didn't match, helping
    diagnose why matching failed.

    Attributes:
        block: The unmatched block
        side: Which side this block is from ('left' or 'right')
        overlapping_candidates: List of blocks from the other side that overlap
                                in time but didn't match according to rules
        original_index: Original index of the block in its input list
    """

    block: object
    side: str  # 'left' or 'right'
    overlapping_candidates: list = field(factory=list)
    original_index: int = -1

    def __repr__(self) -> str:
        """String representation showing block info and overlap count."""
        block_id = getattr(self.block, "id", "no_id")
        candidates = ",".join(o.id for o in self.overlapping_candidates)
        return (
            f"UnmatchedBlock({self.side}, id={block_id}, "
            f"{len(self.overlapping_candidates)} overlapping candidates: {candidates})"
        )


@define
class Match:
    """Result of a successful match."""

    left_block: object
    right_block: object
    rule: MatchingRule
    left_index: int
    right_index: int

    def diff(self) -> XmlDiffResult:
        """Get XML diff between left and right blocks, if supported.

        TODO hacky: we need better typing for all these classes to ensure
        that left_block has xml_diff method.
        """
        if hasattr(self.left_block, "xml_diff") and callable(
            getattr(self.left_block, "xml_diff")
        ):
            return self.left_block.xml_diff(self.right_block)
        raise NotImplementedError("Left block does not support xml_diff method")

    def __iter__(self):
        """
        Allow tuple unpacking for convenient access to block pairs.

        Enables convenient unpacking syntax:
        ```python
        left, right = match
        ```

        Returns:
        - left_block: The left block
        - right_block: The right block

        Example:
            >>> for match in match_result.matches:
            ...     left, right = match
            ...     print(f"{left.id} <-> {right.id}")
        """
        return iter([self.left_block, self.right_block])


@define
class MatchResult:
    """
    Container for matching results with convenient access to matched and unmatched blocks.

    This class provides multiple ways to access matching results:

    1. **Direct attribute access** (full metadata):
       - `result.matches` - List of Match objects with rule info
       - `result.unmatched_left` - List of UnmatchedBlock wrappers
       - `result.unmatched_right` - List of UnmatchedBlock wrappers

    2. **Property access** (unwrapped blocks):
       - `result.matched_blocks` - List of (left, right) tuples
       - `result.unmatched_blocks_left` - List of raw blocks
       - `result.unmatched_blocks_right` - List of raw blocks

    3. **Tuple unpacking** (for convenience):
       ```python
       (
           matches,
           unmatched_left,
           unmatched_right,
       ) = matcher.match(
           left, right
       )
       # Returns: matched_blocks, unmatched_blocks_left, unmatched_blocks_right
       ```

    Important Notes:
    - `unmatched_left` and `unmatched_right` attributes contain UnmatchedBlock wrappers
    - For multi-round matching, extract raw blocks using `.block` or the properties:
      ```python
      # Round 1
      result = (
          matcher1.match(
              left, right
          )
      )

      # Round 2 - extract raw blocks from wrappers
      raw_left = [
          ub.block
          for ub in result.unmatched_left
      ]
      raw_right = [
          ub.block
          for ub in result.unmatched_right
      ]
      result2 = (
          matcher2.match(
              raw_left,
              raw_right,
          )
      )

      # Or use properties directly
      result2 = matcher2.match(
          result.unmatched_blocks_left,
          result.unmatched_blocks_right,
      )
      ```

    Attributes:
        matches: List of Match objects containing matched pairs with metadata
        unmatched_left: List of UnmatchedBlock wrappers from left side
        unmatched_right: List of UnmatchedBlock wrappers from right side
        ambiguous_left: List of blocks that had ambiguous matches (if skip_ambiguous=True)
        left_total: Total number of blocks in left input
        right_total: Total number of blocks in right input

    Examples:
        >>> result = matcher.match(
        ...     blocks_left,
        ...     blocks_right,
        ... )

        # Access Match objects with metadata
        >>> for (
        ...     match
        ... ) in result.matches:
        ...     print(
        ...         f"Matched by rule: {match.rule.description}"
        ...     )
        ...     print(
        ...         f"Left: {match.left_block.id}, Right: {match.right_block.id}"
        ...     )

        # Quick access to block tuples
        >>> for (
        ...     left,
        ...     right,
        ... ) in result.matched_blocks:
        ...     print(
        ...         f"{left.id} <-> {right.id}"
        ...     )

        # Access unmatched blocks directly
        >>> print(
        ...     f"Unmatched: {len(result.unmatched_blocks_left)} blocks"
        ... )

        # Tuple unpacking for convenience
        >>> (
        ...     matches,
        ...     unmatched_l,
        ...     unmatched_r,
        ... ) = matcher.match(
        ...     left, right
        ... )
        >>> print(
        ...     f"Found {len(matches)} matches"
        ... )
    """

    matches: list[Match] = field(factory=list)
    unmatched_left: list[UnmatchedBlock] = field(factory=list)
    unmatched_right: list[UnmatchedBlock] = field(factory=list)
    ambiguous_left: list = field(factory=list)
    left_total: int = 0
    right_total: int = 0

    @property
    def matched_blocks(self) -> list[tuple[object, object]]:
        """
        Get list of matched block pairs as tuples.

        Returns unwrapped blocks without Match metadata.
        Each tuple is (left_block, right_block).

        Returns:
            List of (left_block, right_block) tuples

        Example:
            >>> for (
            ...     left,
            ...     right,
            ... ) in result.matched_blocks:
            ...     if (
            ...         left.id
            ...         != right.id
            ...     ):
            ...         print(
            ...             f"ID changed: {left.id} -> {right.id}"
            ...         )
        """
        return [(item.left_block, item.right_block) for item in self.matches]

    @property
    def unmatched_blocks_left(self) -> list[object]:
        """
        Get list of unmatched blocks from left side.

        Extracts raw blocks from UnmatchedBlock wrappers.
        Use this for multi-round matching or direct block access.

        Returns:
            List of raw block objects from left side

        Example:
            >>> # Use in second round of matching
            >>> result2 = matcher2.match(
            ...     result.unmatched_blocks_left,
            ...     result.unmatched_blocks_right,
            ... )
        """
        return [ub.block for ub in self.unmatched_left]

    @property
    def unmatched_blocks_right(self) -> list[object]:
        """
        Get list of unmatched blocks from right side.

        Extracts raw blocks from UnmatchedBlock wrappers.
        Use this for multi-round matching or direct block access.

        Returns:
            List of raw block objects from right side

        Example:
            >>> for block in result.unmatched_blocks_right:
            ...     print(
            ...         f"New block: {block.id}"
            ...     )
        """
        return [ub.block for ub in self.unmatched_right]

    @property
    def match_count(self) -> int:
        """Number of successful matches."""
        return len(self.matches)

    @property
    def unmatched_left_count(self) -> int:
        """Number of unmatched blocks from left."""
        return len(self.unmatched_left)

    @property
    def unmatched_right_count(self) -> int:
        """Number of unmatched blocks from right."""
        return len(self.unmatched_right)

    @property
    def ambiguous_count(self) -> int:
        """Number of ambiguous blocks from left."""
        return len(self.ambiguous_left)

    @property
    def match_rate_left(self) -> float:
        """Percentage of left blocks that were matched (0-1)."""
        if self.left_total == 0:
            return 0.0
        return self.match_count / self.left_total

    @property
    def match_rate_right(self) -> float:
        """Percentage of right blocks that were matched (0-1)."""
        if self.right_total == 0:
            return 0.0
        return self.match_count / self.right_total

    @property
    def overall_match_rate(self) -> float:
        """Average match rate across both sides (0-1)."""
        if self.left_total + self.right_total == 0:
            return 0.0
        return (self.match_count * 2) / (self.left_total + self.right_total)

    def matches_by_rule(self) -> dict[str, int]:
        """
        Get count of matches per rule.

        Returns:
            Dictionary mapping rule description to count
        """
        counts = Counter(m.rule.description for m in self.matches)
        return dict(counts)

    def get_unequal_matches(self) -> list[Match]:
        """
        Get matches where blocks differ by equality.

        Returns matches where the left and right blocks matched by some
        criteria (ID, timing, etc.) but are not equal according to their
        __eq__ method. These represent blocks that are "the same" but
        have different content/attributes.

        Returns:
            List of Match objects where left_block != right_block

        Example:
            # Find all matched blocks that have differences
            unequal = result.get_unequal_matches()
            for match in unequal:
                print(f"Block {match.left_block.id} differs between versions")
        """
        unequal = []
        for match in self.matches:
            try:
                if match.left_block != match.right_block:
                    unequal.append(match)
            except Exception:
                # If comparison fails, consider them unequal
                unequal.append(match)
        return unequal

    def get_equal_matches(self) -> list[Match]:
        """
        Get matches where blocks are equal.

        Returns matches where the left and right blocks are identical
        according to their __eq__ method. These represent blocks that
        matched and have no differences.

        Returns:
            List of Match objects where left_block == right_block

        Example:
            # Find all matched blocks that are identical
            equal = result.get_equal_matches()
            print(f"{len(equal)} blocks are unchanged")
        """
        equal = []
        for match in self.matches:
            try:
                if match.left_block == match.right_block:
                    equal.append(match)
            except Exception:
                # If comparison fails, skip
                pass
        return equal

    @property
    def unequal_match_count(self) -> int:
        """Number of matches where blocks differ by equality."""
        return len(self.get_unequal_matches())

    @property
    def equal_match_count(self) -> int:
        """Number of matches where blocks are equal."""
        return len(self.get_equal_matches())

    def summary(self) -> str:
        """
        Get a human-readable summary of matching results.

        Returns:
            Multi-line string with matching statistics
        """
        lines = [
            "Match Results Summary",
            "=" * 60,
            f"Total blocks: {self.left_total} left, {self.right_total} right",
            f"Matched: {self.match_count} pairs ({self.overall_match_rate:.1%} overall)",
            f"  Left match rate: {self.match_rate_left:.1%}",
            f"  Right match rate: {self.match_rate_right:.1%}",
            f"  Equal matches: {self.equal_match_count} (identical)",
            f"  Unequal matches: {self.unequal_match_count} (differ by content)",
            f"Unmatched: {self.unmatched_left_count} left, {self.unmatched_right_count} right",
        ]

        if self.ambiguous_count > 0:
            lines.append(
                f"Ambiguous: {self.ambiguous_count} left (multiple possible matches)",
            )

        if self.matches:
            lines.append("\nMatches by rule:")
            for rule_name, count in sorted(
                self.matches_by_rule().items(),
                key=lambda x: -x[1],
            ):
                lines.append(f"  {rule_name:40s}: {count:4d}")

        return "\n".join(lines)

    def report(self, *, show_ambiguous: bool = True):
        """
        Print a detailed matching report to stdout.

        Args:
            show_ambiguous: Whether to show ambiguous matches info (default: True)
        """
        print("=" * 70)
        print("MATCHING REPORT")
        print("=" * 70)
        print(f"\nTotal: {self.match_count} matches")
        print(
            f"Unmatched: {self.unmatched_left_count} left, "
            f"{self.unmatched_right_count} right",
        )

        if self.matches:
            print("\nMatches by rule:")
            for rule_name, count in sorted(
                self.matches_by_rule().items(),
                key=lambda x: -x[1],
            ):
                print(f"  {rule_name:40s}: {count:4d}")

        print("=" * 70)

        print(f"\n✓ Matched: {self.match_count} pairs")
        print(f"  Match rate: {self.overall_match_rate:.1%} overall")
        print(f"✗ Unmatched left: {self.unmatched_left_count}")
        print(f"✗ Unmatched right: {self.unmatched_right_count}")
        if show_ambiguous and self.ambiguous_count > 0:
            print(
                f"⚠ Ambiguous left: {self.ambiguous_count} "
                f"(skipped due to multiple matches)",
            )

    def __str__(self) -> str:
        """String representation showing key statistics."""
        return (
            f"MatchResult({self.match_count} matches, "
            f"{self.unmatched_left_count} unmatched left, "
            f"{self.unmatched_right_count} unmatched right)"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"MatchResult(matches={self.match_count}, "
            f"unmatched_left={self.unmatched_left_count}, "
            f"unmatched_right={self.unmatched_right_count}, "
            f"ambiguous={self.ambiguous_count})"
        )

    def __iter__(self):
        """
        Allow tuple unpacking for backward compatibility.

        Enables convenient unpacking syntax:
        ```python
        (
            matches,
            unmatched_left,
            unmatched_right,
        ) = matcher.match(
            left, right
        )
        ```

        Returns unwrapped blocks (not Match or UnmatchedBlock objects):
        - matches: List of (left_block, right_block) tuples
        - unmatched_left: List of raw left blocks
        - unmatched_right: List of raw right blocks

        This is equivalent to:
        ```python
        result = (
            matcher.match(
                left, right
            )
        )
        matches = result.matched_blocks
        unmatched_left = result.unmatched_blocks_left
        unmatched_right = result.unmatched_blocks_right
        ```

        Note:
            The unpacked values are raw blocks without metadata.
            Use `result.matches` for Match objects with rule information.
            Use `result.unmatched_left` for UnmatchedBlock wrappers with overlap info.
        """
        return iter(
            [
                self.matched_blocks,
                self.unmatched_blocks_left,
                self.unmatched_blocks_right,
            ],
        )

    def as_pandas_matches(
        self,
        attrs: list[str] | None = None,
        priority_columns: list[str] | None = None,
    ):
        """
        Convert matches to a pandas DataFrame.

        Each row represents a matched pair with columns for left block,
        right block, matching rule, and timing drift information.

        Args:
            attrs: Optional list of additional attribute names to extract from blocks
            priority_columns: Optional list of column names to appear first

        Returns:
            pd.DataFrame with matched pairs

        Example:
            df = result.as_pandas_matches(attrs=["id", "designer"])
            df[["left_id", "right_id", "rule", "start_drift_min"]]
        """
        import pandas as pd

        from ptr_editor.io.simplified_converter2 import tabletize_block

        if not self.matches:
            return pd.DataFrame()

        # Always include id in attrs if not already specified
        if attrs is None:
            attrs = ["id"]
        elif "id" not in attrs:
            attrs = ["id"] + list(attrs)

        rows = []
        for match in self.matches:
            # Get left and right block data
            left_series = tabletize_block(
                match.left_block,
                attrs=attrs,
                priority_columns=priority_columns,
            )
            right_series = tabletize_block(
                match.right_block,
                attrs=attrs,
                priority_columns=priority_columns,
            )

            # Create row with prefixed columns
            row = {}

            # Add left block data
            for col, val in left_series.items():
                row[f"left_{col}"] = val

            # Add right block data
            for col, val in right_series.items():
                row[f"right_{col}"] = val

            # Add match metadata
            row["rule"] = match.rule.description
            row["rule_priority"] = match.rule.priority
            row["left_index"] = match.left_index
            row["right_index"] = match.right_index

            # Calculate timing drifts if available
            if all(
                hasattr(b, "start") and hasattr(b, "end") and b.start and b.end
                for b in [match.left_block, match.right_block]
            ):
                start_drift_sec = (
                    match.right_block.start - match.left_block.start
                ).total_seconds()
                end_drift_sec = (
                    match.right_block.end - match.left_block.end
                ).total_seconds()
                left_dur = (
                    match.left_block.end - match.left_block.start
                ).total_seconds()
                right_dur = (
                    match.right_block.end - match.right_block.start
                ).total_seconds()

                row["start_drift_min"] = start_drift_sec / 60
                row["end_drift_min"] = end_drift_sec / 60
                row["duration_change_min"] = (right_dur - left_dur) / 60
                row["left_duration_min"] = left_dur / 60
                row["right_duration_min"] = right_dur / 60

            rows.append(row)

        return pd.DataFrame(rows)

    def as_pandas_unmatched_left(
        self,
        attrs: list[str] | None = None,
        priority_columns: list[str] | None = None,
    ):
        """
        Convert unmatched left blocks to a pandas DataFrame.

        Args:
            attrs: Optional list of additional attribute names to extract
            priority_columns: Optional list of column names to appear first

        Returns:
            pd.DataFrame with unmatched left blocks

        Example:
            df = result.as_pandas_unmatched_left()
            df[["id", "start", "end"]]
        """
        import pandas as pd

        from ptr_editor.io.simplified_converter2 import tabletize_block

        if not self.unmatched_left:
            return pd.DataFrame()

        # Always include id in attrs if not already specified
        if attrs is None:
            attrs = ["id"]
        elif "id" not in attrs:
            attrs = ["id", *attrs]

        rows = []
        for unmatched in self.unmatched_left:
            # Extract the actual block from UnmatchedBlock wrapper
            block = (
                unmatched.block if isinstance(unmatched, UnmatchedBlock) else unmatched
            )
            series = tabletize_block(
                block,
                attrs=attrs,
                priority_columns=priority_columns,
            )
            row_dict = series.to_dict()

            # Add UnmatchedBlock metadata if available
            if isinstance(unmatched, UnmatchedBlock):
                overlap_count = len(unmatched.overlapping_candidates)
                row_dict["overlapping_candidates_count"] = overlap_count

                # Add list of overlapping candidate IDs
                if overlap_count > 0:
                    candidate_ids = [
                        getattr(c, "id", "?") for c in unmatched.overlapping_candidates
                    ]
                    row_dict["overlapping_candidates_ids"] = ", ".join(
                        str(cid) for cid in candidate_ids[:10]
                    )
                    if overlap_count > 10:  # noqa: PLR2004
                        row_dict["overlapping_candidates_ids"] += (
                            f" ... (+{overlap_count - 10} more)"
                        )
                else:
                    row_dict["overlapping_candidates_ids"] = ""

                row_dict["original_index"] = unmatched.original_index

            rows.append(row_dict)

        return pd.DataFrame(rows)

    def as_pandas_unmatched_right(
        self,
        attrs: list[str] | None = None,
        priority_columns: list[str] | None = None,
    ):
        """
        Convert unmatched right blocks to a pandas DataFrame.

        Args:
            attrs: Optional list of additional attribute names to extract
            priority_columns: Optional list of column names to appear first

        Returns:
            pd.DataFrame with unmatched right blocks

        Example:
            df = result.as_pandas_unmatched_right()
            df[["id", "start", "end"]]
        """
        import pandas as pd

        from ptr_editor.io.simplified_converter2 import tabletize_block

        if not self.unmatched_right:
            return pd.DataFrame()

        # Always include id in attrs if not already specified
        if attrs is None:
            attrs = ["id"]
        elif "id" not in attrs:
            attrs = ["id", *attrs]

        rows = []
        for unmatched in self.unmatched_right:
            # Extract the actual block from UnmatchedBlock wrapper
            block = (
                unmatched.block if isinstance(unmatched, UnmatchedBlock) else unmatched
            )
            series = tabletize_block(
                block,
                attrs=attrs,
                priority_columns=priority_columns,
            )
            row_dict = series.to_dict()

            # Add UnmatchedBlock metadata if available
            if isinstance(unmatched, UnmatchedBlock):
                overlap_count = len(unmatched.overlapping_candidates)
                row_dict["overlapping_candidates_count"] = overlap_count

                # Add list of overlapping candidate IDs
                if overlap_count > 0:
                    candidate_ids = [
                        getattr(c, "id", "?") for c in unmatched.overlapping_candidates
                    ]
                    row_dict["overlapping_candidates_ids"] = ", ".join(
                        str(cid) for cid in candidate_ids[:10]
                    )
                    if overlap_count > 10:  # noqa: PLR2004
                        row_dict["overlapping_candidates_ids"] += (
                            f" ... (+{overlap_count - 10} more)"
                        )
                else:
                    row_dict["overlapping_candidates_ids"] = ""

                row_dict["original_index"] = unmatched.original_index

            rows.append(row_dict)

        return pd.DataFrame(rows)

    def as_pandas_ambiguous(
        self,
        attrs: list[str] | None = None,
        priority_columns: list[str] | None = None,
    ):
        """
        Convert ambiguous left blocks to a pandas DataFrame.

        Args:
            attrs: Optional list of additional attribute names to extract
            priority_columns: Optional list of column names to appear first

        Returns:
            pd.DataFrame with ambiguous left blocks

        Example:
            df = result.as_pandas_ambiguous()
            df[["id", "start", "end"]]
        """
        import pandas as pd

        from ptr_editor.io.simplified_converter2 import tabletize_block

        if not self.ambiguous_left:
            return pd.DataFrame()

        # Always include id in attrs if not already specified
        if attrs is None:
            attrs = ["id"]
        elif "id" not in attrs:
            attrs = ["id", *attrs]

        rows = []
        for block in self.ambiguous_left:
            series = tabletize_block(
                block,
                attrs=attrs,
                priority_columns=priority_columns,
            )
            rows.append(series.to_dict())

        return pd.DataFrame(rows)

    def as_pandas_summary(self):
        """
        Get a summary DataFrame with match statistics by rule.

        Returns:
            pd.DataFrame with columns: rule, count, percentage

        Example:
            summary = result.as_pandas_summary()
            print(summary.to_string(index=False))
        """
        import pandas as pd

        rule_counts = self.matches_by_rule()
        if not rule_counts:
            return pd.DataFrame(columns=["rule", "count", "percentage"])

        rows = []
        for rule, count in sorted(rule_counts.items(), key=lambda x: -x[1]):
            pct = (count / self.match_count * 100) if self.match_count > 0 else 0
            rows.append({"rule": rule, "count": count, "percentage": pct})

        return pd.DataFrame(rows)

    def as_pandas_unequal_matches(
        self,
        attrs: list[str] | None = None,
        priority_columns: list[str] | None = None,
    ):
        """
        Convert unequal matches (blocks that differ by equality) to a pandas DataFrame.

        This is useful for finding matched blocks that have differences in their
        attributes or content. Each row represents a matched pair where left != right.

        Args:
            attrs: Optional list of additional attribute names to extract from blocks
            priority_columns: Optional list of column names to appear first

        Returns:
            pd.DataFrame with matched pairs that differ by equality

        Example:
            # Find all matches where blocks differ
            df = result.as_pandas_unequal_matches(attrs=["id", "designer"])
            print(f"Found {len(df)} blocks with differences")

            # Compare specific attributes
            changed = df[df["left_designer"] != df["right_designer"]]
            print(f"{len(changed)} blocks changed designer")
        """
        import pandas as pd

        from ptr_editor.io.simplified_converter2 import tabletize_block

        unequal_matches = self.get_unequal_matches()
        if not unequal_matches:
            return pd.DataFrame()

        # Always include id in attrs if not already specified
        if attrs is None:
            attrs = ["id"]
        elif "id" not in attrs:
            attrs = ["id", *attrs]

        rows = []
        for match in unequal_matches:
            # Get left and right block data
            left_series = tabletize_block(
                match.left_block,
                attrs=attrs,
                priority_columns=priority_columns,
            )
            right_series = tabletize_block(
                match.right_block,
                attrs=attrs,
                priority_columns=priority_columns,
            )

            # Create row with prefixed columns
            row = {}

            # Add left block data
            for col, val in left_series.items():
                row[f"left_{col}"] = val

            # Add right block data
            for col, val in right_series.items():
                row[f"right_{col}"] = val

            # Add match metadata
            row["rule"] = match.rule.description
            row["rule_priority"] = match.rule.priority
            row["left_index"] = match.left_index
            row["right_index"] = match.right_index

            # Calculate timing drifts if available
            if all(
                hasattr(b, "start") and hasattr(b, "end") and b.start and b.end
                for b in [match.left_block, match.right_block]
            ):
                start_drift_sec = (
                    match.right_block.start - match.left_block.start
                ).total_seconds()
                end_drift_sec = (
                    match.right_block.end - match.left_block.end
                ).total_seconds()
                left_dur = (
                    match.left_block.end - match.left_block.start
                ).total_seconds()
                right_dur = (
                    match.right_block.end - match.right_block.start
                ).total_seconds()

                row["start_drift_min"] = start_drift_sec / 60
                row["end_drift_min"] = end_drift_sec / 60
                row["duration_change_min"] = (right_dur - left_dur) / 60
                row["left_duration_min"] = left_dur / 60
                row["right_duration_min"] = right_dur / 60

            rows.append(row)

        return pd.DataFrame(rows)

    def plot_timeline(self, **kwargs):
        """
        Plot timeline visualization showing matched and unmatched blocks.

        Args:
            **kwargs: Additional arguments passed to visualize.plot_match_timeline()
                     (figsize, max_blocks, output_file)

        Returns:
            matplotlib Figure object

        Example:
            result.plot_timeline(figsize=(16, 10), max_blocks=50)
            plt.show()
        """
        from ptr_editor.diffing.visualize import plot_match_timeline

        return plot_match_timeline(self, **kwargs)

    def plot_statistics(self, **kwargs):
        """
        Plot statistical summary with pie charts and bar charts.

        Args:
            **kwargs: Additional arguments passed to visualize.plot_match_statistics()
                     (figsize, output_file)

        Returns:
            matplotlib Figure object

        Example:
            result.plot_statistics(figsize=(14, 6), output_file='stats.png')
        """
        from ptr_editor.diffing.visualize import plot_match_statistics

        return plot_match_statistics(self, **kwargs)

    def plot_timing_drift(self, **kwargs):
        """
        Plot timing drift histograms showing start/end time differences.

        Args:
            **kwargs: Additional arguments passed to visualize.plot_timing_drift()
                     (max_matches, figsize, output_file)

        Returns:
            matplotlib Figure object

        Example:
            result.plot_timing_drift(max_matches=100)
            plt.show()
        """
        from ptr_editor.diffing.visualize import plot_timing_drift

        return plot_timing_drift(self, **kwargs)

    def plot_matrix(self, **kwargs):
        """
        Plot match matrix showing which blocks matched.

        Args:
            **kwargs: Additional arguments passed to visualize.plot_match_matrix()
                     (max_size, figsize, output_file)

        Returns:
            matplotlib Figure object

        Example:
            result.plot_matrix(max_size=50)
            plt.show()
        """
        from ptr_editor.diffing.visualize import plot_match_matrix

        return plot_match_matrix(self, **kwargs)

    def plot_durations(self, **kwargs):
        """
        Plot duration comparison between matched blocks.

        Args:
            **kwargs: Additional arguments passed to visualize.plot_duration_comparison()
                     (max_matches, figsize, output_file)

        Returns:
            matplotlib Figure object

        Example:
            result.plot_durations(max_matches=100)
            plt.show()
        """
        from ptr_editor.diffing.visualize import plot_duration_comparison

        return plot_duration_comparison(self, **kwargs)

    def to_html(
        self,
        output_file: str | None = None,
        *,
        open_browser: bool = False,
        use_temp_dir: bool = False,
    ):
        """
        Generate interactive HTML report and save to file.

        Args:
            output_file: Path to save HTML file. If None and use_temp_dir=True,
                        generates filename in temp dir. If None and use_temp_dir=False,
                        uses 'match_report.html' in current directory.
            open_browser: If True, opens the report in the default web browser
                         (default: False)
            use_temp_dir: If True, saves to system temporary directory (default: False)

        Returns:
            Path object pointing to generated HTML file

        Examples:
            # Save to current directory
            path = result.to_html('my_report.html')

            # Save to temp directory and open in browser
            path = result.to_html(open_browser=True, use_temp_dir=True)

            # Open in browser with custom filename in temp dir
            path = result.to_html(
                'analysis.html', open_browser=True, use_temp_dir=True
            )

            # Just open in browser (saves to temp dir by default)
            path = result.to_html(open_browser=True)
        """
        import tempfile
        import webbrowser
        from pathlib import Path

        from ptr_editor.diffing.visualize import generate_html_report

        # Determine output path
        if use_temp_dir or (open_browser and output_file is None):
            # Use temp directory
            temp_dir = Path(tempfile.gettempdir()) / "ptr_match_reports"
            temp_dir.mkdir(parents=True, exist_ok=True)

            if output_file is None:
                # Generate unique filename with timestamp
                from datetime import datetime, timezone

                timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
                output_path = temp_dir / f"match_report_{timestamp}.html"
            else:
                # Use provided filename in temp directory
                output_path = temp_dir / Path(output_file).name
        elif output_file is None:
            # Use default filename in current directory
            output_path = Path("match_report.html").resolve()
        else:
            # Use provided path
            output_path = Path(output_file)

        # Ensure absolute path for browser opening
        output_path = output_path.resolve()

        # Generate the report
        result_path = generate_html_report(self, str(output_path))

        # Ensure result is an absolute Path object
        if not isinstance(result_path, Path):
            result_path = Path(result_path)
        result_path = result_path.resolve()

        # Open in browser if requested
        if open_browser:
            file_url = result_path.as_uri()
            webbrowser.open(file_url)

        return result_path

    def _repr_html_(self):
        """
        HTML representation for Jupyter notebooks.

        This method is automatically called by Jupyter/IPython to display
        rich HTML output when the object is the last expression in a cell.

        Returns:
            HTML string with summary statistics and match information
        """
        from ptr_editor.diffing.visualize import generate_html_report

        return generate_html_report(self, output_file=None, compact=True)


@define
class BlockMatcher:
    """Simple greedy matching engine using prioritized rules."""

    rules: list[MatchingRule] = field(factory=list)
    skip_ambiguous: bool = True  # Skip matches when multiple right blocks match

    unmatched_left: list = field(factory=list)
    unmatched_right: list = field(factory=list)
    ambiguous_left: list = field(factory=list)  # Blocks with ambiguous matches

    def add_rule(self, matcher: Matcher, priority: int = 0, description: str = ""):
        """Add a matching rule."""
        self.rules.append(MatchingRule(matcher, priority, description))
        self.rules.sort(key=lambda r: r.priority)  # Keep sorted by priority
        return self

    def match(
        self,
        left_blocks: list,
        right_blocks: list,
    ) -> MatchResult:
        """
        Match blocks using rules in priority order.

        If skip_ambiguous is True (default), blocks with multiple possible
        matches are left unmatched at the current priority level but are
        reconsidered with subsequent (stricter/different) rules. A block
        ambiguous for one rule might be unique for the next rule.

        Returns:
            MatchResult object containing matches and unmatched blocks
        """
        matches = []
        unmatched_left = list(left_blocks)
        unmatched_right = list(right_blocks)
        ever_ambiguous_ids = set()  # Track block IDs that were ever ambiguous

        # Try each rule in priority order
        for rule in self.rules:
            if not unmatched_left or not unmatched_right:
                break

            new_matches = []
            still_unmatched_left = []
            still_unmatched_right = list(unmatched_right)

            # Greedy matching: for each left block, find matching right blocks
            for left_block in unmatched_left:
                matched = False

                if self.skip_ambiguous:
                    # Find ALL matching right blocks for this left block
                    matching_indices = [
                        idx
                        for idx, right_block in enumerate(still_unmatched_right)
                        if rule.matcher.matches(left_block, right_block)
                    ]

                    if len(matching_indices) == 0:
                        # No match with this rule - try next rule
                        still_unmatched_left.append(left_block)
                    elif len(matching_indices) == 1:
                        # Potential match - but check bidirectionally!
                        right_idx = matching_indices[0]
                        right_block = still_unmatched_right[right_idx]

                        # Check if this right block also matches multiple left blocks
                        reverse_matching_indices = [
                            idx
                            for idx, other_left_block in enumerate(unmatched_left)
                            if rule.matcher.matches(other_left_block, right_block)
                        ]

                        if len(reverse_matching_indices) == 1:
                            # Bidirectionally unique match - take it!
                            new_matches.append(
                                Match(
                                    left_block=left_block,
                                    right_block=right_block,
                                    rule=rule,
                                    left_index=left_blocks.index(left_block),
                                    right_index=right_blocks.index(right_block),
                                ),
                            )
                            still_unmatched_right.pop(right_idx)
                            matched = True
                        else:
                            # Right block matches multiple left blocks - ambiguous!
                            still_unmatched_left.append(left_block)
                            ever_ambiguous_ids.add(id(left_block))
                    else:
                        # Multiple matches - ambiguous at this rule level!
                        # Try again with next rule (more specific)
                        still_unmatched_left.append(left_block)
                        ever_ambiguous_ids.add(id(left_block))
                else:
                    # Original greedy behavior: take first match
                    for right_idx, right_block in enumerate(still_unmatched_right):
                        if rule.matcher.matches(left_block, right_block):
                            # Found a match!
                            new_matches.append(
                                Match(
                                    left_block=left_block,
                                    right_block=right_block,
                                    rule=rule,
                                    left_index=left_blocks.index(left_block),
                                    right_index=right_blocks.index(right_block),
                                ),
                            )
                            still_unmatched_right.pop(right_idx)
                            matched = True
                            break

                    if not matched:
                        still_unmatched_left.append(left_block)

            # Update state for next rule
            matches.extend(new_matches)
            unmatched_left = still_unmatched_left
            unmatched_right = still_unmatched_right

        # Final ambiguous list = blocks that were ever ambiguous and never got matched
        ambiguous_left = [
            block for block in unmatched_left if id(block) in ever_ambiguous_ids
        ]

        # Wrap unmatched blocks with metadata about overlapping candidates
        wrapped_unmatched_left = []
        for left_block in unmatched_left:
            # Find all right blocks that overlap in time but didn't match
            overlapping = self._find_overlapping_blocks(
                left_block,
                right_blocks,
                matches,
            )
            wrapped_unmatched_left.append(
                UnmatchedBlock(
                    block=left_block,
                    side="left",
                    overlapping_candidates=overlapping,
                    original_index=left_blocks.index(left_block),
                ),
            )

        wrapped_unmatched_right = []
        for right_block in unmatched_right:
            # Find all left blocks that overlap in time but didn't match
            overlapping = self._find_overlapping_blocks(
                right_block,
                left_blocks,
                matches,
            )
            wrapped_unmatched_right.append(
                UnmatchedBlock(
                    block=right_block,
                    side="right",
                    overlapping_candidates=overlapping,
                    original_index=right_blocks.index(right_block),
                ),
            )

        self.unmatched_left = wrapped_unmatched_left
        self.unmatched_right = wrapped_unmatched_right
        self.ambiguous_left = ambiguous_left

        return MatchResult(
            matches=matches,
            unmatched_left=self.unmatched_left,
            unmatched_right=self.unmatched_right,
            ambiguous_left=self.ambiguous_left,
            left_total=len(left_blocks),
            right_total=len(right_blocks),
        )

    def _find_overlapping_blocks(
        self,
        block,
        candidate_blocks: list,
        matches: list[Match],
    ) -> list:
        """
        Find blocks that overlap in time with the given block but weren't matched.

        Args:
            block: The unmatched block to check
            candidate_blocks: List of blocks from the other side to check against
            matches: List of successful matches to exclude

        Returns:
            List of blocks that overlap in time but didn't match
        """
        # Skip if block doesn't have timing info
        if not all(hasattr(block, attr) for attr in ["start", "end"]):
            return []
        if block.start is None or block.end is None:
            return []

        # Get set of already matched block IDs to exclude
        matched_block_ids = set()
        for match in matches:
            matched_block_ids.add(id(match.left_block))
            matched_block_ids.add(id(match.right_block))

        overlapping = []
        for candidate in candidate_blocks:
            # Skip if already matched
            if id(candidate) in matched_block_ids:
                continue

            # Skip if candidate doesn't have timing info
            if not all(hasattr(candidate, attr) for attr in ["start", "end"]):
                continue
            if candidate.start is None or candidate.end is None:
                continue

            # Check for temporal overlap
            overlap_start = max(block.start, candidate.start)
            overlap_end = min(block.end, candidate.end)

            if overlap_end > overlap_start:
                # There is overlap
                overlapping.append(candidate)

        return overlapping


# ============================================================================
# PREDEFINED MATCHER FACTORIES
# ============================================================================
#
# These factory functions create BlockMatcher instances configured for
# common matching scenarios. Use them as-is or as starting points for
# custom configurations.
#
# Available factories:
# - make_strict_matcher()           : Unique ID and timing matches only
# - make_flexible_matcher()         : ID + timing tolerance + overlap
# - make_robust_matcher()           : Multiple fallback strategies
# - make_multi_id_matcher()         : Multiple ID attributes (id, ref, etc.)
# - make_overlap_matcher()          : Focus on temporal overlap
# - make_progressive_matcher()      : Progressive timing loosening
# - make_duration_matcher()         : Match by duration similarity
# - make_custom_matcher()           : Build from rule specifications
#


def make_strict_matcher() -> BlockMatcher:
    """
    Create a strict matcher requiring exact matches.

    Use when blocks must match precisely by ID and timing.

    Returns:
        BlockMatcher configured with strict rules
    """
    matcher = BlockMatcher()
    matcher.add_rule(
        AndMatcher([IDMatcher("id"), TimingMatcher(0)]),
        priority=0,
        description="Unique ID + Timing",
    )
    matcher.add_rule(
        EqualityMatcher(),
        priority=1,
        description="Equality",
    )
    return matcher


def make_flexible_matcher(
    timing_tolerance_seconds: float = 60,
    overlap_threshold: float = 0.8,
) -> BlockMatcher:
    """
    Create a flexible matcher with timing tolerance and overlap support.

    Use when blocks may have slight timing differences but represent
    the same activity. Good for comparing planned vs executed timelines.

    Args:
        timing_tolerance_seconds: Maximum timing difference in seconds (default: 60)
        overlap_threshold: Minimum overlap percentage 0-1 (default: 0.8)

    Returns:
        BlockMatcher configured with flexible rules
    """
    matcher = BlockMatcher()

    # Unique ID + timing
    matcher.add_rule(
        AndMatcher([IDMatcher("id"), TimingMatcher(0)]),
        priority=0,
        description="Unique ID + Timing",
    )

    # ID + overlap percentage (handles timing drift)
    matcher.add_rule(
        AndMatcher(
            [
                IDMatcher("id"),
                PercentageOverlapMatcher(min_overlap_percentage=overlap_threshold),
            ],
        ),
        priority=1,
        description=f"ID + ≥{int(overlap_threshold * 100)}% Overlap",
    )

    # ID + timing tolerance
    matcher.add_rule(
        AndMatcher([IDMatcher("id"), TimingMatcher(timing_tolerance_seconds)]),
        priority=2,
        description=f"ID + Timing ±{timing_tolerance_seconds}s",
    )

    # Exact timing (no ID match)
    matcher.add_rule(
        TimingMatcher(0),
        priority=3,
        description="Exact Timing",
    )

    return matcher


def make_multi_id_matcher(
    id_attributes: list[str] | None = None,
    timing_tolerance_seconds: float = 60,
) -> BlockMatcher:
    """
    Create a matcher supporting multiple ID attributes.

    Use when blocks may have different identifier attributes (id, ref, name, etc.)
    and you want to try multiple matching strategies.

    Args:
        id_attributes: List of attribute names to use as IDs (default: ['id', 'ref'])
        timing_tolerance_seconds: Timing tolerance in seconds (default: 60)

    Returns:
        BlockMatcher configured with multiple ID matching rules
    """
    if id_attributes is None:
        id_attributes = ["id", "ref"]

    matcher = BlockMatcher()
    priority = 0

    # For each ID attribute, add exact timing match
    for attr in id_attributes:
        matcher.add_rule(
            AndMatcher([IDMatcher(attr), TimingMatcher(0)]),
            priority=priority,
            description=f"Exact {attr} + Timing",
        )
        priority += 1

    # For each ID attribute, add timing tolerance
    for attr in id_attributes:
        matcher.add_rule(
            AndMatcher([IDMatcher(attr), TimingMatcher(timing_tolerance_seconds)]),
            priority=priority,
            description=f"{attr} + Timing ±{timing_tolerance_seconds}s",
        )
        priority += 1

    # Fallback to timing only
    matcher.add_rule(
        TimingMatcher(0),
        priority=priority,
        description="Exact Timing",
    )

    return matcher


def make_overlap_matcher(
    min_overlap_percentage: float = 0.5,
    *,
    require_id_match: bool = False,
) -> BlockMatcher:
    """
    Create a matcher focused on temporal overlap.

    Use when you want to match blocks that overlap in time,
    regardless of exact start/end times. Useful for comparing
    activities that may have been rescheduled or adjusted.

    Args:
        min_overlap_percentage: Minimum overlap as fraction 0-1 (default: 0.5)
        require_id_match: If True, also require ID match (default: False)

    Returns:
        BlockMatcher configured for overlap matching
    """
    matcher = BlockMatcher()

    if require_id_match:
        # High overlap with ID
        matcher.add_rule(
            AndMatcher(
                [
                    IDMatcher("id"),
                    PercentageOverlapMatcher(min_overlap_percentage=0.9),
                ],
            ),
            priority=0,
            description="ID + ≥90% Overlap",
        )

        # Medium overlap with ID
        matcher.add_rule(
            AndMatcher(
                [
                    IDMatcher("id"),
                    PercentageOverlapMatcher(
                        min_overlap_percentage=min_overlap_percentage,
                    ),
                ],
            ),
            priority=1,
            description=f"ID + ≥{int(min_overlap_percentage * 100)}% Overlap",
        )
    else:
        # High overlap (no ID required)
        matcher.add_rule(
            PercentageOverlapMatcher(min_overlap_percentage=0.9),
            priority=0,
            description="≥90% Overlap",
        )

        # Specified overlap threshold
        matcher.add_rule(
            PercentageOverlapMatcher(min_overlap_percentage=min_overlap_percentage),
            priority=1,
            description=f"≥{int(min_overlap_percentage * 100)}% Overlap",
        )

    # Fallback to exact timing
    matcher.add_rule(
        TimingMatcher(0),
        priority=2,
        description="Exact Timing",
    )

    return matcher


def make_progressive_matcher(
    id_attr: str = "id",
    timing_steps: list[float] | None = None,
) -> BlockMatcher:
    """
    Create a matcher with progressive loosening of timing constraints.

    Use when you want to try increasingly loose matching criteria.
    Good for multi-round matching where unmatched blocks from strict
    rounds can be matched with looser criteria.

    Args:
        id_attr: Attribute name to use for ID matching (default: 'id')
        timing_steps: List of timing tolerances to try in order
                     (default: [0, 10, 60, 300])

    Returns:
        BlockMatcher configured with progressive timing rules
    """
    if timing_steps is None:
        timing_steps = [0, 10, 60, 300]  # 0s, 10s, 1min, 5min

    matcher = BlockMatcher()

    for priority, tolerance in enumerate(timing_steps):
        if tolerance == 0:
            desc = f"Exact {id_attr} + Timing"
        else:
            desc = f"{id_attr} + Timing ±{tolerance}s"

        matcher.add_rule(
            AndMatcher([IDMatcher(id_attr), TimingMatcher(tolerance)]),
            priority=priority,
            description=desc,
        )

    # Add equality fallback
    matcher.add_rule(
        EqualityMatcher(),
        priority=len(timing_steps),
        description="Equality",
    )

    return matcher


def make_duration_matcher(
    duration_tolerance_seconds: float = 10,
    *,
    also_match_timing: bool = True,
) -> BlockMatcher:
    """
    Create a matcher focused on duration similarity.

    Use when blocks should match if they have similar durations,
    useful for matching activities of the same type.

    Args:
        duration_tolerance_seconds: Maximum duration difference (default: 10)
        also_match_timing: If True, also consider timing overlap (default: True)

    Returns:
        BlockMatcher configured for duration matching
    """
    matcher = BlockMatcher()

    if also_match_timing:
        # ID + exact duration + exact timing
        matcher.add_rule(
            AndMatcher(
                [
                    IDMatcher("id"),
                    DurationMatcher(0),
                    TimingMatcher(0),
                ],
            ),
            priority=0,
            description="ID + Exact Duration + Timing",
        )

        # ID + similar duration
        matcher.add_rule(
            AndMatcher(
                [
                    IDMatcher("id"),
                    DurationMatcher(duration_tolerance_seconds),
                ],
            ),
            priority=1,
            description=f"ID + Duration ±{duration_tolerance_seconds}s",
        )
    else:
        # Just duration matching
        matcher.add_rule(
            DurationMatcher(0),
            priority=0,
            description="Exact Duration",
        )

        matcher.add_rule(
            DurationMatcher(duration_tolerance_seconds),
            priority=1,
            description=f"Duration ±{duration_tolerance_seconds}s",
        )

    return matcher


def make_custom_matcher(rules: list[tuple]) -> BlockMatcher:
    """
    Create a matcher from a list of rule specifications.

    Use when you need fine-grained control over matching rules.

    Args:
        rules: List of (matcher, priority, description) tuples

    Returns:
        BlockMatcher configured with custom rules

    Example:
        ```python
        matcher = make_custom_matcher(
            [
                (
                    AndMatcher(
                        [
                            IDMatcher(
                                "id"
                            ),
                            TimingMatcher(
                                0
                            ),
                        ]
                    ),
                    0,
                    "Exact",
                ),
                (
                    TimingMatcher(
                        60
                    ),
                    1,
                    "Timing ±60s",
                ),
                (
                    EqualityMatcher(),
                    2,
                    "Equality",
                ),
            ]
        )
        ```
    """
    matcher = BlockMatcher()
    for rule_spec in rules:
        if len(rule_spec) == 3:  # noqa: PLR2004
            rule_matcher, priority, description = rule_spec
            matcher.add_rule(rule_matcher, priority=priority, description=description)
        elif len(rule_spec) == 2:  # noqa: PLR2004
            rule_matcher, priority = rule_spec
            matcher.add_rule(rule_matcher, priority=priority)
        else:
            msg = (
                "Each rule must be (matcher, priority) or "
                "(matcher, priority, description)"
            )
            raise ValueError(msg)
    return matcher


def make_robust_matcher() -> BlockMatcher:
    """
    Create a robust matcher with multiple fallback strategies.

    This matcher prioritizes overlap percentage over strict timing, making it
    ideal for comparing timelines where activities may have been adjusted but
    maintain substantial temporal overlap. Includes multiple fallback strategies
    (ref matching, exact timing, equality) to maximize match coverage.

    Use when you need comprehensive matching with graceful degradation through
    multiple criteria.

    Returns:
        BlockMatcher configured with ID + overlap, timing, ref, and equality rules
    """
    # Create matcher with rules in priority order
    matcher = BlockMatcher()

    matcher.add_rule(EqualityMatcher(), priority=-20, description="Equality")

    matcher.add_rule(
        AndMatcher([IDMatcher("id"), TimingMatcher(0)]),
        priority=-10,
        description="Unique ID",
    )

    # Rule 1 (Priority 0): Unique ID + Overlap % (most strict)
    matcher.add_rule(
        AndMatcher(
            [IDMatcher("id"), PercentageOverlapMatcher(min_overlap_percentage=0.8)],
        ),
        priority=0,
        description="Unique ID + Overlap %",
    )

    # Rule 2 (Priority 1): ID + Near Timing (handles duplicated IDs with timing drift)
    matcher.add_rule(
        AndMatcher([IDMatcher("id"), TimingMatcher(60)]),
        priority=1,
        description="ID + Timing ±60s",
    )

    matcher.add_rule(
        EqualityMatcher(exclude_attrs=["metadata"]),
        priority=10,
        description="Equality W/O Metadata",
    )
    # Rule 4 Same designer with IDMatcher, strict Timing
    matcher.add_rule(
        AndMatcher([IDMatcher("ref"), TimingMatcher(0)]),
        priority=20,
        description="Same designer + Exact Timing",
    )

    return matcher
