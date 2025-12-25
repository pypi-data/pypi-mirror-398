"""Time segment interface protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pandas as pd


@runtime_checkable
class TimeSegmentInterface(Protocol):
    """Protocol defining the minimal interface for time segments.

    Any class implementing this protocol can use the TimeSegmentMixin
    to gain rich time segment functionality.

    Required attributes/properties:
    - start: pd.Timestamp | None
    - end: pd.Timestamp | None

    These can be regular attributes, properties, or attrs fields.
    The mixin will access them without modification.
    """

    start: pd.Timestamp | None
    end: pd.Timestamp | None

