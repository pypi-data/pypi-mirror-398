from __future__ import annotations

from typing import Literal

import pandas as pd
from attrs.validators import in_, optional

from attrs_xml import attr, element, element_define, time_element
from attrs_xml.core.sentinels import UNSET, _UnsetType, is_set
from ptr_editor.core.ptr_element import PtrElement

from .array import AnglesVector, AngularVelocityVector, TimesVector
from .values import Angle, TimeDelta


@element_define(defname="offsetAngles")
class OffsetAngles(PtrElement):
    """Base class for offset rotations applied to basic pointings.

    Offset rotations are optional rotations around two axes that can be applied to
    basic pointings. The offset reference axis (`offsetRefAxis`) defines, together
    with the boresight, two axes in the spacecraft frame around which the rotations
    are performed.

    The offset-y-axis is the unit vector along the cross product of boresight and
    offsetRefAxis. The offset-x-axis is defined such that offset-x-axis, offset-y-axis,
    and boresight form a right-handed orthogonal frame.

    The resulting spacecraft attitude with offset rotations is given by the basic
    pointing rotated right-handed first around the offset-x-axis by minus the y-angle,
    then rotated right-handed around the offset-y-axis by the x-angle. This convention
    ensures that positive x and y angles rotate the boresight towards the offset-x-axis
    and offset-y-axis, respectively.

    Default offsetRefAxis: SC x-axis
    Default offset angles: zero

    Attributes:
        ref (str): Offset type identifier ("OFFSET" for base class).

    See Also:
        FixedOffsetAngles: Fixed offset angles.
        RasterOffsetAngles: Raster pattern offsets.
        ScanOffsetAngles: Scanning pattern offsets.
        CustomOffsetAngles: Custom offset angle profiles.
    """

    ref: str = attr(default="OFFSET", kw_only=True)


@element_define
class CustomOffsetAngles(OffsetAngles):
    """Custom offset angles defined by rotation angles and rates at specific times.

    Allows specification of a customized path of offset angles by providing rotation
    angles and rates at certain times. The rotation angles between two times are
    defined as 3rd-order polynomials that match the angles and rates at the interval
    borders.

    Times are specified by a list of delta times relative to a start time. The first
    time is defined by the start_time plus the first delta_time in the list. All
    following delta times are cumulative deltas relative to the previous time.

    The rotation angles before the first time and after the last time correspond to
    the angles at the first and last time, respectively.

    Attributes:
        ref (Literal["custom"]): Offset type identifier. Value: "custom"
        start_time (pd.Timestamp | _UnsetType): Start time for the offset angles.
            Required field but can be left UNSET during initialization. Must be set
            before validation/serialization.
        delta_times (TimesVector): List of delta times. All entries must be positive
            (because delta times are cumulative). Must contain at least two elements.
        x_angles (AnglesVector): Rotation angles towards the offset-x-axis. Must be
            the same length as delta_times.
        x_rates (AngularVelocityVector): Rotation rates towards the offset-x-axis.
            Must be the same length as delta_times.
        y_angles (AnglesVector): Rotation angles towards the offset-y-axis. Must be
            the same length as delta_times.
        y_rates (AngularVelocityVector): Rotation rates towards the offset-y-axis.
            Must be the same length as delta_times.

    Example:
        >>> from ptr_editor.elements.offset import (
        ...     CustomOffsetAngles,
        ... )
        >>> from ptr_editor.elements.array import (
        ...     TimesVector,
        ...     AnglesVector,
        ...     AngularVelocityVector,
        ... )
        >>> import pandas as pd
        >>> custom = CustomOffsetAngles(
        ...     start_time=pd.Timestamp(
        ...         "2032-01-01T10:00:00"
        ...     ),
        ...     delta_times=TimesVector(
        ...         [0, 60],
        ...         unit="sec",
        ...     ),
        ...     x_angles=AnglesVector(
        ...         [0, 1],
        ...         unit="deg",
        ...     ),
        ...     x_rates=AngularVelocityVector(
        ...         [0, 0],
        ...         unit="deg/sec",
        ...     ),
        ...     y_angles=AnglesVector(
        ...         [0, 0.5],
        ...         unit="deg",
        ...     ),
        ...     y_rates=AngularVelocityVector(
        ...         [0, 0],
        ...         unit="deg/sec",
        ...     ),
        ... )

    Notes:
        - All angle/rate vectors must have the same length as delta_times
        - delta_times must contain at least two elements
        - Rotation angles are interpolated using 3rd-order polynomials
    """

    ref: Literal["custom"] = attr(default="custom", kw_only=False)
    #: Start time for the offset angles. Required field but can be left
    #: UNSET during initialization. Must be set before validation/serialization.
    start_time: pd.Timestamp | _UnsetType = time_element(default=UNSET)
    delta_times: TimesVector = element(factory=TimesVector)

    x_angles: AnglesVector = element(factory=AnglesVector)
    x_rates: AngularVelocityVector = element(
        factory=AngularVelocityVector,
    )
    y_angles: AnglesVector = element(factory=AnglesVector)

    y_rates: AngularVelocityVector = element(
        factory=AngularVelocityVector,
    )

    def validate_required_fields(self):
        """Validate that all required fields have been set."""
        if not is_set(self.start_time):
            msg = "start_time must be set before using this CustomOffsetAngles"
            raise ValueError(msg)


@element_define
class FixedOffsetAngles(OffsetAngles):
    """Fixed offset angles applied to basic pointing.

    Defines two fixed rotation angles applied to the spacecraft attitude. These
    angles rotate the boresight towards the offset-x and offset-y axes.

    For small offset rotation angles, the position of the rotated boresight
    projected in the plane spanned by the offset-x and y-axis can be visualized
    with positive x_angle rotating towards offset-x-axis and positive y_angle
    rotating towards offset-y-axis.

    Attributes:
        ref (Literal["fixed"]): Offset type identifier. Value: "fixed"
        x_angle (Angle): Rotation angle of the boresight towards the offset-x-axis
            (rotation around plus offset-y-axis). Defaults to 0 degrees.
        y_angle (Angle): Rotation angle of the boresight towards the offset-y-axis
            (rotation around minus offset-x-axis). Defaults to 0 degrees.

    Example:
        >>> from ptr_editor.elements.offset import (
        ...     FixedOffsetAngles,
        ... )
        >>> from ptr_editor.elements.values import (
        ...     Angle,
        ... )
        >>> fixed = FixedOffsetAngles(
        ...     x_angle=Angle(
        ...         5, "deg"
        ...     ),
        ...     y_angle=Angle(
        ...         10, "deg"
        ...     ),
        ... )
    """

    ref: Literal["fixed"] = attr(default="fixed", kw_only=True)
    x_angle: Angle = element(factory=lambda: Angle(0, "deg"))
    y_angle: Angle = element(factory=lambda: Angle(0, "deg"))


@element_define
class ScanOffsetAngles(OffsetAngles):
    """Scanning pattern offset angles.

    Defines a scan pattern where the boresight moves along lines with multiple
    scans per line. Useful for creating scanning observation patterns.

    Before the scan start time and after the last scan, a slew is performed with
    duration `border_slew_time`. Before the initial slew and after the final slew,
    the offset angles are fixed to the angles at the start of the first scan and
    the end of the last scan, respectively.

    Either `scan_time` or `scan_speed` must be provided (but not both) to define
    the scan velocity.

    Attributes:
        ref (Literal["scan"]): Offset type identifier. Value: "scan"
        start_time (pd.Timestamp | None | _UnsetType): Scan start time. Required.
        number_of_lines (int): Number of lines along which a scan is performed.
            Defaults to 1.
        number_of_scans_per_line (int): Number of scans performed per line.
            Defaults to 1.
        x_start (Angle): Rotation angle of start point of first line towards
            offset-x-axis. Defaults to 0 degrees.
        y_start (Angle): Rotation angle of start point of first line towards
            offset-y-axis. Defaults to 0 degrees.
        scan_delta (Angle): Delta angle of one scan. Defaults to 0 degrees.
        line_delta (Angle | None): Angular offset between two lines of the scan.
            Optional.
        scan_time (TimeDelta | None): Duration of one scan. Must not be provided
            if scan_speed is specified. Optional.
        scan_speed (AngularVelocityVector | None): Angular speed of a scan. Must
            not be provided if scan_time is specified. Optional.
        border_slew_time (TimeDelta | None): Slew time before first and after last
            scan to reach start angles of first scan and final angles of last scan.
            Optional.
        scan_slew_time (TimeDelta | None): Slew time between two scans in the same
            line. Optional.
        line_slew_time (TimeDelta | None): Slew time between two scans in different
            lines. Optional.
        line_axis (Literal["x", "y"]): Name of offset-axis along which the scans
            are performed. Defaults to "y".
        keep_line_dir (bool | None): Flag indicating whether the direction of the
            first scan line is kept for other lines (True) or alternated (False).
            Optional.
        keep_scan_dir (bool | None): Flag indicating whether the direction of the
            scan performed in one line is kept (True) or alternated (False). Optional.

    Example:
        >>> from ptr_editor.elements.offset import (
        ...     ScanOffsetAngles,
        ... )
        >>> from ptr_editor.elements.values import (
        ...     Angle,
        ...     TimeDelta,
        ... )
        >>> import pandas as pd
        >>> scan = ScanOffsetAngles(
        ...     start_time=pd.Timestamp(
        ...         "2032-01-01T10:00:00"
        ...     ),
        ...     number_of_lines=5,
        ...     number_of_scans_per_line=10,
        ...     x_start=Angle(
        ...         -5, "deg"
        ...     ),
        ...     y_start=Angle(
        ...         -5, "deg"
        ...     ),
        ...     scan_delta=Angle(
        ...         1, "deg"
        ...     ),
        ...     line_delta=Angle(
        ...         1, "deg"
        ...     ),
        ...     scan_time=TimeDelta(
        ...         30, "sec"
        ...     ),
        ...     line_axis="x",
        ... )

    Notes:
        - Either scan_time or scan_speed must be provided (mutually exclusive)
        - Scans do not contain slews; slews occur between scans
    """

    ref: Literal["scan"] = attr(default="scan", kw_only=False)
    start_time: pd.Timestamp | None | _UnsetType = time_element(default=UNSET)
    number_of_lines: int | None = element(default=1)
    number_of_scans_per_line: int | None = element(default=1)
    x_start: Angle | None = element(factory=lambda: Angle(0, "deg"))
    y_start: Angle | None = element(factory=lambda: Angle(0, "deg"))
    scan_delta: Angle| None = element(
        factory=lambda: Angle(0, "deg"),
    )
    line_delta: Angle | None = element(default=None)
    scan_time: TimeDelta | None = element(
        default=None,
    )
    scan_speed: AngularVelocityVector | None = element(
        default=None,
    )  # This can be used instead of scan_time
    border_slew_time: TimeDelta | None = element(
        default=None,
    )
    scan_slew_time: TimeDelta | None = element(
        default=None,
    )
    line_slew_time: TimeDelta | None = element(
        default=None,
    )

    line_axis: Literal["x", "y"] | None = element(default="y", validator=optional(in_(["x", "y"])))

    keep_line_dir: bool | None = element(default=None)

    keep_scan_dir: bool | None = element(default=None)


@element_define
class RasterOffsetAngles(OffsetAngles):
    """Raster pattern offset angles.

    Defines a raster (grid) pattern of observation points in the offset angle
    coordinate system. Points are arranged in a rectangular grid with specified
    spacing and timing parameters.

    The rotation angles before the raster start_time and after the dwell_time of
    the last raster point correspond to the angles of the first and last raster
    point, respectively.

    Attributes:
        ref (Literal["raster"]): Offset type identifier. Value: "raster"
        start_time (pd.Timestamp | None | _UnsetType): Raster start time. Required.
        x_points (int): Number of points in offset-x-direction. Defaults to 1.
        y_points (int): Number of points in offset-y-direction. Defaults to 1.
        x_start (Angle): Rotation angle of first raster point towards the offset
            x-axis. Defaults to 0 degrees.
        y_start (Angle): Rotation angle of first raster point towards the offset
            y-axis. Defaults to 0 degrees.
        x_delta (Angle | None): Delta angle towards offset x-axis between two
            raster points. Optional.
        y_delta (Angle): Delta angle towards offset y-axis between two raster
            points. Defaults to 0 degrees.
        point_slew_time (TimeDelta): Slew time between two raster points in the
            same line. Defaults to 1 minute.
        line_slew_time (TimeDelta | None): Slew time between two raster points in
            different lines. Optional.
        dwell_time (TimeDelta): Time spent at one raster point. Defaults to 1 minute.
        line_axis (Literal["x", "y"]): Name of offset-axis along which the raster
            points are connected in a line. Defaults to "y".
        keep_line_dir (bool): Flag indicating whether the direction of the first
            raster-row is kept (True) or alternated (False). Defaults to False.

    Example:
        >>> from ptr_editor.elements.offset import (
        ...     RasterOffsetAngles,
        ... )
        >>> from ptr_editor.elements.values import (
        ...     Angle,
        ...     TimeDelta,
        ... )
        >>> import pandas as pd
        >>> raster = RasterOffsetAngles(
        ...     start_time=pd.Timestamp(
        ...         "2032-01-01T10:00:00"
        ...     ),
        ...     x_points=5,
        ...     y_points=5,
        ...     x_start=Angle(
        ...         -2, "deg"
        ...     ),
        ...     y_start=Angle(
        ...         -2, "deg"
        ...     ),
        ...     x_delta=Angle(
        ...         1, "deg"
        ...     ),
        ...     y_delta=Angle(
        ...         1, "deg"
        ...     ),
        ...     point_slew_time=TimeDelta(
        ...         10, "sec"
        ...     ),
        ...     dwell_time=TimeDelta(
        ...         30, "sec"
        ...     ),
        ...     line_axis="x",
        ...     keep_line_dir=True,
        ... )

    Notes:
        - Creates a grid of (x_points * y_points) observation positions
        - line_axis determines how points are connected (row-wise or column-wise)
        - keep_line_dir controls whether alternating rows/columns reverse direction
    """

    ref: Literal["raster"] = attr(default="raster", kw_only=False)
    start_time: pd.Timestamp | None | _UnsetType = time_element(default=UNSET)
    x_points: int = element(default=1)
    y_points: int = element(default=1)
    x_start: Angle = element(factory=lambda: Angle(0, "deg"))
    y_start: Angle = element(factory=lambda: Angle(0, "deg"))
    x_delta: Angle | None = element(default=None)
    y_delta: Angle = element(factory=lambda: Angle(0, "deg"))
    point_slew_time: TimeDelta = element(
        factory=lambda: TimeDelta(1, "min"),
    )
    line_slew_time: TimeDelta | None = element(
        default=None,
    )
    dwell_time: TimeDelta = element(
        default=TimeDelta(1, "min"),
    )
    line_axis: Literal["x", "y"] | None = element(
        default="y",
        validator=optional(in_(["x", "y"])),
    )
    keep_line_dir: bool = element(default=False)


OFFSETS = CustomOffsetAngles | FixedOffsetAngles | RasterOffsetAngles | ScanOffsetAngles
