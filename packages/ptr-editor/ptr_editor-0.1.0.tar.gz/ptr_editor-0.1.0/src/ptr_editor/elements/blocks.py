from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast


if TYPE_CHECKING:
    from ptr_editor.elements.timeline import Timeline


from typing import override

import pandas as pd  # noqa: TC002
from loguru import logger as log

from attrs_xml import (
    attr,
    element,
    element_define,
    time_element,
)
from ptr_editor.context.defaults import from_defaults
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.metadata import MWOLMetadata
from ptr_editor.factory.blocks import ObsBlockFactory
from ptr_editor.html import render_xml_html2
from ptr_solver import PtrSolvableMixin
from time_segments.segment_mixin import TimeSegmentMixin

# import pydantic as pd
from .attitude import ATTITUDES
from .metadata import (
    Metadata,
    Observations,
    get_block_designer,
    get_block_human_id,
    set_block_designer,
    set_block_human_id,
)


def _force_as_utc(item: pd.Timestamp | None):
    if item is None:
        return None
    if item.tz is not None:
        return item.tz_convert("UTC")
    return item.tz_localize("UTC")


@element_define(defname="block", repr=False)
class Block(PtrElement):
    ref: str = attr(default="", init=False)
    name: str | None = attr(
        default=None,
        kw_only=True,
    )  # direction can be named, e.g. to be stored in config files.

    def __repr__(self) -> str:
        return f"Block {self.name} of type {self.ref} - start={self.start}, end={self.end}, index={self.index}"

    def to_ptr(self) -> str:
        return self.to_xml(pretty=True)

    @property
    # @override
    def parent(self) -> Timeline | None:
        """Returns the parent timeline of the block, if any."""
        return cast("Timeline | None", self._parent)

    @parent.setter
    # @override
    def parent(self, value: Timeline | None) -> None:
        self._parent = cast("PtrElement | None", value)  # type: ignore

    @property
    def source_ptr(self) -> str | None:
        if self.parent:
            return self.parent.source
        return None

    @property
    def index(self) -> int | None:
        from ptr_editor.elements.timeline import Timeline

        """Returns the index of the block in the parent timeline."""
        if self.parent is None:
            log.opt(lazy=True).trace(f"Block {self.id} has no parent.")
            return None

        if not isinstance(self.parent, Timeline):
            log.warning(f"Parent of block {self.id} is not a Timeline.")
            return None

        parent: Timeline = self.parent

        if self not in parent:
            log.warning(f"Block {self.id} is not in parent's blocks.")
            return None

        return parent.index(self)

    def _find_next_block(
        self,
        block_type: BLOCKS | None = None,
        direction: Literal["forward", "backward"] = "forward",
    ) -> BLOCKS | None:
        """Returns the next block of the specified type in the timeline."""
        if self.index is None:
            log.debug("Block index is None, cannot find next block.")
            return None

        if block_type is None:
            block_type = Block

        from ptr_editor.elements.timeline import Timeline

        parent: Timeline = self.parent
        if not isinstance(parent, Timeline):
            log.debug("Parent is not a Timeline.")
            return None

        if direction == "forward":
            log.debug(
                f"Finding next block of type {block_type} after index {self.index}.",
            )
            for block in parent[self.index + 1 :]:
                if isinstance(block, block_type):
                    return block
        else:
            log.debug(
                f"Finding previous block of type {block_type} before index {self.index}.",
            )
            for block in parent[: self.index][::-1]:
                if isinstance(block, block_type):
                    return block

        log.debug(f"No next block of type {block_type} found.")
        return None

    @property
    def next_obs_block(self):
        return self._find_next_block(ObsBlock, direction="forward")

    @property
    def next_timed_block(self):
        return self._find_next_block(TimedBlock, direction="forward")

    @property
    def previous_timed_block(self):
        return self._find_next_block(TimedBlock, direction="backward")

    @property
    def previous_obs_block(self):
        return self._find_next_block(ObsBlock, direction="backward")


@element_define()
class TimedBlock(PtrSolvableMixin, TimeSegmentMixin, Block):
    start: pd.Timestamp | None = time_element(default=None, tag="startTime")
    end: pd.Timestamp | None = time_element(default=None, tag="endTime")

    def is_open(self) -> bool:
        """Returns True if the block is open-ended (no start or end time)."""
        return self.start is None or self.end is None

    def _solvable_ptr_(self) -> str:
        return self.xml


@element_define
class ObsBlock(ObsBlockFactory, TimedBlock):
    """
    Observation block representing a pointing request in a PTR timeline.

    An ObsBlock defines a time-bounded pointing request with associated attitude,
    metadata, and observation parameters. It is the primary building block for
    instrument pointing requests in timelines.

    Attributes:
        ref (Literal["OBS"]): Block type identifier, always "OBS".
        start (pd.Timestamp | None): Start time of the observation.
        end (pd.Timestamp | None): End time of the observation.
        attitude (ATTITUDES): Spacecraft attitude configuration for the observation.
            Defaults to value from pointing context.
        metadata (Metadata | None): Observation metadata including planning info
            and comments.
        designer (str | None): Instrument or instrument code associated with the
            observation (for example: "JANUS", "MAJIS", "UVS"). This field
            indicates which instrument is responsible for or designed the
            observation, and is stored in the metadata planning section.
        name (str | None): Optional human-readable name for the block. It is
            used only for naming templates and it makes a ptr block invalid if used
            in a timeline.

    Properties:
        id (str | None): Observation block identifier (read/write).
        designer (str | None): Name of the observation designer (read/write).
        observations (Observations | None): Observation planning details.
        duration (pd.Timedelta | None): Observation duration.
        index (int | None): Position of this block in the parent timeline.
        next_obs_block (ObsBlock | None): Next observation block in the timeline.
        previous_obs_block (ObsBlock | None): Previous observation block in the timeline.

    Methods:
        new: Class method to create a new ObsBlock with simplified parameters.
        solve: Solve the observation block using the PTR solver.
        add_comment: Add a plain text comment to the observation metadata.
        as_pandas: Convert block to a pandas DataFrame representation.
        to_ptr: Export block as PTR XML string.

    Examples:
        Create a new observation block with default attitude:

        >>> from ptr_editor.elements.blocks import (
        ...     ObsBlock,
        ... )
        >>> import pandas as pd
    >>> block = ObsBlock.new(
    ...     start="2024-01-01T10:00:00",
    ...     end="2024-01-01T11:00:00",
    ...     designer="JANUS",
    ...     target="Jupiter",
    ...     id="OBS_001",
    ... )
        >>> print(
        ...     block.duration
        ... )
        Timedelta('0 days 01:00:00')

        Create with specific attitude:

        >>> from ptr_editor.elements.attitude import (
        ...     TrackAttitude,
        ... )
    >>> block = ObsBlock.new(
    ...     start="2024-01-01T10:00:00",
    ...     end="2024-01-01T12:00:00",
    ...     attitude=TrackAttitude(),
    ...     designer="MAJIS",
    ... )

        Access and modify metadata:

    >>> block.id = "OBS_002"
    >>> block.designer = (
    ...     "UVS"
    ... )
    >>> block.add_comment(
    ...     "First observation of Europa"
    ... )

        Navigate timeline:

        >>> # Assuming block is in a timeline
        >>> next_block = block.next_obs_block
        >>> prev_block = block.previous_obs_block
        >>> block_position = (
        ...     block.index
        ... )

        Solve the observation:

        >>> result = block.solve()  # Returns PTR solver results

    Notes:
        - Start and end times can be provided as strings (ISO format) or pd.Timestamp objects.
        - Attitude defaults to the value from the global pointing context if not specified.
        - Metadata is automatically initialized if not provided.
        - The block must be part of a Timeline to use navigation properties
          (index, next_obs_block, previous_obs_block).
    """

    ref: Literal["OBS"] = attr(default="OBS", kw_only=True)
    attitude: ATTITUDES = element(factory=from_defaults("pointing.attitude"))
    metadata: Metadata | None = element(factory=Metadata)

    # def __deepcopy__(self, memo) -> ObsBlock:
    #     # call parent deepcopy but renew the id
    #     from copy import deepcopy
    #     new_instance = super().__deepcopy__(memo)
    #     if self.id is not None:
    #         new_instance.renew_id()
    #     return new_instance

    def renew_id(self) -> None:
        """Generates and assigns a new unique ID to the observation block."""
        from ptr_editor.core.codenames_gen import make_unique_codename_id

        new_id = make_unique_codename_id(self)
        self.id = new_id
        log.info(f"Assigned new ID to ObsBlock: {new_id}")

    def add_comment(self, comment: str) -> None:
        """Adds a plain text comment to the observation metadata.

        Shortcut for adding comments to the metadata.
        """
        if self.metadata is None:
            self.metadata = Metadata()

        self.metadata.add_comment(comment)

    def __repr__(self) -> str:
        # Get the default attrs repr
        attrs_repr = super().__repr__()
        # Remove the closing parenthesis and add duration
        attrs_repr = attrs_repr[:-1]
        duration_str = str(self.duration) if self.duration is not None else "None"
        des = self.designer if self.designer else "None"
        id = self.id if self.id else "None"
        return f"<ObsBlock {id}, duration={duration_str}, start={self.start}, end={self.end}, designer={des}, id={id})"

    def as_pandas(self) -> pd.Series:
        from ptr_editor.io.simplified_converter2 import tabletize_block

        """Returns a pandas Series representation of the ObsBlock."""
        return tabletize_block(self)

    def _repr_html_(self) -> str:
        from ptr_editor.io.simplified_converter2 import tabletize_block

        properties = tabletize_block(self)
        return render_xml_html2(self.xml, properties.to_dict())

    def copy(self, id: str = "", renew_id: bool = False) -> ObsBlock:
        """Create a copy of the ObsBlock, optionally renewing the ID.

        Args:
            id: New ID to assign (currently unused)
            renew_id: If True and the block has an ID, generate a new unique ID
        """
        new_instance = super().copy()
        if renew_id and self.id is not None:
            new_instance.renew_id()

        if id:
            new_instance.id = id

        return new_instance

    @property
    def id(self) -> str | None:
        """Returns the ID of the observation block."""
        if self.metadata is None:
            return None
        return get_block_human_id(self.metadata.planning)

    @id.setter
    def id(self, value: str) -> None:
        """Sets the ID of the observation block."""
        if self.metadata is None:
            log.warning(
                f"Could not set ID to {value} - metadata structure not initialized",
            )
            return
        set_block_human_id(self.metadata.planning, value)

    @property
    def obs_ids(self) -> list[str]:
        """Returns observation IDs from metadata planning section.
        
        Delegates to the Metadata class for safe access to nested observations.
        
        Returns:
            list[str]: List of observation IDs, empty if not available.
        """
        if self.metadata is None:
            return []
        return self.metadata.get_obs_ids()

    @property
    def designer(self) -> str | None:
        """Returns the designer of the observation."""
        if self.metadata is None:
            log.debug("ObsBlock has no metadata.")
            return None
        return get_block_designer(self.metadata.planning)

    @designer.setter
    def designer(self, value: str) -> None:
        """Set the designer of the observation."""
        if self.metadata is None:
            log.warning(
                f"Could not set designer to {value} - metadata structure not initialized",
            )
            return
        set_block_designer(self.metadata.planning, value)

    @property
    def observations(self) -> Observations | None:
        if self.metadata is None:
            log.debug("ObsBlock has no metadata.")
            return None

        if self.metadata.planning is None:
            log.debug("ObsBlock metadata has no planning info.")
            return None

        return self.metadata.planning.observations


@element_define(repr=False)
class SlewBlock(Block):
    """Attitude slew block for transitions between observation blocks.

    An attitude slew is implemented by inserting a slew block in the PTR. A slew
    block must be placed in between two observation blocks. The duration of slew
    blocks is defined implicitly by the end time of the previous observation block
    and the start time of the following observation block.

    Slew blocks do not have explicit start and end times - the slew duration is
    automatically determined by the gap between adjacent observation blocks.

    Unlike ObsBlocks, SlewBlocks do not have id properties, metadata, or explicit
    timing attributes. They serve purely as transition markers between observations.

    Attributes:
        ref (Literal["SLEW"]): Block type identifier. Value: "SLEW"

    Example:
        >>> from ptr_editor import (
        ...     ObsBlock,
        ...     SlewBlock,
        ...     Timeline,
        ... )
        >>> # Create two observation blocks with a slew between them
        >>> obs1 = ObsBlock(
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )
        >>> slew = SlewBlock()
        >>> obs2 = ObsBlock(
        ...     start="2032-01-01T02:00:00",  # Gap = slew duration (1 hour)
        ...     end="2032-01-01T03:00:00",
        ... )
        >>> timeline = Timeline(
        ...     blocks=[
        ...         obs1,
        ...         slew,
        ...         obs2,
        ...     ]
        ... )

    Note:
        - Slew blocks must be positioned between observation blocks
        - The slew duration is the time gap between the end of the previous
          observation and the start of the next observation
        - Slew blocks do not have start/end time attributes (returns None)
        - Slew blocks do not have id properties or metadata like ObsBlocks
    """

    ref: Literal["SLEW"] = attr(default="SLEW", kw_only=True)

    @property
    def id(self) -> str:
        """Slew blocks do not have IDs. Keeping for compatibility."""
        return "SLEW"

    @property
    def start(self) -> pd.Timestamp | None:
        """Slew Blocks do not have start times. Keeping for compatibility."""
        return None

    @property
    def end(self) -> pd.Timestamp | None:
        """Slew Blocks do not have end times. Keeping for compatibility."""
        return None


@element_define(repr=False)
class DownlinkBlock(TimedBlock):
    """Downlink block for data transmission periods.

    Downlink blocks represent periods when the spacecraft is transmitting data
    to ground stations. These blocks have explicit start and end times.

    Attributes:
        ref (Literal["DL"]): Block type identifier. Value: "DL"
        start (pd.Timestamp | None): Start time of the downlink period.
        end (pd.Timestamp | None): End time of the downlink period.
        metadata (Metadata | None): Block metadata including planning information.

    Example:
        >>> from ptr_editor import (
        ...     DownlinkBlock,
        ... )
        >>> dl = DownlinkBlock(
        ...     start="2032-01-01T10:00:00",
        ...     end="2032-01-01T11:00:00",
        ... )
    """

    ref: Literal["DL"] = attr(default="DL", kw_only=True)
    metadata: Metadata | None = element(factory=Metadata)


@element_define(repr=False)
class MNAVBlock(TimedBlock):
    """Navigation maintenance block using NAVCAM without wheel offloading.

    MNAV blocks are navigation slots that nominally use the NAVCAM and do not
    contain a wheel offloading (WOL). These blocks need to be scheduled frequently
    and do not contain slews. Therefore, before and after these blocks, slews are
    required (or another maintenance block that contains a slew).

    The attitude in MNAV slots is defined as for an observation block. The basic
    pointing is either specified in the PTS or the default is used.

    Each MNAV block contains metadata with:
    - mntBlockNumber: Integer ID (four digits with leading zero)
    - vstpNumber: Optional VSTP number
    - positionError: Optional position error
    - hgaRequest: Optional HGA request (can be supplied by SGS if not in PTS)
    - comment: Optional comments

    Attributes:
        ref (Literal["MNAV"]): Maintenance block type. Value: "MNAV"
        start (pd.Timestamp | None): Start time of the navigation slot.
        end (pd.Timestamp | None): End time of the navigation slot.
        metadata (Metadata | None): Maintenance block metadata including
            mntBlockNumber and optional hgaRequest.

    Example:
        >>> from ptr_editor import (
        ...     MNAVBlock,
        ... )
        >>> mnav = MNAVBlock(
        ...     start="2032-01-01T12:00:00",
        ...     end="2032-01-01T12:30:00",
        ... )

    Note:
        - MNAV blocks do not contain slews; slews are required before/after
        - Navigation blocks can be followed by observation or other maintenance blocks
        - Duration and parameters must match those defined in the PTS
    """

    ref: Literal["MNAV"] = attr(default="MNAV", kw_only=True)
    metadata: Metadata | None = element(factory=Metadata)

    @property
    def id(self) -> str:
        """Slew blocks do not have IDs. Keeping for compatibility."""
        return "MNAV"


@element_define(repr=False)
class MWOLBlock(TimedBlock):
    """Wheel offloading maintenance block.

    MWOL blocks are maintenance slots for performing wheel offloading (WOL)
    maneuvers. These blocks contain slews, so no additional slews are needed
    before or after them. Navigation or observation blocks can be scheduled
    directly before/after MWOL blocks.

    Each MWOL block contains metadata with:
    - mntBlockNumber: Integer ID (four digits with leading zero)
    - vstpNumber: Optional VSTP number
    - positionError: Optional position error
    - comment: Optional comments

    Note: hgaRequest is only allowed for navigation blocks (MNAV, MWNV, MWAC),
    not for MWOL blocks.

    Attributes:
        ref (Literal["MWOL"]): Maintenance block type. Value: "MWOL"
        start (pd.Timestamp | None): Start time of the wheel offloading.
        end (pd.Timestamp | None): End time of the wheel offloading.
        metadata (MWOLMetadata | None): MWOL-specific metadata.

    Example:
        >>> from ptr_editor import (
        ...     MWOLBlock,
        ... )
        >>> mwol = MWOLBlock(
        ...     start="2032-01-01T06:00:00",
        ...     end="2032-01-01T07:00:00",
        ... )

    Note:
        - MWOL blocks contain slews; no additional slews needed before/after
        - Can be followed directly by observation or navigation blocks
        - Duration and parameters must match those defined in the PTS
    """

    ref: Literal["MWOL"] = attr(default="MWOL", kw_only=True)
    metadata: MWOLMetadata | None = element(factory=MWOLMetadata)

    @property
    def id(self) -> str:
        """Slew blocks do not have IDs. Keeping for compatibility."""
        return "MWOL"


@element_define(repr=False)
class MTCMBlock(TimedBlock):
    """Trajectory correction maneuver maintenance block (MOCM).

    MTCM (formerly MOCM) blocks are maintenance slots for performing delta-V
    maneuvers and trajectory corrections. These blocks contain slews, so no
    additional slews are needed before or after them. Navigation or observation
    blocks can be scheduled directly before/after MTCM blocks.

    Each MTCM block contains metadata with:
    - mntBlockNumber: Integer ID (four digits with leading zero)
    - vstpNumber: Optional VSTP number
    - positionError: Optional position error
    - comment: Optional comments

    Note: hgaRequest is only allowed for navigation blocks (MNAV, MWNV, MWAC),
    not for MTCM blocks.

    Attributes:
        ref (Literal["MTCM"]): Maintenance block type. Value: "MTCM"
        start (pd.Timestamp | None): Start time of the maneuver.
        end (pd.Timestamp | None): End time of the maneuver.
        metadata (Metadata | None): Maintenance block metadata.

    Example:
        >>> from ptr_editor import (
        ...     MTCMBlock,
        ... )
        >>> mtcm = MTCMBlock(
        ...     start="2032-01-01T08:00:00",
        ...     end="2032-01-01T09:00:00",
        ... )

    Note:
        - MTCM blocks contain slews; no additional slews needed before/after
        - Can be followed directly by observation or navigation blocks
        - Duration and parameters must match those defined in the PTS
        - Used for dV maneuvers and trajectory corrections
    """

    ref: Literal["MTCM"] = attr(default="MTCM", kw_only=True)
    metadata: Metadata | None = element(factory=Metadata)

    @property
    def id(self) -> str:
        """Slew blocks do not have IDs. Keeping for compatibility."""
        return "MTCM"


BLOCKS = ObsBlock | SlewBlock | DownlinkBlock | MNAVBlock | MWOLBlock | MTCMBlock
