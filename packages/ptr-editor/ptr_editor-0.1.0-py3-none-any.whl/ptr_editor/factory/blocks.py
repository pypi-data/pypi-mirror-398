"""Factory functions for creating PTR blocks."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd  # noqa: TC002
from attrs import NOTHING, NothingType
from loguru import logger as log

from ptr_editor.core.codenames_gen import make_unique_codename_id

if TYPE_CHECKING:
    from ptr_editor.elements.attitude import ATTITUDES
    from ptr_editor.elements.blocks import ObsBlock


class ObsBlockFactory:
    """Factory for creating PTR blocks.

    It can be used as a mixin or via static methods.
    """

    @staticmethod
    def create(
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        id: str | None = None,
        *,
        duration: str | pd.Timedelta | None = None,
        attitude: ATTITUDES | str | NothingType = NOTHING,
        designer: str | None = None,
        target: str | NothingType = NOTHING,
        boresight: str | None = None,
        comment: str | list[str] | None = None,
        phase_angle: str | NothingType = NOTHING,
    ) -> ObsBlock:
        """Primary entry point to create a new ObsBlock.

        Factory function for creating observation blocks with simplified parameters.
        This function handles context management and metadata initialization.

        This function is very lickely fragile with the current implementation. 
        TODO: refactor properly.

        Args:
            start: Start time of the observation (ISO format string or pd.Timestamp).
            end: End time of the observation (ISO format string or pd.Timestamp).
            id: Observation block identifier.
            attitude: Spacecraft attitude configuration (defaults to context value).
            designer: Instrument or instrument code (e.g., "JANUS", "MAJIS", "UVS").
            target: Target body name (e.g., "Jupiter", "Europa").
            comment: Plain text comment(s) to add to metadata. Can be a single string
                or a list of strings.
            phase_angle: Phase angle value for the attitude.

        Returns:
            ObsBlock: A new observation block instance.

        Example:
            >>> from ptr_editor.factory.blocks import (
            ...     create_obs_block,
            ... )
            >>> block = create_obs_block(
            ...     start="2024-01-01T10:00:00",
            ...     end="2024-01-01T11:00:00",
            ...     designer="JANUS",
            ...     target="Jupiter",
            ...     id="OBS_001",
            ... )
        """
        from ptr_editor.context import get_defaults_config
        from ptr_editor.elements.blocks import ObsBlock

        # Get current defaults configuration
        current_config = get_defaults_config()
        current_pointing = current_config.pointing
        
        # Only pass non-NOTHING values to evolve to avoid setting defaults to NOTHING
        evolve_kwargs = {}
        if target is not NOTHING:
            evolve_kwargs["target"] = target
        if phase_angle is not NOTHING:
            evolve_kwargs["phase_angle"] = phase_angle
        if designer is not None:
            evolve_kwargs["designer"] = designer
        if attitude is not NOTHING:
            evolve_kwargs["attitude"] = attitude

        if boresight:
            evolve_kwargs["boresight"] = boresight

        # Create new pointing defaults with overrides if any
        if evolve_kwargs:
            ctx = current_pointing.evolve(**evolve_kwargs)
        else:
            ctx = current_pointing

        log.debug(
            f"Creating ObsBlock with start={start}, end={end}, "
            f"id={id}, duration={duration}, attitude={attitude}, "
            f"designer={designer}, target={target}, phase_angle={phase_angle}, "
            f"comment={comment}",
        )
        
        # Use context manager to temporarily apply the pointing defaults
        with ctx:
            block = ObsBlock(
                start=start,
                end=end,
                attitude=attitude or NOTHING,
            )

        log.debug(f"Created ObsBlock {block} with start={start}, end={end}, id={id}")

        if duration is not None:
            block.set_times_from_duration(duration, start, end)

        # this is a little messy, we need to re-set it after block creation
        # bacause when an attitude is passed to the block constructor, it
        # overrides the context attitude/boresight settings
        if boresight is not None and boresight is not NOTHING:
            block.attitude.boresight = boresight

        # same for target
        if target is not None and target is not NOTHING:
            block.attitude.target = target

        log.debug(
            f"ObsBlock times after applying duration={duration}: "
            f"start={block.start}, end={block.end}",
        )

        block.id = id or make_unique_codename_id(block)

        log.debug(f"ObsBlock ID set to {block.id}")

        if designer is not None:
            block.designer = designer

        if comment is not None:
            if isinstance(comment, str):
                block.add_comment(comment)
            elif isinstance(comment, list):
                for c in comment:
                    block.add_comment(c)

        return block
