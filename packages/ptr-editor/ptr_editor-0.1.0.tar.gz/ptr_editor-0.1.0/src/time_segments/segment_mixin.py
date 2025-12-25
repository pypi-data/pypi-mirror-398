"""Time segment mixin providing rich functionality."""

from __future__ import annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Literal

import pandas as pd

if TYPE_CHECKING:
    from typing_extensions import Self

    from .interface import TimeSegmentInterface


DEFAULT_GAP = pd.Timedelta("2 minutes")


def _get_default_gap() -> pd.Timedelta:
    """Return the default gap duration.

    TODO This should reach out a configuration system in the future.
    so that the user can configure it. To be implemented later as is not trivial.
    """

    return DEFAULT_GAP


class TimeSegmentMixin:
    """
    Mixin providing rich functionality for time segments.

    Can be mixed into any class that has `start` and `end` attributes
    of type `pd.Timestamp | None`.

    Usage:
        class MySegment(TimeSegmentAccessor):
            def __init__(self, start, end):
                self.start = start
                self.end = end

        segment = MySegment(start_time, end_time)
        segment.duration
        segment.intersect(other_segment)
    """

    # Type hints for the required attributes (to be provided by the implementing class)
    start: pd.Timestamp | None
    end: pd.Timestamp | None
    id: str | int | None

    @property
    def duration(self) -> pd.Timedelta | None:
        """Return the duration of the segment."""
        if not self.start or not self.end:
            return None
        return self.end - self.start

    @duration.setter
    def duration(self, new_duration: str | pd.Timedelta) -> None:
        """Set the duration by modifying the end time.

        This implements the default behavior of keeping the start time fixed.
        To set the duration while keeping the end time fixed, use the `set_duration` method.
        """
        self.set_duration(new_duration, fixed="start")

    def set_times_from_duration(
        self,
        duration: str | pd.Timedelta,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> None:
        """Set the start and end times based on the duration and either the start or the end."""
        duration = pd.Timedelta(duration)
        if duration <= pd.Timedelta(0):
            msg = "Only positive and non-zero durations are allowed."
            raise ValueError(msg)

        if start is None and end is None:
            msg = "Either start or end time must be provided to set duration."
            raise ValueError(msg)

        if start is not None and end is not None:
            msg = "Provide only one of start or end time as reference to set duration."
            raise ValueError(msg)

        if start is not None:
            self.start = start
            self.set_duration(duration, fixed="start")

        if end is not None:
            self.end = end
            self.set_duration(duration, fixed="end")

    def set_duration(
        self, new_duration: str | pd.Timedelta, fixed: Literal["start", "end"]
    ) -> None:
        """Set the duration by keeping fixed start or end."""
        new_duration = pd.Timedelta(new_duration)
        if new_duration < pd.Timedelta(0):
            msg = "Only positive durations are allowed."
            raise ValueError(msg)

        if fixed == "start":
            if self.start is None:
                msg = "Start time is not set, cannot set duration."
                raise ValueError(msg)
            self.end = self.start + new_duration
        elif fixed == "end":
            if self.end is None:
                msg = "End time is not set, cannot set duration."
                raise ValueError(msg)
            self.start = self.end - new_duration
        else:
            msg = f"Unknown fixed parameter: {fixed}. Use 'start' or 'end'."
            raise ValueError(msg)

    @property
    def middle(self) -> pd.Timestamp | None:
        """Return the midpoint timestamp of the segment."""
        if not self.start or not self.end:
            return None
        return self.start + (self.end - self.start) / 2

    def is_valid(self) -> bool:
        """Return True if the segment has valid start and end times."""
        if self.start is None or self.end is None:
            return False
        return self.start <= self.end

    def contains(self, time: pd.Timestamp | str) -> bool:
        """Return True if the given time is within this segment."""
        if not self.is_valid():
            return False
        time = pd.Timestamp(time)
        return self.start <= time <= self.end  # type: ignore[operator]

    def intersects(self, other: TimeSegmentInterface) -> bool:
        """Check if this segment intersects with another.

        Returns True if they intersect, False otherwise.
        Equal endpoints are not considered as intersection.
        """
        if (
            self.start is None
            or self.end is None
            or other.start is None
            or other.end is None
        ):
            return False

        if self.end <= other.start or other.end <= self.start:
            return False

        return not (self.end == other.start or other.end == self.start)

    def intersect(self, other: TimeSegmentInterface) -> Self | None:
        """Return a new segment representing the intersection with another segment.

        Returns None if there is no intersection.
        """
        if not self.intersects(other):
            return None

        inters = deepcopy(self)
        # Calculate intersection boundaries
        if self.start is not None and other.start is not None:
            inters.start = max(self.start, other.start)
        if self.end is not None and other.end is not None:
            inters.end = min(self.end, other.end)
        return inters

    def split(
        self,
        time: pd.Timestamp | str | None = None,
        gap: pd.Timedelta | str | None = None,
        gap_mode: Literal["center", "before", "after"] = "center",
        *,
        delta_from_start: pd.Timedelta | str | None = None,
        delta_from_end: pd.Timedelta | str | None = None,
    ) -> list[Self]:
        """Split the segment at the given time.

        Returns a list with either one segment (if time is outside)
        or two segments.

        If gap is provided, it will create a gap of the specified duration
        between the two segments.

        gap_mode controls where the gap is placed:
        - "after": gap is placed after the split point (default)
        - "before": gap is placed before the split point
        - "center": gap is centered on the split point and both segments
          are adjusted accordingly

        """

        from .ops import split

        return split(
            self,
            time=time,
            gap=gap,
            gap_mode=gap_mode,
            delta_from_start=delta_from_start,
            delta_from_end=delta_from_end,
        )

    def subtract(
        self,
        other: TimeSegmentInterface | list[TimeSegmentInterface],
        gap: str | pd.Timedelta | None = None,
    ) -> Self | list[Self]:
        """Subtract another segment (or segments) from this one.

        Args:
            other: The segment(s) to subtract from this one
            gap: Optional gap to add around the subtracted segments.
                Defaults to DEFAULT_GAP. Can be a string or pd.Timedelta.

        Returns:
            Single remaining segment if only one remains, otherwise list of segments.
        """
        # if gap is None:
        #     gap = _get_default_gap()

        from .ops import subtract

        result = subtract(self, other, gap=gap)

        # Return single item if list has only one element
        if len(result) == 1:
            return result[0]
        return result

    def move(self, delta: str | pd.Timedelta) -> None:
        """Move the segment by a time delta."""
        time_delta = pd.Timedelta(delta)
        if self.start is not None:
            self.start = self.start + time_delta
        if self.end is not None:
            self.end = self.end + time_delta

    def move_to_time(
        self,
        time: str | pd.Timestamp,
        mode: Literal["start", "end", "middle"] = "start",
    ) -> None:
        """Move the segment to align with a specific time.

        Args:
            time: Target time to move to
            mode: "start" to align the start time, "end" to align the end time,
                or "middle" to align the middle of the segment to the given time
        """
        time = pd.Timestamp(time)
        duration = self.duration
        if duration is None:
            msg = "Cannot move segment without valid duration."
            raise ValueError(msg)

        if mode == "start":
            self.start = time
            self.end = time + duration
        elif mode == "end":
            self.end = time
            self.start = time - duration
        elif mode == "middle":
            half_duration = duration / 2
            self.start = time - half_duration
            self.end = time + half_duration
        else:
            msg = f"Unknown mode {mode}. Use 'start', 'end', or 'middle'."
            raise ValueError(msg)

    def move_after(
        self,
        other: TimeSegmentInterface,
        gap: str | pd.Timedelta | None = None,
    ) -> None:
        """Move this segment to start after another segment with a configurable gap.

        Args:
            other: The segment to move after
            gap: Time gap between the end of the other segment and the start of
                this one. Defaults to DEFAULT_GAP. Can be a string or pd.Timedelta.
        """
        if gap is None:
            gap = _get_default_gap()

        if other.end is None:
            msg = "Cannot move after a segment without an end time."
            raise ValueError(msg)

        duration = self.duration
        if duration is None:
            msg = "Cannot move segment without valid duration."
            raise ValueError(msg)

        gap_delta = pd.Timedelta(gap)
        new_start = other.end + gap_delta
        self.start = new_start
        self.end = new_start + duration

    def move_before(
        self,
        other: TimeSegmentInterface,
        gap: str | pd.Timedelta | None = None,
    ) -> None:
        """Move this segment to end before another segment with a configurable gap.

        Args:
            other: The segment to end before
            gap: Time gap between the end of this segment and the start of
                the other one. Defaults to DEFAULT_GAP. Can be a string or pd.Timedelta.
        """
        if gap is None:
            gap = _get_default_gap()

        if other.start is None:
            msg = "Cannot end before a segment without a start time."
            raise ValueError(msg)

        duration = self.duration
        if duration is None:
            msg = "Cannot move segment without valid duration."
            raise ValueError(msg)

        gap_delta = pd.Timedelta(gap)
        new_end = other.start - gap_delta
        self.end = new_end
        self.start = new_end - duration

    def end_before(
        self,
        other: TimeSegmentInterface,
        gap: str | pd.Timedelta | None = None,
        mode: Literal["resize", "move"] = "move",
    ) -> None:
        """Set this segment to end before another segment with a configurable gap.

        Args:
            other: The segment to end before
            gap: Time gap between the end of this segment and the start of
                the other one. Defaults to DEFAULT_GAP. Can be a string or pd.Timedelta.
            mode: Operation mode:
                - "move": Move the entire segment (preserving duration)
                - "resize": Resize by adjusting the end time only
        """
        if gap is None:
            gap = _get_default_gap()

        if other.start is None:
            msg = "Cannot end before a segment without a start time."
            raise ValueError(msg)

        gap_delta = pd.Timedelta(gap)
        new_end = other.start - gap_delta

        if mode == "move":
            duration = self.duration
            if duration is None:
                msg = "Cannot move segment without valid duration."
                raise ValueError(msg)
            self.end = new_end
            self.start = new_end - duration
        elif mode == "resize":
            if self.start is None:
                msg = "Cannot resize segment without a start time."
                raise ValueError(msg)
            if new_end <= self.start:
                msg = "Resulting segment would have non-positive duration."
                raise ValueError(msg)
            self.end = new_end
        else:
            msg = f"Unknown mode {mode}. Use 'move' or 'resize'."
            raise ValueError(msg)

    def start_after(
        self,
        other: TimeSegmentInterface,
        gap: str | pd.Timedelta | None = None,
        mode: Literal["resize", "move"] = "move",
    ) -> None:
        """Set this segment to start after another segment with a configurable gap.

        Args:
            other: The segment to start after
            gap: Time gap between the end of the other segment and the start of
                this one. Defaults to DEFAULT_GAP. Can be a string or pd.Timedelta.
            mode: Operation mode:
                - "move": Move the entire segment (preserving duration)
                - "resize": Resize by adjusting the start time only
        """
        if gap is None:
            gap = _get_default_gap()

        if other.end is None:
            msg = "Cannot start after a segment without an end time."
            raise ValueError(msg)

        gap_delta = pd.Timedelta(gap)
        new_start = other.end + gap_delta

        if mode == "move":
            duration = self.duration
            if duration is None:
                msg = "Cannot move segment without valid duration."
                raise ValueError(msg)
            self.start = new_start
            self.end = new_start + duration
        elif mode == "resize":
            if self.end is None:
                msg = "Cannot resize segment without an end time."
                raise ValueError(msg)
            if new_start >= self.end:
                msg = "Resulting segment would have non-positive duration."
                raise ValueError(msg)
            self.start = new_start
        else:
            msg = f"Unknown mode {mode}. Use 'move' or 'resize'."
            raise ValueError(msg)

    def align_to(
        self,
        other: TimeSegmentInterface,
        mode: Literal["all", "start", "end", "middle"] = "all",
        gap: str | pd.Timedelta | None = None,
    ) -> None:
        """Align this segment to another segment.

        Args:
            other: The segment to align to (must have start and end attributes)
            mode: Alignment mode:
                - "all": copy both start and end from other (default)
                - "start": align this segment's start to other's start
                - "end": align this segment's end to other's end
                - "middle": align this segment's middle to other's middle
            gap: Optional gap to add when aligning. Defaults to no gap.
                For start/end modes, gap is added in the direction away from
                the other segment. For middle mode, gap is ignored.
        """
        gap = pd.Timedelta(0) if gap is None else pd.Timedelta(gap)

        if mode == "all":
            self.start = other.start
            self.end = other.end
            return

        duration = self.duration
        if duration is None:
            msg = "Cannot align segment without valid duration."
            raise ValueError(msg)

        if mode == "start":
            if other.start is None:
                msg = "Cannot align to segment without start time."
                raise ValueError(msg)
            aligned_start = other.start + gap
            self.start = aligned_start
            self.end = aligned_start + duration
        elif mode == "end":
            if other.end is None:
                msg = "Cannot align to segment without end time."
                raise ValueError(msg)
            aligned_end = other.end - gap
            self.end = aligned_end
            self.start = aligned_end - duration
        elif mode == "middle":
            if other.start is None or other.end is None:
                msg = "Cannot align to segment without valid start and end times."
                raise ValueError(msg)
            # For middle mode, gap is ignored (ambiguous direction)
            other_middle = other.start + (other.end - other.start) / 2
            half_duration = duration / 2
            self.start = other_middle - half_duration
            self.end = other_middle + half_duration
        else:
            msg = f"Unknown mode {mode}. Use 'all', 'start', 'end', or 'middle'."
            raise ValueError(msg)

    def subdivide_equal_intervals(
        self,
        interval: str | pd.Timedelta,
        duration: str | pd.Timedelta,
    ) -> list[Self]:
        """Subdivide this segment into equal intervals.

        Args:
            interval: Time between the start of each sub-segment
            duration: Duration of each sub-segment

        Returns:
            List of sub-segments
        """
        if not self.is_valid():
            return []

        interval = pd.Timedelta(interval)
        duration = pd.Timedelta(duration)

        if interval <= pd.Timedelta(0):
            msg = "Interval must be positive."
            raise ValueError(msg)
        if duration <= pd.Timedelta(0):
            msg = "Duration must be positive."
            raise ValueError(msg)

        segments = []
        current_time = self.start

        while current_time < self.end:  # type: ignore[operator]
            segment = self.copy()
            segment.start = current_time
            segment.end = min(current_time + duration, self.end)  # type: ignore[arg-type,operator]
            segments.append(segment)
            current_time += interval  # type: ignore[operator]

        return segments

    def copy(self, *, deep: bool = True) -> Self:
        """Create a copy of this segment.

        Args:
            deep: If True, create a deep copy; otherwise a shallow copy
        """
        if deep:
            return deepcopy(self)
        return copy(self)

    def equals(
        self,
        other: TimeSegmentInterface,
        *,
        exclude: str | list[str] | None = None,
    ) -> bool:
        """Compare this segment with another, optionally excluding attributes.

        By default, performs a standard equality check using `==`.
        When `exclude` is provided, the specified attributes are ignored
        during comparison.

        Args:
            other: The segment to compare with
            exclude: Attribute name(s) to exclude from comparison.
                Can be a single string or list of strings.
                Common exclusions: "metadata", "id", "parent"

        Returns:
            True if segments are equal (ignoring excluded attributes)

        Example:
            >>> # Standard equality
            >>> block1.equals(block2)
            >>>
            >>> # Ignore metadata differences
            >>> block1.equals(block2, exclude="metadata")
            >>>
            >>> # Ignore multiple attributes
            >>> block1.equals(
            ...     block2,
            ...     exclude=["metadata", "id"],
            ... )
        """
        if exclude is None:
            return self == other

        # Normalize exclude to a set
        exclude_set = {exclude} if isinstance(exclude, str) else set(exclude)

        import attrs

        # Get fields, filtering out those with eq=False
        self_fields = attrs.fields(type(self))
        other_fields = attrs.fields(type(other))

        # Build dicts with only eq-participating fields
        self_dict = {
            f.name: getattr(self, f.name)
            for f in self_fields
            if f.eq and f.name not in exclude_set
        }
        other_dict = {
            f.name: getattr(other, f.name)
            for f in other_fields
            if f.eq and f.name not in exclude_set
        }

        return self_dict == other_dict

    def __repr__(self) -> str:
        """Return a string representation of the segment."""
        class_name = type(self).__name__
        return (
            f"<{self.id}> start={self.start}, end={self.end}, duration={self.duration}>"
        )

    def __lt__(self, other: TimeSegmentInterface) -> bool:
        if self.start is None or other.start is None:
            return NotImplemented

        return self.start < other.start
