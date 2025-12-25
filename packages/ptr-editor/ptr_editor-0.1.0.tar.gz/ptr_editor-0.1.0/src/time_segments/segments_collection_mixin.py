"""Mixin for handling collections of time segments."""

from __future__ import annotations

from collections.abc import Sequence
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Iterator, Literal, TypeVar

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Self

    from time_segments.merging import MergeResult, SegmentMerger

from .segment_mixin import TimeSegmentMixin

T = TypeVar("T", bound="TimeSegmentMixin")


class SegmentsCollectionMixin:
    """
    Mixin providing rich functionality for collections of time segments.

    Can be mixed into any class that manages a collection of segments,
    where each segment inherits from TimeSegmentMixin.

    Usage:
        class MySegment(TimeSegmentMixin):
            def __init__(self, start, end):
                self.start = start
                self.end = end

        class MySegmentCollection(SegmentsCollectionMixin):
            def __init__(self, segments):
                self._segments_ = segments

        collection = MySegmentCollection([seg1, seg2, seg3])
        collection.total_duration
        collection.find_gaps()
    """

    # Type hint for the collection attribute (to be provided by implementing class)
    # Segments must inherit from TimeSegmentMixin to have methods like
    # intersects, copy, etc.
    _segments_: list[TimeSegmentMixin]

    @property
    def total_duration(self) -> pd.Timedelta:
        """Return the total duration of all timed segments in the collection."""
        total = pd.Timedelta(0)
        for seg in self._segments_:
            if seg.start is not None and seg.end is not None:
                total += seg.end - seg.start
        return total

    @property
    def start(self) -> pd.Timestamp | None:
        """Return the earliest start time across all segments."""
        starts = [seg.start for seg in self._segments_ if seg.start is not None]
        return min(starts) if starts else None

    @property
    def end(self) -> pd.Timestamp | None:
        """Return the latest end time across all segments."""
        ends = [seg.end for seg in self._segments_ if seg.end is not None]
        return max(ends) if ends else None

    @property
    def timespan(self) -> pd.Timedelta | None:
        """Return the total timespan from earliest start to latest end."""
        start = self.start
        end = self.end
        if start is None or end is None:
            return None
        return end - start

    @property
    def is_empty(self) -> bool:
        """Return True if the collection has no segments."""
        return len(self._segments_) == 0

    @property
    def encompassing_segment(self) -> TimeSegmentMixin | None:
        """Return a single segment spanning the entire collection.

        Returns None if collection is empty.
        """
        if self.is_empty:
            return None

        start = self.start
        end = self.end

        # Create a copy of the first segment and modify its times
        encompassing = self._segments_[0].copy()
        encompassing.start = start
        encompassing.end = end
        return encompassing

    @property
    def is_time_resolved(self) -> bool:
        """Check if all segments in the timeline have defined start and end times."""
        return all(
            seg.start is not None and seg.end is not None for seg in self._segments_
        )

    @property
    def is_sorted(self) -> bool:
        """Check if segments are sorted by start time.

        Segments with None start times are considered to be in valid position.
        Returns True if all consecutive pairs with defined start times are in order.
        """
        return all(
            current.start is None
            or next_seg.start is None
            or current.start <= next_seg.start
            for current, next_seg in zip(
                self._segments_, self._segments_[1:], strict=False
            )
        )

    def sort(
        self,
        *,
        by: Literal["start", "end", "duration"] = "start",
        reverse: bool = False,
    ) -> None:
        """Sort segments in place.

        Args:
            by: Sort key - "start" for start time, "end" for end time,
                "duration" for duration
            reverse: If True, sort in descending order
        """
        if by == "start":
            self._segments_.sort(
                key=lambda seg: seg.start
                if seg.start is not None
                else pd.Timestamp.min,
                reverse=reverse,
            )
        elif by == "end":
            self._segments_.sort(
                key=lambda seg: seg.end if seg.end is not None else pd.Timestamp.max,
                reverse=reverse,
            )
        elif by == "duration":
            self._segments_.sort(
                key=lambda seg: seg.duration
                if seg.duration is not None
                else pd.Timedelta.min,
                reverse=reverse,
            )
        else:
            msg = f"Unknown sort key '{by}'. Use 'start', 'end', or 'duration'."
            raise ValueError(msg)

    def filter(self, predicate: Callable[[TimeSegmentMixin], bool]) -> Self:
        """Return a new collection with segments matching the predicate.

        Args:
            predicate: Function that returns True for segments to keep
        """
        filtered_segments = [seg for seg in self._segments_ if predicate(seg)]
        return self._create_new_collection(filtered_segments)

    def filter_by_time_range(
        self,
        start: (
            pd.Timestamp
            | str
            | TimeSegmentMixin
            | Sequence[TimeSegmentMixin]
            | None
        ) = None,
        end: pd.Timestamp | str | None = None,
    ) -> Self:
        """Return segments that overlap with the given time range.

        Can be called with:
        - Two arguments: start and end timestamps
        - One argument: an object with start/end attributes (e.g., a segment)
        - One argument: a sequence of segments (uses min start, max end)

        Args:
            start: One of:
                - Start timestamp (inclusive)
                - An object with start/end attributes (e.g., a segment)
                - A sequence of segments (computes encompassing time range)
            end: End of time range (inclusive). 
                 Ignored if start is a segment or sequence.

        Returns:
            A new collection containing segments that overlap with the time range.

        Example:
            >>> # Filter by explicit start/end
            >>> filtered = collection.filter_by_time_range(
            ...     start="2024-01-01",
            ...     end="2024-01-31",
            ... )
            >>>
            >>> # Filter by segment's time range
            >>> filtered = collection.filter_by_time_range(reference_segment)
            >>>
            >>> # Filter by encompassing range of multiple segments
            >>> filtered = collection.filter_by_time_range(other_collection)
        """
        # Handle sequence of segments - compute min/max time range
        if isinstance(start, Sequence) and not isinstance(start, str):
            segments = list(start)
            if not segments:
                # Empty sequence - return empty collection
                return self._create_new_collection([])
            starts = [s.start for s in segments if s.start is not None]
            ends = [s.end for s in segments if s.end is not None]
            start = min(starts) if starts else None
            end = max(ends) if ends else None
        # Handle single object with start/end attributes
        elif hasattr(start, "start") and hasattr(start, "end"):
            range_obj = start
            start = range_obj.start
            end = range_obj.end
        
        if start is not None:
            start = pd.Timestamp(start)
        if end is not None:
            end = pd.Timestamp(end)

        def overlaps_range(seg: TimeSegmentMixin) -> bool:
            if seg.start is None or seg.end is None:
                return False
            if start is not None and seg.end < start:
                return False
            return not (end is not None and seg.start > end)

        return self.filter(overlaps_range)

    def find_gaps(self) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        """Find gaps between segments.

        Returns a list of (start, end) tuples representing gaps.
        Segments are first sorted by start time.
        """
        min_segments = 2
        if len(self._segments_) < min_segments:
            return []

        # Create a sorted copy
        sorted_segs = sorted(
            self._segments_,
            key=lambda seg: seg.start if seg.start is not None else pd.Timestamp.min,
        )

        gaps = []
        for i in range(len(sorted_segs) - 1):
            current = sorted_segs[i]
            next_seg = sorted_segs[i + 1]

            if (
                current.end is not None
                and next_seg.start is not None
                and current.end < next_seg.start
            ):
                gaps.append((current.end, next_seg.start))

        return gaps

    def find_overlaps(self) -> list[tuple[TimeSegmentMixin, TimeSegmentMixin]]:
        """Find all pairs of overlapping segments.

        Returns a list of tuples, each containing two overlapping segments.
        """
        return [
            (seg1, seg2)
            for i, seg1 in enumerate(self._segments_)
            for seg2 in self._segments_[i + 1 :]
            if seg1.intersects(seg2)
        ]

    def has_overlaps(self) -> bool:
        """Check if any segments in the collection overlap.

        Returns True if at least one pair of segments overlaps, False otherwise.
        This is more efficient than find_overlaps() when you only need to know
        if overlaps exist.
        """
        for i, seg1 in enumerate(self._segments_):
            for seg2 in self._segments_[i + 1 :]:
                if seg1.intersects(seg2):
                    return True
        return False

    def merge_overlapping(self) -> Self:
        """Merge all overlapping segments into non-overlapping segments.

        Returns a new collection with merged segments.
        """
        if not self._segments_:
            return self._create_new_collection([])

        # Sort by start time
        sorted_segs = sorted(
            self._segments_,
            key=lambda seg: seg.start if seg.start is not None else pd.Timestamp.min,
        )

        merged = []
        current = sorted_segs[0].copy()

        for seg in sorted_segs[1:]:
            if seg.start is None or seg.end is None:
                continue
            if current.end is None:
                merged.append(current)
                current = seg.copy()
                continue

            # Check if segments overlap or touch
            if seg.start <= current.end:
                # Merge by extending current
                if seg.end is not None and seg.end > current.end:
                    current.end = seg.end
            else:
                # No overlap, save current and start new
                merged.append(current)
                current = seg.copy()

        merged.append(current)
        return self._create_new_collection(merged)

    def split_at_time(self, time: pd.Timestamp | str) -> tuple[Self, Self]:
        """Split collection into two at the given time.

        Returns:
            Tuple of (before, after) collections
        """
        time = pd.Timestamp(time)
        before = []
        after = []

        for seg in self._segments_:
            if seg.end is not None and seg.end <= time:
                before.append(seg)
            elif seg.start is not None and seg.start >= time:
                after.append(seg)
            else:
                # Segment spans the split time
                split_segs = seg.split(time)
                num_splits = 2
                if len(split_segs) == num_splits:
                    before.append(split_segs[0])
                    after.append(split_segs[1])
                elif seg.start is not None and seg.start < time:
                    before.append(split_segs[0])
                else:
                    after.append(split_segs[0])

        return (
            self._create_new_collection(before),
            self._create_new_collection(after),
        )

    def filter_by_time(self, time: pd.Timestamp | str) -> Self:
        """Return segments that contain the given time.

        Args:
            time: The timestamp to check

        Returns:
            A new collection containing only segments that contain the given time.

        Example:
            >>> # Find all segments active at a specific time
            >>> active = collection.filter_by_time("2024-01-01 12:00:00")
        """
        time = pd.Timestamp(time)
        return self.filter(lambda seg: seg.contains(time))

    def filter_intersecting(
        self,
        other: TimeSegmentMixin | Sequence[TimeSegmentMixin],
    ) -> Self:
        """Return segments that intersect with the given segment(s).

        Args:
            other: A single segment or sequence of segments to check for intersections.
                   Returns all segments from self that intersect with ANY of the
                   provided segments.

        Returns:
            A new collection containing segments that overlap with any of the
            provided segments.

        Example:
            >>> # Find segments overlapping a single segment
            >>> overlapping = collection.filter_intersecting(segment)
            >>>
            >>> # Find segments overlapping any of the provided segments
            >>> overlapping = collection.filter_intersecting([seg1, seg2, seg3])
            >>>
            >>> # Use with diff result deletions
            >>> additions, deletions, changes = differ.diff(match_result)
            >>> affected = collection.filter_intersecting(deletions)
        """
        # Normalize to sequence
        others = [other] if isinstance(other, TimeSegmentMixin) else list(other)

        def intersects_any(seg: TimeSegmentMixin) -> bool:
            return any(seg.intersects(o) for o in others)

        return self.filter(intersects_any)

    def is_id_unique(self, segment_id: str | int) -> bool:
        """Check if an ID is unique in the collection.

        Args:
            segment_id: The ID to check

        Returns:
            True if the ID appears exactly once or not at all,
            False if it appears multiple times

        Example:
            >>> if not collection.is_id_unique(
            ...     "obs_001"
            ... ):
            ...     print(
            ...         "Warning: Duplicate ID found!"
            ...     )
        """
        count = 0
        for seg in self._segments_:
            if hasattr(seg, "id") and seg.id == segment_id:
                count += 1
                if count > 1:
                    return False
        return True

    def find_by_id(self, segment_id: str | int) -> TimeSegmentMixin | None:
        """Find a segment by its ID.

        Args:
            segment_id: The ID to search for

        Returns:
            The segment with the matching ID, or None if not found

        Raises:
            ValueError: If multiple segments with the same ID are found

        Example:
            >>> segment = collection.find_by_id(
            ...     "obs_001"
            ... )
            >>> if segment:
            ...     print(
            ...         f"Found: {segment.start} - {segment.end}"
            ...     )
        """
        if not self.is_id_unique(segment_id):
            msg = f"Multiple segments found with id '{segment_id}'. IDs must be unique. Use filter_by_id instead."
            raise ValueError(msg)

        for seg in self._segments_:
            if hasattr(seg, "id") and seg.id == segment_id:
                return seg
        return None

    def filter_by_id(
        self,
        pattern: str | list[str],
        mode: Literal["any", "all"] = "any",
    ) -> Self:
        """Filter segments by their ID using wildcards.

        Supports Unix shell-style wildcards:
        - `*` matches everything
        - `?` matches any single character
        - `[seq]` matches any character in seq
        - `[!seq]` matches any character not in seq

        Args:
            pattern: ID pattern(s) with optional wildcards. Can be a single string
                    or a list of patterns.
            mode: Match mode when multiple patterns are provided:
                - "any": Match segments that match ANY of the patterns (default)
                - "all": Match segments that match ALL of the patterns

        Returns:
            A new collection containing only the segments with matching IDs

        Example:
            >>> # Find all observation blocks
            >>> obs_blocks = collection.filter_by_id(
            ...     "obs_*"
            ... )
            >>>
            >>> # Find blocks matching any of the patterns
            >>> blocks = collection.filter_by_id(
            ...     [
            ...         "COSMIC_*",
            ...         "MAJ_*",
            ...     ],
            ...     mode="any",
            ... )
            >>>
            >>> # Find blocks matching all patterns (ID must contain all substrings)
            >>> blocks = collection.filter_by_id(
            ...     [
            ...         "*_SAT_*",
            ...         "*_SCAN_*",
            ...     ],
            ...     mode="all",
            ... )
            >>>
            >>> # Exact match (no wildcards)
            >>> block = collection.filter_by_id(
            ...     "obs_001"
            ... )
        """
        # Normalize pattern to list
        patterns = [pattern] if isinstance(pattern, str) else pattern

        if mode == "any":
            # Match if ANY pattern matches
            filtered = [
                seg
                for seg in self._segments_
                if hasattr(seg, "id")
                and any(fnmatch(str(seg.id), pat) for pat in patterns)
            ]
        elif mode == "all":
            # Match if ALL patterns match
            filtered = [
                seg
                for seg in self._segments_
                if hasattr(seg, "id")
                and all(fnmatch(str(seg.id), pat) for pat in patterns)
            ]
        else:
            msg = f"Invalid mode '{mode}'. Use 'any' or 'all'."
            raise ValueError(msg)

        return self._create_new_collection(filtered)

    def insert(
        self,
        segment: TimeSegmentMixin | list[TimeSegmentMixin],
        *,
        strategy: str | SegmentMerger = "error",
    ) -> MergeResult:
        """Insert a segment or list of segments into the collection with conflict resolution.

        TODO move the entire logic in the merger by creating a SegmentMerger for
        ptrs somewhere else

        Args:
            segment: The segment(s) to insert. Can be a single segment or a list of segments.
            strategy: Strategy for handling overlapping segments:
                - "error": Raise ValueError if segment overlaps
                - "skip": Skip insertion if segment overlaps
                - "replace": Remove overlapping segments and insert new one
                - "force": Insert regardless of overlaps

        Returns:
            MergeResult containing information about the insertion operation

        Raises:
            ValueError: If strategy="error" and segment overlaps with existing

        Example:
            >>> # Insert a single segment
            >>> result = collection.insert(
            ...     new_segment
            ... )
            >>>
            >>> # Insert multiple segments
            >>> result = collection.insert(
            ...     [
            ...         seg1,
            ...         seg2,
            ...         seg3,
            ...     ]
            ... )
            >>>
            >>> # Use different strategy
            >>> result = collection.insert(
            ...     segment,
            ...     strategy="replace",
            ... )
        """
        from time_segments.merging import SegmentMerger

        if isinstance(strategy, SegmentMerger):
            merger = strategy

        elif isinstance(strategy, str):
            # Use the new merger system
            merger = SegmentMerger(strategy=strategy)

        else:
            msg = (
                f"Invalid strategy type '{type(strategy)}'. "
                "Must be a string or SegmentMerger instance."
            )
            raise ValueError(msg)

        # Handle both single segment and list of segments
        if isinstance(segment, list):
            return merger.insert_many(self._segments_, segment)

        return merger.insert(self._segments_, segment)

    def append(self, segment: TimeSegmentMixin | list[TimeSegmentMixin]) -> Self:
        """Append a segment or list of segments to the collection.

        Args:
            segment: Single segment or list of segments to append

        Returns:
            Self for method chaining
        """
        if isinstance(segment, list):
            self._segments_.extend(segment)
        else:
            self._segments_.append(segment)
        return self

    def __add__(
        self,
        other: SegmentsCollectionMixin
        | Sequence[TimeSegmentMixin]
        | TimeSegmentMixin,
    ) -> Self:
        """Create a new collection by concatenating segments from another source.

        The original collections remain untouched; incoming segments are copied to
        avoid sharing parent references between collections.
        """
        new_collection = self.copy()

        if isinstance(other, SegmentsCollectionMixin):
            incoming_segments: Sequence[TimeSegmentMixin] = other._segments_
        elif isinstance(other, TimeSegmentMixin):
            incoming_segments = [other]
        elif isinstance(other, Sequence):
            incoming_segments = list(other)
        else:
            return NotImplemented

        for segment in incoming_segments:
            segment_to_add = segment.copy() if hasattr(segment, "copy") else segment
            new_collection.append(segment_to_add)

        return new_collection

    def __radd__(
        self,
        other: SegmentsCollectionMixin
        | Sequence[TimeSegmentMixin]
        | TimeSegmentMixin,
    ) -> Self:
        """Support reversed addition so sequences or collections can lead."""
        if isinstance(other, SegmentsCollectionMixin):
            new_collection = other.copy()
            leading_segments: Sequence[TimeSegmentMixin] = []
            trailing_segments = self._segments_
        elif isinstance(other, TimeSegmentMixin):
            new_collection = self._create_new_collection([])
            leading_segments = [other]
            trailing_segments = self._segments_
        elif isinstance(other, Sequence):
            new_collection = self._create_new_collection([])
            leading_segments = list(other)
            trailing_segments = self._segments_
        else:
            return NotImplemented

        for segment in leading_segments:
            segment_to_add = segment.copy() if hasattr(segment, "copy") else segment
            new_collection.append(segment_to_add)

        for segment in trailing_segments:
            segment_to_add = segment.copy() if hasattr(segment, "copy") else segment
            new_collection.append(segment_to_add)

        return new_collection

    def __iadd__(
        self,
        other: SegmentsCollectionMixin
        | Sequence[TimeSegmentMixin]
        | TimeSegmentMixin,
    ) -> Self:
        """Support in-place addition using += operator.

        Segments are appended to this collection. The append method handles
        any necessary copying or parent reference management.
        """
        if isinstance(other, SegmentsCollectionMixin):
            segments_to_add: Sequence[TimeSegmentMixin] = other._segments_
        elif isinstance(other, TimeSegmentMixin):
            segments_to_add = [other]
        elif isinstance(other, Sequence):
            segments_to_add = list(other)
        else:
            return NotImplemented

        for segment in segments_to_add:
            self.append(segment)

        return self

    def drop(self, segment: TimeSegmentMixin | list[TimeSegmentMixin]) -> Self:
        """Remove a segment or list of segments from the collection.

        Args:
            segment: Single segment or list of segments to remove

        Returns:
            Self for method chaining
        """
        if isinstance(segment, list):
            # Create a copy to avoid issues when segment is self.segments
            to_remove = list(segment)
            for seg in to_remove:
                if seg in self._segments_:
                    self._segments_.remove(seg)
        elif segment in self._segments_:
            self._segments_.remove(segment)
        return self

    def replace(
        self,
        old_segment: TimeSegmentMixin | Sequence[TimeSegmentMixin] | Sequence[tuple[TimeSegmentMixin, TimeSegmentMixin]],
        new_segments: TimeSegmentMixin | Sequence[TimeSegmentMixin] | None = None,
        *,
        strategy: str | SegmentMerger = "error",
    ) -> MergeResult:
        """Replace one or more segments with new segment(s) using conflict resolution.

        Supports multiple calling conventions:

        1. Two arguments: old_segment(s) and new_segment(s)
           ```python
           collection.replace(old_block, new_block)
           collection.replace([old1, old2], [new1, new2])
           ```

        2. One-to-many: replace a single segment with multiple segments
           ```python
           # Replace one segment with the results of a split
           a, b = block.split(block.middle, gap="2m")
           collection.replace(block, [a, b])
           ```

        3. Single argument: sequence of (old, new) pairs (unpackable)
           ```python
           # From DiffResult.changed_blocks or MatchResult.matched_blocks
           collection.replace(diff_result.changed_blocks)
           
           # Or explicit pairs
           collection.replace([(old1, new1), (old2, new2)])
           ```

        Args:
            old_segment: Either:
                - The segment(s) to replace (when new_segments is provided)
                - A sequence of (old, new) tuples to replace (when new_segments is None)
            new_segments: A single segment or sequence of segments to replace with.
                         If None, old_segment must be a sequence of (old, new) pairs.
            strategy: Strategy for handling overlapping segments when inserting new ones:
                - "error": Raise error if new segments overlap with remaining segments (default)
                - "skip": Skip insertion if new segments overlap
                - "replace": Remove overlapping segments and insert new ones
                - "force": Insert regardless of overlaps
                - Or pass a SegmentMerger instance for custom behavior

        Returns:
            MergeResult containing information about the replacement operation

        Raises:
            ValueError: If old_segment is not in the collection

        Example:
            >>> # Replace a single segment with another
            >>> result = collection.replace(old_segment, new_segment)
            >>>
            >>> # Replace one segment with multiple (e.g., after split)
            >>> a, b = block.split(block.middle, gap="2m")
            >>> result = collection.replace(block, [a, b])
            >>>
            >>> # Replace using (old, new) pairs from diff result
            >>> additions, deletions, changes = differ.diff(match_result)
            >>> result = collection.replace(changes)
            >>>
            >>> # Replace using explicit pairs
            >>> result = collection.replace([
            ...     (old1, new1),
            ...     (old2, new2),
            ... ])
        """
        from time_segments.merging import SegmentMerger

        if isinstance(strategy, SegmentMerger):
            merger = strategy
        elif isinstance(strategy, str):
            merger = SegmentMerger(strategy=strategy)
        else:
            msg = (
                f"Invalid strategy type '{type(strategy)}'. "
                "Must be a string or SegmentMerger instance."
            )
            raise ValueError(msg)

        # Handle single argument case: sequence of (old, new) pairs
        if new_segments is None:
            # old_segment should be a sequence of (old, new) tuples
            pairs = list(old_segment)
            if not pairs:
                # Empty sequence, nothing to do
                from time_segments.merging import MergeResult
                return MergeResult(success=True, strategy_used=merger._strategy_instance.name())
            
            # Build list of (old_segs, new_segs) for merger.replace
            replacements = []
            for pair in pairs:
                old, new = pair  # Unpack the pair
                old_list = [old] if isinstance(old, TimeSegmentMixin) else list(old)
                new_list = [new] if isinstance(new, TimeSegmentMixin) else list(new)
                replacements.append((old_list, new_list))
            
            # Pass the strategy to replace so it's used for insertions
            return merger.replace(
                self._segments_, replacements, strategy=merger._strategy_instance
            )

        # Two argument case: old_segment(s) and new_segment(s)
        old_segs = (
            [old_segment]
            if isinstance(old_segment, TimeSegmentMixin)
            else list(old_segment)
        )
        new_segs = (
            [new_segments]
            if isinstance(new_segments, TimeSegmentMixin)
            else list(new_segments)
        )

        # Use merger's replace method, passing the strategy for insertions
        return merger.replace(
            self._segments_,
            [(old_segs, new_segs)],
            strategy=merger._strategy_instance,
        )

    def copy(self, *, deep: bool = True) -> Self:
        """Create a copy of the collection.

        Args:
            deep: If True, create deep copy of segments; otherwise shallow copy

        Returns:
            New collection instance
        """
        if deep:
            from copy import deepcopy

            copied_segments = [deepcopy(seg) for seg in self._segments_]
        else:
            copied_segments = self._segments_.copy()

        return self._create_new_collection(copied_segments)

    def union(self) -> Self:
        """Merge all overlapping or contiguous segments into non-overlapping ones.

        This is similar to merge_overlapping but also merges segments that touch
        (end of one equals start of another).

        Returns:
            New collection with merged segments
        """
        if self.is_empty:
            return self._create_new_collection([])

        # Sort by start time
        sorted_segs = sorted(
            self._segments_,
            key=lambda seg: seg.start if seg.start is not None else pd.Timestamp.min,
        )

        merged = []
        current = sorted_segs[0].copy()

        for seg in sorted_segs[1:]:
            if seg.start is None or seg.end is None:
                continue
            if current.end is None:
                merged.append(current)
                current = seg.copy()
                continue

            # Check if segments overlap or touch (<=  instead of <)
            if seg.start <= current.end:
                # Merge by extending current
                if seg.end is not None and seg.end > current.end:
                    current.end = seg.end
            else:
                # No overlap, save current and start new
                merged.append(current)
                current = seg.copy()

        merged.append(current)
        return self._create_new_collection(merged)

    def subtract(
        self,
        other: TimeSegmentMixin | list[TimeSegmentMixin] | Self,
        gap: pd.Timedelta | str | None = None,
    ) -> Self:
        """Subtract segments from this collection.

        Args:
            other: Segment(s) to subtract from this collection

        Returns:
            New collection with remaining segments after subtraction
        """
        # Normalize input to list
        if isinstance(other, TimeSegmentMixin):
            segments_to_subtract = [other]
        elif hasattr(other, "segments"):
            segments_to_subtract = other._segments_
        else:
            segments_to_subtract = other

        # Start with all segments
        remaining = [seg.copy() for seg in self._segments_]

        # Subtract each segment
        for sub_seg in segments_to_subtract:
            new_remaining = []
            for seg in remaining:
                # Use the segment's subtract method
                subtracted = seg.subtract(sub_seg, gap=gap)
                if not isinstance(subtracted, list):
                    subtracted = [subtracted]
                new_remaining.extend(subtracted)
            remaining = new_remaining

        return self._create_new_collection(remaining)

    def intersect(
        self,
        other: TimeSegmentMixin | list[TimeSegmentMixin] | Self,
    ) -> Self:
        """Get intersection of this collection with other segment(s).

        Args:
            other: Segment(s) to intersect with

        Returns:
            New collection with intersecting segments
        """
        # Normalize input to list
        if isinstance(other, TimeSegmentMixin):
            segments_to_intersect = [other]
        elif hasattr(other, "segments"):
            segments_to_intersect = other._segments_
        else:
            segments_to_intersect = other

        # Collect all intersections
        intersections = []
        for seg in self._segments_:
            for other_seg in segments_to_intersect:
                intersection = seg.intersect(other_seg)
                if intersection is not None:
                    intersections.append(intersection)

        return self._create_new_collection(intersections)

    def empty_spaces(self) -> Self:
        """Return the gaps between segments as a new collection.

        Returns:
            New collection containing segments representing gaps
        """
        gaps = self.find_gaps()

        # Create segments from gaps
        gap_segments = []
        for gap_start, gap_end in gaps:
            # Create a new segment (copy from first segment and modify)
            if self._segments_:
                gap_seg = self._segments_[0].copy()
                gap_seg.start = gap_start
                gap_seg.end = gap_end
                gap_segments.append(gap_seg)

        return self._create_new_collection(gap_segments)

    def drop_small_segments(
        self,
        threshold: str | pd.Timedelta = "0s",
        *,
        inplace: bool = False,
    ) -> Self:
        """Remove segments with duration smaller than threshold.

        Args:
            threshold: Minimum duration (segments below this are removed)
            inplace: If True, modify this collection; otherwise return new one

        Returns:
            Self (if inplace=True) or new collection (if inplace=False)
        """
        threshold = pd.Timedelta(threshold)

        result = self if inplace else self.copy()

        # Filter out small segments
        to_drop = [
            seg
            for seg in result._segments_
            if seg.duration is not None and seg.duration <= threshold
        ]

        result.drop(to_drop)
        return result

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the collection to a pandas DataFrame.

        Returns:
            DataFrame with columns: start, end, duration
        """
        data = []
        for i, seg in enumerate(self._segments_):
            duration = None
            if seg.start is not None and seg.end is not None:
                duration = seg.end - seg.start
            data.append(
                {
                    "id": i,
                    "start": seg.start,
                    "end": seg.end,
                    "duration": duration,
                },
            )
        return pd.DataFrame(data)

    def _create_new_collection(self, segments: list[TimeSegmentMixin]) -> Self:
        """Create a new collection instance with the given segments.

        This method should be overridden by subclasses if they need
        special initialization logic.
        """
        # Create new instance of the same type
        return self.__class__(segments)

    def __len__(self) -> int:
        """Return the number of segments in the collection."""
        return len(self._segments_)

    def __iter__(self) -> Iterator[TimeSegmentMixin]:
        """Iterate over segments in the collection."""
        return iter(self._segments_)

    def __getitem__(self, index: int) -> TimeSegmentMixin:
        """Get segment by index."""
        return self._segments_[index]

    def __repr__(self) -> str:
        """Return a string representation of the collection."""
        class_name = type(self).__name__
        count = len(self._segments_)
        return (
            f"<{class_name} with {count} segments, "
            f"total_duration={self.total_duration}>"
        )
