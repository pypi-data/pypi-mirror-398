from __future__ import annotations

import os
from collections.abc import Sequence
from copy import deepcopy
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Self

import pandas as pd
from loguru import logger as log

from attrs_xml import attr, element, element_define
from attrs_xml.core.base_element import _set_child_parent
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.diffing import DiffResult
from ptr_editor.diffing.matcher import BlockMatcher, MatchResult
from ptr_editor.elements.attitude import ATTITUDES
from ptr_editor.elements.blocks import BLOCKS, ObsBlock, SlewBlock, TimedBlock
from ptr_solver.solvable_mixin import PtrSolvableMixin
from time_segments.merging import MergeResult, SegmentMerger
from time_segments.segments_collection_mixin import SegmentsCollectionMixin

if TYPE_CHECKING:
    from ptr_editor.elements.doc import Prm

from attrs import define, field


@define
class TimelineSourceMetadata:
    """Describes the source of a timeline, e.g., the file it was loaded from."""

    source_file: Path | None = field(
        default=None, converter=lambda x: Path(x) if x is not None else None,
    )

    def __repr__(self) -> str:
        if self.source_file:
            return f"TimelineSourceMetadata(file='{self.source_file.name}', path='{self.source_file.parent}')"
        return "TimelineSourceMetadata(file=None)"

    def __fspath__(self) -> str:
        """Return the file system path representation.

        This allows TimelineSourceMetadata to be used wherever a path is expected.
        """
        if self.source_file is None:
            raise ValueError("No source file associated with this metadata")
        return str(self.source_file)

    @classmethod
    def from_file(cls, file: os.PathLike | None) -> TimelineSourceMetadata:
        """Create TimelineSourceMetadata from a file path."""
        return cls(source_file=file)

    def has_file(self) -> bool:
        """Check if a source file is associated with the timeline."""
        return self.source_file is not None

    @property
    def source_name(self) -> str | None:
        """Return the source file name without path or extension, if available."""
        if self.source_file:
            return self.source_file.name
        return None


@element_define(repr=False)
class Timeline(PtrElement, PtrSolvableMixin, SegmentsCollectionMixin):
    """Spacecraft attitude timeline defined by a list of pointing blocks.

    The SC attitude timeline is defined by a list of pointing blocks. Each pointing
    block is represented by a child element block. Each of these blocks defines the
    SC attitude for an interval of time.

    The pointing blocks must be in order of increasing time. Pointing blocks must
    not overlap in time.

    There are four types of pointing blocks:
    1. **Observation blocks** (ObsBlock): Used to implement scientific observations
    2. **GSEP blocks**: Ground Station Event Predictions
    3. **Slew blocks** (SlewBlock): Attitude transitions between observations
    4. **Maintenance blocks**: Used to perform Orbit-Correction-Manoeuvre (OCM),
       Wheel-off-Loading (WOL), slews, or navigation slots

    In between each two observation or GSEP blocks, there shall be a slew or a
    maintenance slot that contains slews (these are MOCM, MSLW and MWOL).

    **Parent Reference Management:**
    
    When adding blocks to a timeline (via append, insert, etc.), the timeline
    automatically sets itself as the parent of each block. If a block already has
    a different parent, it is copied before being added to avoid conflicts.
    
    Filtering operations (obs_blocks, filter_by_designer, etc.) return a new Timeline
    containing references to the filtered blocks by default. The blocks in the
    filtered timeline maintain their parent reference to the original timeline.
    To get independent copies with parent references aligned to the new timeline,
    use the filter() method with copy=True or call .copy() on the filtered result.

    Attributes:
        frame (str): Reference frame for the timeline. Default: "SC" (spacecraft frame)
        _blocks (list[BLOCKS]): Internal list of blocks. Access via Timeline methods
            to maintain proper parent references.

    Example:
        >>> from ptr_editor import (
        ...     Timeline,
        ...     ObsBlock,
        ...     SlewBlock,
        ... )
        >>> # Create observation blocks
        >>> obs1 = ObsBlock(
        ...     start="2032-01-01T00:00:00",
        ...     end="2032-01-01T01:00:00",
        ... )
        >>> obs2 = ObsBlock(
        ...     start="2032-01-01T02:00:00",
        ...     end="2032-01-01T03:00:00",
        ... )
        >>> # Create timeline with automatic slew insertion
        >>> timeline = Timeline(
        ...     blocks=[
        ...         obs1,
        ...         obs2,
        ...     ]
        ... )
        >>> timeline.insert_slews()  # Adds slew between obs1 and obs2
        >>> print(len(timeline))
        3  # obs1, slew, obs2

        >>> # Access blocks
        >>> for (
        ...     block
        ... ) in timeline:
        ...     print(
        ...         f"{block.ref}: {block.start} - {block.end}"
        ...     )

        >>> # Filter to observation blocks (returns references)
        >>> obs_blocks = timeline.obs_blocks
        >>> print(len(obs_blocks))
        2
        >>> # Blocks still reference original timeline
        >>> obs_blocks[0].parent is timeline
        True

        >>> # Filter with copies (parent aligned to filtered timeline)
        >>> copied_obs = timeline.filter(lambda b: isinstance(b, ObsBlock), copy=True)
        >>> copied_obs[0].parent is copied_obs
        True

    Note:
        - Pointing blocks must be in chronological order (increasing time)
        - Pointing blocks must not overlap in time
        - Slews or maintenance blocks with slews must separate observation/GSEP blocks
        - Use insert_slews() to automatically add slew blocks where needed
        - Parent references are automatically maintained when adding blocks
        - Blocks with different parents are copied before insertion to avoid conflicts
    """

    #: Reference frame for the timeline. Default is "SC" (spacecraft frame).
    frame: str = attr(default="SC", kw_only=True)
    #: blocks is the actual container. I do not want to expose it directly to avoid
    #: users messing with it and breaking parent references, etc. Access via methods
    #: of the parent Timeline class.
    _blocks: list[BLOCKS] = element(factory=list, tag="block")

    # keep_slews: bool = element(default=False, kw_only=True, cattrs_omit=True)

    #: Source file path, only set if loaded from a PTR file
    source: TimelineSourceMetadata | None = element(
        factory=TimelineSourceMetadata,
        kw_only=True,
        init=False,
        cattrs_omit=True,
        eq=False,
    )

    def _create_new_collection(self, segments: list[BLOCKS]) -> Self:
        """Create a new Timeline containing references to the given segments.

        This is called by filter operations from SegmentsCollectionMixin.
        Returns a new Timeline with block references (not copies), maintaining
        their original parent references.
        """
        return Timeline._create_filtered(segments, frame=self.frame)

    @classmethod
    def from_file(cls, file: os.PathLike | str, *, drop_slews=True) -> Timeline:
        """Load a Timeline from a PTR file."""
        from ptr_editor.io import read_ptr

        file_ = Path(file)  # ensure Path object

        tml = read_ptr(file_, drop_slews=drop_slews)

        return tml

    def to_file(self, file: os.PathLike | str, *, insert_slews=True) -> None:
        """Save the Timeline to a PTR file."""
        from ptr_editor.io import save_ptr

        file_ = Path(file)  # ensure Path object

        if insert_slews:
            tml = self.copy()
            tml.insert_slews()

        prm = tml.as_prm()
        save_ptr(prm, file_)

    @property
    def source_name(self) -> str | None:
        """Return the source file name without path or extension, if available."""
        return self.source.source_name if self.source else None

    @classmethod
    def _create_filtered(cls, blocks: list[BLOCKS], frame: str) -> Timeline:
        """Create a Timeline with block references without modifying parent.
        
        This creates a new Timeline containing references to the given blocks,
        without modifying their parent references. This is used by filtering
        operations to return references to blocks.
        """
        instance = cls.__new__(cls)
        instance.frame = frame
        instance._blocks = blocks  # Direct assignment, bypasses parent setting
        instance.source = TimelineSourceMetadata()
        return instance

    @property
    def _segments_(self) -> list[BLOCKS]:  # type: ignore
        """Return the list of blocks as "_segments_" to support SegmentsCollectionMixin."""
        return self._blocks

    def _solvable_ptr_(self) -> str:
        """Serialize the timeline to PTR XML for solving."""
        return self.as_prm().xml

    def as_prm(self) -> Prm:
        from ptr_editor.elements.doc import Prm

        """Convert the timeline to a Prm object for any further use as ptr. timeline is copied."""
        prm = Prm()
        prm.timeline = self

        return prm

    def append(self, block: BLOCKS) -> Self:
        """Append a block at the end of the timeline.

        If the block already has a different parent (not self), it makes a copy of the
        block before appending to avoid conflicts. The block's parent reference is then
        set to this timeline.

        It does not handle the time ordering of the blocks, but blocks can be sorted later
        using the sort() method.

        Args:
            block: The block to append. Will be copied if it has a different parent.
        """
        if block.parent is not None and block.parent is not self:
            log.warning("Block already has a different parent. Making a copy.")
            block = block.copy()

        block.parent = self
        self._blocks.append(block)

        return self


    def extend(self, blocks: Sequence[BLOCKS]) -> Self:
        """Extend the timeline by appending multiple blocks.

        If any block already has a different parent (not self), it makes a copy of the
        block before appending to avoid conflicts. Each block's parent reference is then
        set to this timeline.

        It does not handle the time ordering of the blocks, but blocks can be sorted later
        using the sort() method.

        Args:
            blocks: Sequence of blocks to append. Each will be copied if it has a different parent.
        """
        for block in blocks:
            self.append(block)

        return self

    def match(
        self, other: Timeline, matcher: BlockMatcher | None = None,
    ) -> MatchResult:
        if not matcher:
            from ptr_editor.diffing.matcher import make_robust_matcher

            matcher = make_robust_matcher()

        return matcher.match(self, other)

    def diff(
        self, other: Timeline, match_result: MatchResult | None = None,
    ) -> DiffResult:
        from ptr_editor.diffing.timeline_differ_simple import make_timeline_differ

        if not match_result:
            match_result = self.match(other)
        differ = make_timeline_differ(
            include_attributes=[
                "attitude",
                "metadata",
                "attitude.phase_angle",
                "designer",
            ],
        )
        return differ.diff(match_result)

    def drop_slews(self) -> None:
        """Remove all SlewBlock instances from the timeline.

        Also clears the parent reference on removed slew blocks.
        """
        slews_to_remove = [b for b in self._blocks if isinstance(b, SlewBlock)]
        for slew in slews_to_remove:
            slew.parent = None
        self._blocks = list(
            filter(lambda block: not isinstance(block, SlewBlock), self._blocks),
        )

    def drop(self, block: BLOCKS | list[BLOCKS]) -> Self:
        """Remove a block or list of blocks from the timeline.

        This method clears the parent reference on removed blocks.

        Args:
            block: Single block or list of blocks to remove

        Returns:
            Self for method chaining
        """
        blocks_to_drop = [block] if not isinstance(block, list) else block
        for blk in blocks_to_drop:
            if blk in self._blocks:
                blk.parent = None
        return super().drop(block)

    def remove(
        self,
        block: BLOCKS | Sequence[BLOCKS],
    ) -> MergeResult:
        """Remove one or more blocks from the timeline.

        Args:
            block: The block(s) to remove. Can be a single block or a sequence.

        Returns:
            MergeResult containing information about the removal operation

        Raises:
            ValueError: If block is not in the timeline

        Example:
            >>> # Remove a single block
            >>> result = (
            ...     timeline.remove(
            ...         block
            ...     )
            ... )
            >>>
            >>> # Remove multiple blocks (e.g., deletions from diff)
            >>> (
            ...     additions,
            ...     deletions,
            ...     changes,
            ... ) = timeline.diff(
            ...     incoming
            ... )
            >>> result = (
            ...     timeline.remove(
            ...         deletions
            ...     )
            ... )
        """
        from time_segments.merging import DeleteAction, MergeResult

        blocks_to_remove = [block] if not isinstance(block, Sequence) else list(block)
        actions = []
        removed = []

        for blk in blocks_to_remove:
            if blk not in self._blocks:
                msg = f"Block {blk} not found in timeline"
                raise ValueError(msg)
            blk.parent = None  # Remove parent reference
            self._blocks.remove(blk)
            removed.append(blk)
            actions.append(DeleteAction(segment=blk, reason="removed from timeline"))

        return MergeResult(
            success=True,
            actions=actions,
            segments_removed=removed,
            strategy_used="direct",
        )

    def insert(
        self,
        segment: TimedBlock | list[TimedBlock],
        *,
        strategy: Literal[
            "id_safe",
            "designer_safe",
            "error",
            "skip",
            "replace",
            "force",
        ]
        | SegmentMerger = "id_safe",
    ) -> MergeResult:
        """Insert one or more blocks into the timeline with conflict resolution.

        Args:
            segment: The block(s) to insert. Can be a single block or a list of blocks.
            strategy: Strategy for handling overlapping segments:
                - "id_safe": Only insert if IDs match existing overlapping blocks (default)
                - "designer_safe": Only insert if designer matches existing overlapping blocks
                - "error": Raise error if block overlaps with existing blocks
                - "skip": Skip insertion if block overlaps with existing blocks
                - "replace": Remove overlapping blocks and insert new one
                - "force": Insert regardless of overlaps
                - Or pass a SegmentMerger instance for custom behavior

        Returns:
            MergeResult containing information about the insertion operation

        Example:
            >>> # Insert a single block
            >>> result = (
            ...     timeline.insert(
            ...         new_block
            ...     )
            ... )
            >>>
            >>> # Insert multiple blocks
            >>> result = (
            ...     timeline.insert(
            ...         [
            ...             block1,
            ...             block2,
            ...             block3,
            ...         ]
            ...     )
            ... )
            >>>
            >>> # Use strict mode - fail on overlap
            >>> result = timeline.insert(
            ...     block,
            ...     strategy="error",
            ... )
            >>>
            >>> # Force insert regardless of overlaps
            >>> result = timeline.insert(
            ...     block,
            ...     strategy="force",
            ... )
        """
        # Copy blocks that have a different parent before inserting
        if isinstance(segment, list):
            segments_to_insert = []
            for seg in segment:
                if seg.parent is not None and seg.parent is not self:
                    log.debug(f"Block {seg.id if hasattr(seg, 'id') else seg} has different parent, creating a copy")
                    seg = seg.copy(renew_id=False)
                segments_to_insert.append(seg)
            segment = segments_to_insert
        else:
            if segment.parent is not None and segment.parent is not self:
                log.debug(f"Block {segment.id if hasattr(segment, 'id') else segment} has different parent, creating a copy")
                segment = segment.copy(renew_id=False)
        
        result = super().insert(
            segment,
            strategy=strategy,
        )

        # Set parent on added segments
        for seg in result.segments_added:
            _set_child_parent(seg, self)

        # Clear parent on removed segments
        for seg in result.segments_removed:
            if hasattr(seg, "parent"):
                seg.parent = None

        return result

    def reset_parents(
        self,
        mode: Literal["force", "copy", "skip", "error"] = "copy",
    ) -> None:
        """Reset the parent reference of all contained blocks to this timeline.

        This method ensures all blocks in the timeline have their parent reference
        correctly set to this timeline instance. The behavior depends on the mode
        selected. This is particularly useful after loading from files, manually
        manipulating the block list, or when working with filtered timelines where
        you want to update parent references.

        Args:
            mode: How to handle blocks that already have a parent:
                - "copy": (default) Set parent for blocks without one. If a block has
                  a different parent (not self), copy it first then set parent.
                  Blocks already belonging to this timeline are left untouched.
                - "force": Unconditionally set parent=self for ALL blocks without
                  copying. Use with caution as this breaks parent references in
                  other timelines.
                - "skip": Only set parent for blocks with parent=None. Skip blocks
                  that already have any parent.
                - "error": Raise ValueError if any block has a different parent
                  (not self and not None).

        Raises:
            ValueError: If mode='error' and any block has a different parent.

        Example:
            >>> # After filtering, make blocks belong to filtered timeline
            >>> obs = timeline.obs_blocks
            >>> obs.reset_parents(mode="copy")  # Copies blocks with different parent
            >>> 
            >>> # Force all blocks to have this timeline as parent
            >>> timeline.reset_parents(mode="force")  # No copying, just reassign
            >>> 
            >>> # Only set parent for orphaned blocks
            >>> timeline.reset_parents(mode="skip")
            >>> 
            >>> # Strict mode - fail if conflicts exist
            >>> timeline.reset_parents(mode="error")
        """
        updated_blocks = []
        for i, block in enumerate(self._blocks):
            # Check if block has a different parent
            has_different_parent = block.parent is not None and block.parent is not self

            if mode == "error":
                if has_different_parent:
                    msg = (
                        f"Block {i} already has a different parent. "
                        f"Cannot reset parent in 'error' mode."
                    )
                    raise ValueError(msg)
                block.parent = self

            elif mode == "skip":
                if not has_different_parent:
                    block.parent = self

            elif mode == "copy":
                # Copy only if different parent; don't copy blocks already in this timeline
                if block.parent is None:
                    # No parent, just set it
                    block.parent = self
                elif has_different_parent:
                    # Has a different parent, copy then set
                    log.debug(f"Block {i} has different parent, creating a copy")
                    block = block.copy(renew_id=False)
                    block.parent = self
                # else: already has this timeline as parent, do nothing

            elif mode == "force":
                # Force all blocks to have this parent,
                if has_different_parent:
                    log.debug(f"Block {i} has different parent, creating a copy")
                    block.parent = self

            updated_blocks.append(block)

        # Update the blocks list in case any were copied
        self._blocks = updated_blocks

    def replace(
        self,
        old_segment: (
            TimedBlock | Sequence[TimedBlock] | Sequence[tuple[TimedBlock, TimedBlock]]
        ),
        new_segments: TimedBlock | Sequence[TimedBlock] | None = None,
        *,
        strategy: Literal[
            "id_safe",
            "designer_safe",
            "error",
            "skip",
            "replace",
            "force",
        ]
        | SegmentMerger = "id_safe",
    ) -> MergeResult:
        """Replace one or more blocks in the timeline with new block(s).

        Supports two calling conventions:

        1. Two arguments: old_block(s) and new_block(s)
           ```python
           timeline.replace(
               old_block,
               new_block,
           )
           timeline.replace(
               [old1, old2],
               [new1, new2],
           )
           ```

        2. Single argument: sequence of (old, new) pairs (unpackable)
           ```python
           # From DiffResult.changed_blocks
           (
               additions,
               deletions,
               changes,
           ) = timeline.diff(
               other
           )
           timeline.replace(
               changes
           )

           # Or explicit pairs
           timeline.replace(
               [
                   (
                       old1,
                       new1,
                   ),
                   (
                       old2,
                       new2,
                   ),
               ]
           )
           ```

        Args:
            old_segment: Either:
                - The block(s) to replace (when new_segments is provided)
                - A sequence of (old, new) tuples to replace (when new_segments is None)
            new_segments: A single block or sequence of blocks to replace with.
                         If None, old_segment must be a sequence of (old, new) pairs.
            strategy: Strategy for handling overlapping segments when inserting new ones:
                - "id_safe": Only replace if IDs match (default for Timeline)
                - "designer_safe": Only replace if designer matches
                - "error": Raise error if new segments overlap with remaining segments
                - "skip": Skip insertion if new segments overlap
                - "replace": Remove overlapping segments and insert new ones
                - "force": Insert regardless of overlaps
                - Or pass a SegmentMerger instance for custom behavior

        Returns:
            MergeResult containing information about the replacement operation

        Example:
            >>> # Replace a single block
            >>> result = timeline.replace(
            ...     old_block,
            ...     new_block,
            ... )
            >>>
            >>> # Apply changes from diff result
            >>> (
            ...     additions,
            ...     deletions,
            ...     changes,
            ... ) = timeline.diff(
            ...     incoming_timeline
            ... )
            >>> result = timeline.replace(
            ...     changes
            ... )
        """
        result = super().replace(
            old_segment,
            new_segments,
            strategy=strategy,
        )

        # Set parent on added segments
        for seg in result.segments_added:
            _set_child_parent(seg, self)

        # Clear parent on removed segments
        for seg in result.segments_removed:
            if hasattr(seg, "parent"):
                seg.parent = None

        return result

    def insert_slews(self) -> None:
        """Ensure that a SlewBlock is inserted between consecutive TimedBlock instances.

        This method iterates through the timeline and inserts SlewBlock instances
        wherever two consecutive TimedBlock instances are found without an intervening
        SlewBlock.
        """
        self.drop_slews()  # First, remove existing slews

        # Insert slews in place, iterating backwards to avoid index shifting
        i = len(self._blocks) - 1
        while i > 0:
            current_block = self._blocks[i]
            prev_block = self._blocks[i - 1]

            # Check if both blocks are TimedBlock instances
            if isinstance(prev_block, TimedBlock) and isinstance(
                current_block, TimedBlock,
            ):
                # Insert a SlewBlock between them
                slew = SlewBlock()
                slew.parent = self
                self._blocks.insert(i, slew)
                log.debug(
                    f"Inserted SlewBlock between block {i - 1} "
                    f"(ends {prev_block.end}) and block {i} "
                    f"(starts {current_block.start})",
                )
            i -= 1

    @property
    def id(self) -> str:
        """Return a unique identifier for the timeline based on its source.
        if no source is available, use the object's id() just to have something unique.
        """
        if self.source_name:
            return self.source_name
        return f"{id(self)}"

    def __repr__(self) -> str:
        return f"Timeline<{self.id}>(frame={self.frame}, blocks_count={len(self._blocks)}, start={self.start}, end={self.end})"

    def _repr_html_(self) -> str:
        """Return a rich HTML representation for Jupyter notebooks."""
        # Count different block types
        obs_count = len(self.obs_blocks)

        slew_count = len(self.slew_blocks)
        timed_count = len(self.timed_blocks)

        # Check for overlaps using SegmentsCollectionMixin
        has_overlaps = self.obs_blocks.has_overlaps()
        if has_overlaps:
            num_overlaps = len(self.obs_blocks.find_overlaps())
            overlap_info = (
                f'<span style="color: #d32f2f;">⚠ {num_overlaps} overlap(s)</span>'
            )
        else:
            overlap_info = '<span style="color: #388e3c;">✓ No overlaps</span>'

        # Check time ordering using SegmentsCollectionMixin
        is_ordered = self.is_sorted
        order_info = (
            '<span style="color: #388e3c;">✓ Ordered</span>'
            if is_ordered
            else '<span style="color: #d32f2f;">⚠ Not ordered</span>'
        )

        # Check for unique IDs
        ids = [b.id for b in self.obs_blocks if hasattr(b, "id") and b.id]
        has_unique_ids = len(ids) == len(set(ids))
        ids_info = (
            '<span style="color: #388e3c;">✓ Unique IDs</span>'
            if has_unique_ids
            else f'<span style="color: #d32f2f;">⚠ {len(ids) - len(set(ids))} duplicate ID(s)</span>'
        )

        # Build header with timeline statistics
        header = f"""
        <div style="margin-bottom: 15px; padding: 8px 0; border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);">
            <strong>Timeline {self.id}</strong>
            <div style="margin-top: 8px; font-size: 0.9em;">
                <span style="margin-right: 15px;">Total: {len(self._blocks)}</span>
                <span style="margin-right: 15px;">Obs: {obs_count}</span>
                <span style="margin-right: 15px;">Slew: {slew_count}</span>
                <span style="margin-right: 15px;">Timed: {timed_count}</span>
                <span style="margin-right: 15px;">Frame: {self.frame}</span>
            </div>
            <div style="margin-top: 4px; font-size: 0.9em;">
                <span style="margin-right: 15px;">Start: {self.start if self.start else "N/A"}</span>
                <span style="margin-right: 15px;">End: {self.end if self.end else "N/A"}</span>
            </div>
            <div style="margin-top: 4px; font-size: 0.9em;">
                <span style="margin-right: 15px;">{overlap_info}</span>
                <span style="margin-right: 15px;">{order_info}</span>
                <span>{ids_info}</span>
            </div>
        </div>
        """

        # Combine header with the DataFrame HTML
        return header + self.as_pandas()._repr_html_()

    @property
    def obs_blocks(self) -> Timeline[ObsBlock]:
        """Return a new Timeline containing references to observation blocks.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        filtered_blocks = [
            block for block in self._blocks if isinstance(block, ObsBlock)
        ]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    @property
    def timed_blocks(self) -> Timeline[TimedBlock]:
        """Return a new Timeline containing references to timed blocks.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        filtered_blocks = [
            block for block in self._blocks if isinstance(block, TimedBlock)
        ]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    @property
    def slew_blocks(self) -> Timeline[SlewBlock]:
        """Return a new Timeline containing references to slew blocks.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        filtered_blocks = [
            block for block in self._blocks if isinstance(block, SlewBlock)
        ]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    @property
    def nonslew_blocks(self) -> Timeline[BLOCKS]:
        """Return a new Timeline containing references to all non-slew blocks.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        filtered_blocks = [
            block for block in self._blocks if not isinstance(block, SlewBlock)
        ]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    @property
    def with_designer_blocks(self) -> Timeline[BLOCKS]:
        """Return a new Timeline containing references to blocks with a designer specified.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        def has_designer(block: BLOCKS) -> bool:
            return hasattr(block, "designer") and block.designer.strip() != ""

        filtered_blocks = [block for block in self._blocks if has_designer(block)]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    @property
    def without_designer_blocks(self) -> Timeline[BLOCKS]:
        """Return a new Timeline containing references to blocks without a designer.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        def lacks_designer(block: BLOCKS) -> bool:
            return not (
                hasattr(block, "designer")
                and isinstance(block.designer, str)
                and block.designer.strip() != ""
            )

        filtered_blocks = [block for block in self._blocks if lacks_designer(block)]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    def blocks_by_type(self, type: str | BLOCKS) -> Timeline[BLOCKS]:
        """Return a new Timeline containing references to blocks of a specific type.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        def is_type(block: BLOCKS) -> bool:
            if isinstance(type, str):
                return block.element_type == type
            return isinstance(block, type)

        filtered_blocks = [block for block in self._blocks if is_type(block)]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    def filter_by_designer(self, designer: str) -> Timeline:
        """Return a new Timeline containing references to blocks from a specific designer.
        
        The returned Timeline contains the same block objects (references), not copies.
        Blocks maintain their parent reference to the original timeline.
        To get independent copies, call .copy() on the result.
        """
        filtered_blocks = [
            block
            for block in self.with_designer_blocks
            if block.designer.strip() == designer.strip()
        ]
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    def filter_by_obs_id(self, pattern: str | list[str], *, copy: bool = False) -> Timeline:
        """Return a new Timeline containing blocks with obs_ids matching the pattern(s).
        
        Supports fnmatch-style pattern matching for flexible obs_id filtering:
        - '*' matches everything
        - '?' matches any single character
        - '[seq]' matches any character in seq
        - '[!seq]' matches any character not in seq
        
        Args:
            pattern: A single obs_id pattern or list of patterns to match against.
                     Uses fnmatch for Unix shell-style wildcards.
            copy: If False (default), return references to blocks (blocks keep their
                  original parent). If True, return copies of blocks with parent set
                  to the new timeline.
        
        Returns:
            A new Timeline containing blocks whose obs_ids match any of the patterns.
        
        Example:
            >>> # Find all JANUS observations
            >>> janus_obs = timeline.filter_by_obs_id("JANUS_*")
            >>> 
            >>> # Find multiple instruments
            >>> multi = timeline.filter_by_obs_id(["JANUS_*", "MAJIS_*"])
            >>> 
            >>> # Get independent copies
            >>> copies = timeline.filter_by_obs_id("OBS_*", copy=True)
        """
        patterns = pattern if isinstance(pattern, list) else [pattern]
        
        def matches_any_obs_id(block: BLOCKS) -> bool:
            """Check if block has any obs_id matching the patterns."""
            if not isinstance(block, ObsBlock):
                return False
            
            obs_ids = block.obs_ids
            if not obs_ids:
                return False
            
            for obs_id in obs_ids:
                for pat in patterns:
                    if fnmatch(obs_id, pat):
                        return True
            return False
        
        filtered_blocks = [block for block in self._blocks if matches_any_obs_id(block)]
        
        if copy:
            # Create copies and set parent to new timeline
            result = Timeline(frame=self.frame)
            for block in filtered_blocks:
                copied_block = block.copy(renew_id=False)
                copied_block.parent = result
                result._blocks.append(copied_block)
            return result
        
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    def filter(
        self,
        predicate: callable,
        *,
        copy: bool = False,
    ) -> Timeline[BLOCKS]:
        """Filter blocks using a custom predicate function.

        Args:
            predicate: A callable that takes a block and returns True to include it
            copy: If False (default), return references to blocks (blocks keep their
                  original parent). If True, return copies of blocks with parent set
                  to the new timeline.

        Returns:
            A new Timeline containing the filtered blocks

        Example:
            >>> # Filter by custom condition (references)
            >>> long_blocks = timeline.filter(
            ...     lambda b: b.duration.total_seconds() > 3600
            ... )
            >>> 
            >>> # Filter and copy blocks
            >>> copied = timeline.filter(
            ...     lambda b: b.designer == "JANUS",
            ...     copy=True
            ... )
        """
        filtered_blocks = [block for block in self._blocks if predicate(block)]
        
        if copy:
            # Create copies and set parent to new timeline
            result = Timeline(frame=self.frame)
            for block in filtered_blocks:
                copied_block = block.copy(renew_id=False)
                copied_block.parent = result
                result._blocks.append(copied_block)
            return result
        
        # Return references (blocks keep original parent)
        return Timeline._create_filtered(filtered_blocks, frame=self.frame)

    def find_by_designer(self, designer: str) -> BLOCKS | None:
        """Find the first block with the specified designer.

        Args:
            designer: The designer name to search for

        Returns:
            The block with the matching designer, or None if not found

        Raises:
            ValueError: If multiple blocks with the same designer are found

        Example:
            >>> block = timeline.find_by_designer(
            ...     "MAJIS"
            ... )
            >>> if block:
            ...     print(
            ...         f"Found: {block.start} - {block.end}"
            ...     )
        """
        matching_blocks = [
            block
            for block in self.with_designer_blocks
            if block.designer.strip() == designer.strip()
        ]

        if len(matching_blocks) > 1:
            msg = f"Multiple blocks found with designer '{designer}'. Found {len(matching_blocks)} blocks. Use filter_by_designer instead."
            raise ValueError(msg)

        return matching_blocks[0] if matching_blocks else None

    def append_attitude(
        self,
        start: pd.Timestamp | str,
        end: pd.Timestamp | str,
        attitude: ATTITUDES,
    ) -> ObsBlock:
        from ptr_editor import ObsBlock

        if not isinstance(attitude, ATTITUDES):
            raise TypeError("attitude must be an instance of ATTITUDES")

        """Add an attitude block to the timeline."""
        new_block = ObsBlock(start=start, end=end, attitude=attitude.copy())

        self.append(new_block)
        return new_block

    def append_slew(self) -> None:
        """Append a slew block to the timeline.

        This is a convenience method to add a SlewBlock at the end of the timeline.
        """
        slew = SlewBlock()
        slew.parent = self
        self._blocks.append(slew)

    # Implement essential container dunders for core list-like behavior
    def __len__(self):
        return len(self._blocks)

    def __getitem__(self, index):
        # If it's a slice, return a new Timeline with block references
        if isinstance(index, slice):
            result = self._blocks[index]
            return Timeline._create_filtered(result, frame=self.frame)
        # if it is an int, return the block at that index
        if isinstance(index, int):
            return self._blocks[index]
        # If it's a string, treat it as an ID lookup
        if isinstance(index, str):
            result = self.find_by_id(index)
            if result is None:
                msg = f"No block found with id '{index}'"
                raise KeyError(msg)
            return result
        return self._blocks[index]

    def __setitem__(self, index, value):
        self._blocks[index] = value

    def __delitem__(self, index):
        del self._blocks[index]

    def __iter__(self):
        return iter(self._blocks)

    def index(self, block: BLOCKS) -> int:
        """Return the index of a block in the timeline."""
        return self._blocks.index(block)

    def _ipython_key_completions_(self) -> list[str]:
        """Provide autocomplete suggestions for block IDs in IPython/Jupyter.

        This enables tab completion for string-based indexing like:
        timeline["OBS_<TAB>"] will show all block IDs starting with "OBS_"

        Returns:
            List of all block IDs that can be used with timeline[id]
        """
        return [
            str(block.id) for block in self._blocks if hasattr(block, "id") and block.id
        ]

    def __copy__(self) -> Timeline:

        new_instance = deepcopy(self)

        return new_instance

    # def clone(self) -> Self:
    #     """Create a deep copy of the timeline, without parent references."""
    #     from copy import deepcopy

    #     new_instance = deepcopy(self)

    #     return new_instance

    def as_pandas(self, *, attrs: list[str] | None = None) -> pd.DataFrame:
        """Convert the timeline to a pandas DataFrame for analysis.

        Columns are ordered with id, start, end, designer appearing first (if present),
        followed by all other columns in their natural order.

        Args:
            attrs: Optional list of additional attribute names to extract from blocks.
                Common attributes: ["id", "designer"]

        Returns:
            pd.DataFrame with blocks as rows and attributes as columns.

        Example:
            >>> df = timeline.as_pandas(
            ...     attrs=[
            ...         "id",
            ...         "designer",
            ...         "target",
            ...     ]
            ... )
        """
        from ptr_editor.io.simplified_converter2 import tabletize_block

        # Default attributes to extract if not specified
        if attrs is None:
            attrs = ["id", "designer"]

        data = []
        for block in self._blocks:
            series = tabletize_block(block, attrs=attrs)
            data.append(series)

        # Priority columns are already handled by tabletize_block
        return pd.DataFrame(data).reset_index(drop=True)

    def plot(self, hover_cols=["id", "designer", "start", "end"], **kwargs):
        from time_segments.plot import plot

        return plot(self, hover_cols=hover_cols, **kwargs)
