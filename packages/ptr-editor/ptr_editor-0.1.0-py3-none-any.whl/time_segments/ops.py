"""Standalone time segment operations.

This module provides all time segment operations as standalone functions
that operate on objects implementing the TimeSegmentInterface protocol.
"""

from __future__ import annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Literal, TypeVar

import pandas as pd

if TYPE_CHECKING:
    from .interface import TimeSegmentInterface
    from .segment_mixin import TimeSegmentMixin 

T = TypeVar("T", bound="TimeSegmentMixin")



def _calculate_split_time(
    segment: TimeSegmentMixin,
    time: pd.Timestamp | str | None,
    delta_from_start: pd.Timedelta | str | None,
    delta_from_end: pd.Timedelta | str | None,
) -> pd.Timestamp:
    """Calculate the split time from various input formats."""
    if delta_from_start is not None:
        if segment.start is None:
            msg = "Cannot split from start: segment has no start time"
            raise ValueError(msg)
        delta = pd.Timedelta(delta_from_start)
        duration = segment.duration
        if duration is not None and delta > duration:
            msg = (
                f"delta_from_start ({delta}) exceeds "
                f"segment duration ({duration})"
            )
            raise ValueError(msg)
        return segment.start + delta

    if delta_from_end is not None:
        if segment.end is None:
            msg = "Cannot split from end: segment has no end time"
            raise ValueError(msg)
        delta = pd.Timedelta(delta_from_end)
        duration = segment.duration
        if duration is not None and delta > duration:
            msg = (
                f"delta_from_end ({delta}) exceeds "
                f"segment duration ({duration})"
            )
            raise ValueError(msg)
        return segment.end - delta

    # time parameter provided - should not be None at this point
    if time is None:
        msg = "time parameter cannot be None"
        raise ValueError(msg)
    return pd.Timestamp(time)


def _apply_gap_to_segments(
    first: T,
    second: T,
    split_time: pd.Timestamp,
    gap: pd.Timedelta | str | None,
    gap_mode: str,
) -> tuple[T, T]:
    """Apply gap between split segments based on gap_mode."""
    if gap is None:
        first.end = split_time
        second.start = split_time
        return first, second

    gap_delta = pd.Timedelta(gap)

    if gap_mode == "after":
        first.end = split_time
        second.start = split_time + gap_delta
    elif gap_mode == "before":
        first.end = split_time - gap_delta
        second.start = split_time
    elif gap_mode == "center":
        half_gap = gap_delta / 2
        first.end = split_time - half_gap
        second.start = split_time + half_gap
    else:
        msg = f"Unknown gap_mode: {gap_mode}"
        raise ValueError(msg)

    return first, second


def split(
    segment: T,
    time: pd.Timestamp | str | None = None,
    gap: pd.Timedelta | str | None = None,
    gap_mode: Literal["center", "before", "after"] = "center",
    *,
    delta_from_start: pd.Timedelta | str | None = None,
    delta_from_end: pd.Timedelta | str | None = None,
) -> list[T]:
    """Split the segment at the given time or at a delta from start/end.

    Returns a list with either one segment (if time is outside)
    or two segments.

    Args:
        segment: The segment to split
        time: Explicit timestamp to split at (mutually exclusive with deltas)
        gap: Optional gap duration between the two segments
        gap_mode: Controls where the gap is placed:
            - "after": gap is placed after the split point
            - "before": gap is placed before the split point
            - "center": gap is centered on the split point
        delta_from_start: Split at this duration from segment start
            (mutually exclusive with time and delta_from_end)
        delta_from_end: Split at this duration before segment end
            (mutually exclusive with time and delta_from_start)

    Returns:
        List with one or two segments depending on whether split occurred

    Raises:
        ValueError: If multiple split specifications are provided or if
            delta exceeds segment duration

    Examples:
        >>> split(segment, time="2024-01-01T12:00:00")
        >>> split(segment, delta_from_start="1h")
        >>> split(segment, delta_from_end="30min", gap="5min")
    """
    # Validate mutually exclusive parameters
    split_specs = sum([
        time is not None,
        delta_from_start is not None,
        delta_from_end is not None,
    ])

    if split_specs == 0:
        msg = "Must provide one of: time, delta_from_start, or delta_from_end"
        raise ValueError(msg)

    if split_specs > 1:
        msg = (
            "Only one of time, delta_from_start, or "
            "delta_from_end can be specified"
        )
        raise ValueError(msg)

    # Calculate split time
    split_time = _calculate_split_time(
        segment, time, delta_from_start, delta_from_end
    )

    # Check if split time is within segment bounds
    if not (
        segment.start is not None
        and segment.end is not None
        and segment.start < split_time < segment.end
    ):
        return [deepcopy(segment)]

    # Split the segment
    first = deepcopy(segment)
    second = deepcopy(segment)
    first, second = _apply_gap_to_segments(
        first,
        second,
        split_time,
        gap,
        gap_mode,
    )

    return [first, second]


def subtract(
    segment: T,
    other: TimeSegmentMixin | list[TimeSegmentMixin],
    gap: pd.Timedelta | str | None = None,
) -> list[T]:
    """Subtract another segment (or segments) from this one.

    Args:
        segment: The segment to subtract from
        other: The segment(s) to subtract
        gap: Optional gap to add around the subtracted segments.
            This expands the subtraction area by the gap amount.
            If None, no gap is applied (unlike the mixin method which uses default gap).

    Returns:
        List of remaining segments after subtraction.
    """

    if gap is None:
        gap = pd.Timedelta(0)

    if not isinstance(other, list):
        other = [other]

    remaining = [deepcopy(segment)]

    for sub in other:
        new_remaining = []
        for seg in remaining:
            # Apply gap expansion if specified
            if gap is not None:
                gap_delta = pd.Timedelta(gap)
                expanded_start = (
                    (sub.start - gap_delta) if sub.start is not None else None
                )
                expanded_end = (
                    (sub.end + gap_delta) if sub.end is not None else None
                )
            else:
                expanded_start = sub.start
                expanded_end = sub.end

            # Skip if either segment is invalid or they don't overlap
            if (
                not seg.is_valid()
                or expanded_start is None
                or expanded_end is None
                or expanded_start > expanded_end
                or seg.end is None
                or seg.start is None
                or seg.end <= expanded_start
                or seg.start >= expanded_end
            ):
                new_remaining.append(seg)
            else:
                # left part
                if seg.start is not None and seg.start < expanded_start:
                    left = deepcopy(seg)
                    left.end = expanded_start
                    new_remaining.append(left)
                # right part
                if seg.end is not None and seg.end > expanded_end:
                    right = deepcopy(seg)
                    right.start = expanded_end
                    new_remaining.append(right)
        remaining = new_remaining

    return remaining


