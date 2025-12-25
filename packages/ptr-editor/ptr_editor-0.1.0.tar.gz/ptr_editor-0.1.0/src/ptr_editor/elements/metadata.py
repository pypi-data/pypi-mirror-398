# import pydantic as pd
import json
from typing import Any, Literal

import pandas as pd
from attrs import NOTHING
from loguru import logger as log

from attrs_xml import attr, element, element_define, text
from ptr_editor.context import from_defaults
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.attitude import time_element
from ptr_editor.elements.values import Angle, TimeDelta


@element_define
class SolarArrays(PtrElement):
    """Solar array configuration for the spacecraft.

    Attributes:
        fixed_rotation_angle: The fixed rotation angle of the solar arrays relative
            to the spacecraft body frame, expressed in degrees.
    """

    fixed_rotation_angle: Angle = element(factory=lambda: Angle(0, units="deg"))


@element_define
class PlanningSegmentation(PtrElement):
    """Planning segmentation defines time boundaries for observation planning.

    This class represents a time segment within the mission planning timeline,
    with optional descriptive information.

    Attributes:
        start: Start timestamp of the planning segment.
        end: End timestamp of the planning segment.
        definition: Optional descriptive text defining this planning segment.
    """

    start: pd.Timestamp | None = time_element(default=None)
    end: pd.Timestamp | None = time_element(default=None)
    definition: str | None = element(
        default=None, converter=lambda x: str(x) if x is not None else None
    )


@element_define
class ObservationORB17(PtrElement):
    """Observation metadata from ORB17 format (legacy).

    This class represents the observation structure used in the ORB17 planning format.
    It is maintained for backward compatibility with older PTR files.

    Attributes:
        definition: The observation definition or identifier.
        type: The observation type (PRIME, RIDER, or DESIGNER).
        unit: Instrument unit identifier (for compatibility).
        target: The observation target (e.g., planet name, region).
        start_delta: Optional time delta from the block start time.
        end_delta: Optional time delta from the block end time.
        comments: List of optional comments associated with the observation.
        start_time: Absolute start time of the observation.
        end_time: Absolute end time of the observation.
    """

    definition: str | None = element()
    type: (
        Literal["PRIME", "RIDER", "DESIGNER"]
        # | list[Literal["PRIME", "RIDER", "DESIGNER"]]
    ) = element(
        default="PRIME",
    )

    unit: str | None = element(default=None)
    target: str | None = element(default=None)
    start_delta: pd.Timedelta | None = element(default=None)
    end_delta: pd.Timedelta | None = element(default=None)
    comments: list[str] | None = element(default=None, tag="comment")
    start_time: pd.Timestamp | None = element(default=None)
    end_time: pd.Timestamp | None = element(default=None)

    @property
    def obs_id(self) -> str | None:
        """Returns the obs_id associated with the observation.

        Future-compatibility property to align with newer Observation class.

        The obs_id is derived from the definition field.
        If the definition is not set, returns None.

        Returns:
            str: The obs_id of the observation.
        """
        return self.definition

    @obs_id.setter
    def obs_id(self, value: str) -> None:
        """Sets the obs_id associated with the observation.

        Future-compatibility property to align with newer Observation class.

        The obs_id is derived from the definition field.

        Args:
            value (str): The obs_id value to set.
        """
        self.definition = value


@element_define
class Observation(PtrElement):
    """Observation metadata for a single observation within a planning block.

    This class represents a single observation in the current (post-ORB17) format.
    It includes all necessary information to identify and schedule an observation.

    Attributes:
        obs_id: The observation identifier (unique within the block).
        instrument: The instrument unit performing the observation.
        type: The observation type (PRIME or RIDER).
        target: The observation target (e.g., planet name, region).
        start_delta: Optional time delta from the block start time.
        end_delta: Optional time delta from the block end time.
        comments: List of optional comments associated with the observation.
        start_time: Absolute start time of the observation.
        end_time: Absolute end time of the observation.
    """

    obs_id: str | None = element(tag="obs_id", tag_aliases=['obsId'])
    instrument: str | None = element()
    type: Literal["PRIME", "RIDER"] = element(
        default=None,
    )

    target: str | None = element(default=None)
    start_delta: pd.Timedelta | None = element(default=None)
    end_delta: pd.Timedelta | None = element(default=None)
    comments: list[str] | None = element(default=None, tag="comment")
    start_time: pd.Timestamp | None = time_element(default=None)
    end_time: pd.Timestamp | None = time_element(default=None)

    @property
    def unit(self) -> str:
        """Returns the unit associated with the observation.

        Back-compatibility property.

        The unit is derived from the instrument field.
        If the instrument is not set, returns an empty string.

        Returns:
            str: The unit of the observation.
        """
        return self.instrument if self.instrument else ""


OBS = Observation | ObservationORB17


@element_define
class Observations(PtrElement):
    """Container for a collection of observations within a planning block.

    This class manages a list of observations and provides properties to filter
    observations by designer and observation type.

    Attributes:
        designer: The name of the instrument unit acting as the pointing designer
            for this block. Used to identify designer-controlled observations.
        observations: List of observation objects (can be either Observation or
            ObservationORB17 instances for format compatibility).
    """

    designer: str | None = attr(default=None)
    observations: list[OBS] = element(factory=list, tag="observation")

    @property
    def designer_observations(self) -> list[OBS]:
        """Returns all observations where unit == designer."""
        if not self.designer:
            return []
        return [
            obs
            for obs in self.observations
            if obs.unit and obs.unit.strip().lower() == self.designer.strip().lower()
        ]

    @property
    def designer_prime_observations(self) -> list[OBS]:
        """Returns all PRIME observations where unit == designer."""
        return [
            obs
            for obs in self.designer_observations
            if (isinstance(obs.type, str) and obs.type.strip().lower() == "prime")
            or (isinstance(obs.type, list) and "PRIME" in obs.type)
        ]


@element_define
class PlanningORB17(PtrElement):
    """Planning metadata for a block.
    Not used! keep it as a record
    Notice that we are currently hosting both old and new block ID logic.

    This should become two different classes in the future that will be clearly separated.
    Cattrs will take care of the serialization details.
    """

    reset_wheel_momentum: bool | None = attr(default=None)
    is_maintenance: bool | None = attr(default=None)
    has_internal_slews: bool | None = attr(default=None)
    allow_attitude: bool | None = attr(default=None)
    allow_hga_request: bool | None = attr(default=None)
    origin: str | None = element(default=None)
    int_slew_duration_before: TimeDelta | None = element(default=None)
    int_slew_duration_after: TimeDelta | None = element(default=None)
    segmentation: PlanningSegmentation | None = element(factory=PlanningSegmentation)
    observations: ObservationORB17 | None = element(factory=ObservationORB17)


@element_define
class Planning(PtrElement):
    """Planning metadata for a block.
    Notice that we are currently hosting both old and new block ID logic.

    This should become two different classes in the future that will be clearly separated.
    Cattrs will take care of the serialization details.
    """

    ## new items introduced after orb17
    block_id: str | None = element(default=None, tag="block_id", tag_aliases=['blockId'])
    designer: str | None = element(factory=from_defaults("pointing.designer"))
    status: Literal["BASELINE", "DRAFT", "IN-PROGRESS", "FINAL", "FROZEN"] | None = (
        element(default=None)
    )

    # common attributes
    reset_wheel_momentum: bool | None = attr(default=None)
    is_maintenance: bool | None = attr(default=None)
    has_internal_slews: bool | None = attr(default=None)
    allow_attitude: bool | None = attr(default=None)
    allow_hga_request: bool | None = attr(default=None)
    origin: str | None = element(default=None)
    int_slew_duration_before: TimeDelta | None = element(default=None)
    int_slew_duration_after: TimeDelta | None = element(default=None)
    segmentation: PlanningSegmentation | None = element(factory=PlanningSegmentation)
    observations: Observations | None = element(factory=Observations)


@element_define
class Metadata(PtrElement):
    """Top-level metadata container for a planning block.

    This class aggregates all metadata information for a planning block,
    including planning constraints, mission-related comments, and spacecraft
    configuration like solar array orientation. It also provides dict-like
    access for flexible key-value storage via comments.

    Attributes:
        planning: Planning metadata including block ID, designer, status,
            and observations.
        comments: List of optional comments associated with the block.
            Also used for key-value metadata storage in "key=value" format.
        solar_arrays: Solar array configuration for the spacecraft.
    """

    planning: Planning | None = element(factory=Planning)
    comments: list[str] | None = element(factory=list, tag="comment")
    solar_arrays: SolarArrays | None = element(default=None)

    # Reserved attribute names that cannot be used as dict keys
    _RESERVED_KEYS = {"planning", "comments", "solar_arrays", "id"}

    def to_dict(self) -> dict:
        """Convert Metadata to a dictionary representation.

        Returns:
            dict: Dictionary representation of the Metadata.
        """
        return {**self}

    def clear_observations(self, *, designer: bool = False) -> None:
        """Clears all observations from the metadata.

        This method can optionally reset the designer field to None.
        """
        if self.planning is not None:
            self.planning.observations.designer = None
            if designer:
                self.planning.observations.observations.clear()

    def __getitem__(self, key: str):
        """
        Get a value from metadata using dict-like access.

        Values are automatically deserialized from JSON, supporting any JSON-compatible type
        (str, int, float, bool, list, dict, None).

        Args:
            key: The key to retrieve

        Returns:
            The deserialized value associated with the key

        Raises:
            KeyError: If the key is not found
            ValueError: If the key is a reserved attribute name
        """
        if key in self._RESERVED_KEYS:
            raise ValueError(
                f"Cannot use '{key}' as a metadata key - it's a reserved attribute name"
            )

        if not self.comments:
            raise KeyError(key)

        # Look for "key=value" pattern in comments
        prefix = f"{key}="
        for comment in self.comments:
            if comment.startswith(prefix):
                # Extract value after "key="
                json_str = comment[len(prefix) :].strip()
                # Always parse as JSON to support any type
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    log.debug(
                        f"Failed to parse metadata value for key '{key}' as JSON. "
                        f"Returning raw string. Value: {json_str}"
                    )
                    return json_str

        raise KeyError(key)

    def __setitem__(self, key: str, value) -> None:
        """
        Set a value in metadata using dict-like access.

        The key-value pair is stored as a comment in the format "key=value".
        Values are automatically serialized to JSON, supporting any JSON-compatible type
        (str, int, float, bool, list, dict, None).

        If the key already exists, its value is updated.

        Args:
            key: The key to set
            value: The value to associate with the key (any JSON-serializable type)

        Raises:
            ValueError: If the key is a reserved attribute name or contains '='
            TypeError: If the value is not JSON-serializable
        """
        if key in self._RESERVED_KEYS:
            raise ValueError(
                f"Cannot use '{key}' as a metadata key - it's a reserved attribute name"
            )

        if "=" in key:
            raise ValueError("Metadata keys cannot contain '=' character")

        # Always serialize to JSON to support any type consistently
        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise TypeError(
                f"Value for key '{key}' is not JSON-serializable: {e}"
            ) from e

        if self.comments is None:
            self.comments = []

        # Check if key already exists and update it
        prefix = f"{key}="
        for i, comment in enumerate(self.comments):
            if comment.startswith(prefix):
                self.comments[i] = f"{key}={json_value}"
                return

        # Key doesn't exist, add new comment
        self.comments.append(f"{key}={json_value}")

    def __delitem__(self, key: str) -> None:
        """
        Delete a key-value pair from metadata.

        Args:
            key: The key to delete

        Raises:
            KeyError: If the key is not found
            ValueError: If the key is a reserved attribute name
        """
        if key in self._RESERVED_KEYS:
            raise ValueError(
                f"Cannot use '{key}' as a metadata key - it's a reserved attribute name"
            )

        if not self.comments:
            raise KeyError(key)

        prefix = f"{key}="
        for i, comment in enumerate(self.comments):
            if comment.startswith(prefix):
                del self.comments[i]
                return

        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in metadata.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        if key in self._RESERVED_KEYS:
            return False

        if not self.comments:
            return False

        prefix = f"{key}="
        return any(comment.startswith(prefix) for comment in self.comments)

    def get(self, key: str, default=None) -> Any:
        """
        Get a value from metadata with a default fallback.

        Values are automatically deserialized from JSON.

        Args:
            key: The key to retrieve
            default: Default value to return if key is not found

        Returns:
            The deserialized value associated with the key, or default if not found
        """
        try:
            return self[key]
        except (KeyError, ValueError):
            return default

    def keys(self) -> list[str]:
        """
        Get all keys from metadata stored as key=value comments.

        Returns:
            List of keys
        """
        if not self.comments:
            return []

        keys = []
        for comment in self.comments:
            if "=" in comment:
                key = comment.split("=", 1)[0]
                if key not in self._RESERVED_KEYS:
                    keys.append(key)
        return keys

    def values(self) -> list[Any]:
        """
        Get all values from metadata stored as key=value comments.

        Values are automatically deserialized from JSON.

        Returns:
            List of values
        """
        if not self.comments:
            return []

        values = []
        for comment in self.comments:
            if "=" in comment:
                key, json_str = comment.split("=", 1)
                if key not in self._RESERVED_KEYS:
                    try:
                        value = json.loads(json_str.strip())
                    except json.JSONDecodeError:
                        value = json_str.strip()
                    values.append(value)
        return values

    def items(self) -> list[tuple[str, Any]]:
        """
        Get all key-value pairs from metadata.

        Values are automatically deserialized from JSON.

        Returns:
            List of (key, value) tuples
        """
        if not self.comments:
            return []

        items = []
        for comment in self.comments:
            if "=" in comment:
                key, json_str = comment.split("=", 1)
                if key not in self._RESERVED_KEYS:
                    try:
                        value = json.loads(json_str.strip())
                    except json.JSONDecodeError:
                        value = json_str.strip()
                    items.append((key, value))
        return items

    def update(self, other: dict | None = None, **kwargs) -> None:
        """
        Update metadata with key-value pairs from a dict or keyword arguments.

        Args:
            other: Dictionary of key-value pairs to add
            **kwargs: Additional key-value pairs as keyword arguments

        Example:
            >>> metadata = (
            ...     Metadata()
            ... )
            >>> metadata.update(
            ...     {
            ...         "author": "John",
            ...         "version": "1.0",
            ...     }
            ... )
            >>> metadata.update(
            ...     status="approved"
            ... )
        """
        if other:
            for key, value in other.items():
                self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def clear(self) -> None:
        """
        Remove all key-value pairs from metadata.

        This removes all comments that contain '=' (key-value pairs) but
        preserves regular comments that don't follow the key=value format.

        Example:
            >>> metadata = (
            ...     Metadata()
            ... )
            >>> metadata["key1"] = (
            ...     "value1"
            ... )
            >>> metadata.add_comment(
            ...     "Regular comment"
            ... )
            >>> metadata.clear()
            >>> len(metadata)
            0
            >>> "Regular comment" in metadata.comments
            True
        """
        if not self.comments:
            return

        # Keep only comments that don't contain '=' (regular comments)
        self.comments = [c for c in self.comments if "=" not in c]

    def pop(self, key: str, default=None) -> Any:
        """
        Remove and return a value from metadata.

        Values are automatically deserialized from JSON.

        Args:
            key: The key to remove
            default: Default value to return if key is not found

        Returns:
            The deserialized value associated with the key, or default if not found

        Example:
            >>> metadata = (
            ...     Metadata()
            ... )
            >>> metadata[
            ...     "version"
            ... ] = "1.0"
            >>> version = (
            ...     metadata.pop(
            ...         "version"
            ...     )
            ... )
            >>> "version" in metadata
            False
        """
        try:
            value = self[key]
            del self[key]
            return value
        except (KeyError, ValueError):
            return default

    def add_comment(self, comment: str) -> None:
        """
        Add a regular comment (not a key-value pair) to metadata.

        Regular comments are not treated as key-value pairs and are ignored
        by dict-like operations like keys(), values(), items(), etc.

        Args:
            comment: The comment text to add

        Example:
            >>> metadata = (
            ...     Metadata()
            ... )
            >>> metadata.add_comment(
            ...     "This is a note about the observation"
            ... )
            >>> metadata.add_comment(
            ...     "Created by John Doe"
            ... )
            >>> metadata[
            ...     "author"
            ... ] = "John"
            >>> metadata.keys()
            ['author']
            >>> len(
            ...     metadata.comments
            ... )
            3
        """
        if self.comments is None:
            self.comments = []

        self.comments.append(comment)

    def get_obs_ids(self) -> list[str]:
        """Returns observation IDs from the planning section.
        
        Returns an empty list if planning structure is incomplete or missing.
        Safe to call during deserialization - handles partially-initialized objects.
        
        Returns:
            list[str]: List of observation IDs, empty if not available.
            
        Note:
            This is a method rather than a property to avoid being triggered
            during object deserialization/initialization.
        """
        # Safe navigation through nested attributes
        planning = getattr(self, 'planning', None)
        if not planning:
            return []
        
        observations = getattr(planning, 'observations', None)
        if not observations:
            return []
        
        obs_list = getattr(observations, 'observations', None)
        if not obs_list:
            return []
        
        # Extract obs_ids from observation list
        result = []
        for ob in obs_list:
            obs_id = getattr(ob, 'obs_id', None)
            if obs_id:
                result.append(obs_id)
        
        return result

    def __len__(self) -> int:
        """
        Return the number of key-value pairs in metadata.

        Returns:
            Number of key-value pairs (excludes regular comments)

        Example:
            >>> metadata = (
            ...     Metadata()
            ... )
            >>> metadata["key1"] = (
            ...     "value1"
            ... )
            >>> metadata["key2"] = (
            ...     "value2"
            ... )
            >>> metadata.add_comment(
            ...     "Regular comment"
            ... )
            >>> len(metadata)
            2
        """
        return len(self.keys())

    def __repr__(self) -> str:
        """
        Return a string representation of the metadata.

        Returns:
            String showing the metadata contents

        Example:
            >>> metadata = (
            ...     Metadata()
            ... )
            >>> metadata[
            ...     "version"
            ... ] = "1.0"
            >>> repr(metadata)
            "Metadata({'version': '1.0'})"
        """
        kv_pairs = dict(self.items())
        return f"Metadata({kv_pairs})"

    @property
    def id(self) -> str | None:
        """
        Returns the block ID from the metadata.

        Priority logic:
        1. Planning.block_id (if set)
        2. First designer prime observation's obs_id (if set)
        3. First designer prime observation's definition (fallback)

        Returns:
            The block ID or None if not found
        """
        return get_block_human_id(self.planning)

    @id.setter
    def id(self, value: str) -> None:
        """
        Sets the block ID in the metadata.

        Sets Planning.block_id and also updates obs_id and definition
        in the first designer prime observation for consistency.

        Args:
            value: The ID value to set
        """
        set_block_human_id(self.planning, value)


@element_define
class WheelMomentum(PtrElement):
    """Reaction wheel angular momentum value.

    Represents the angular momentum stored in a single reaction wheel.

    Attributes:
        value: The angular momentum magnitude (default: 0).
        number: The wheel number identifier (default: 1).
        unit: The unit of angular momentum (default: "Nms" - Newton·meter·seconds).
    """

    value: int | float = text(default=0)
    number: int = attr(default=1)
    unit: Literal["Nms"] = attr(default="Nms")


@element_define
class WheelMomentumTarget(PtrElement):
    """Target wheel momentum configuration for the spacecraft.

    Contains a list of reaction wheels and their target angular momentum values.
    Automatically initializes with 3 wheels by default if none are provided.

    Attributes:
        wheel: List of WheelMomentum objects representing each reaction wheel.
    """

    wheel: list[WheelMomentum] = element(factory=list)

    def __attrs_post_init__(self):
        if not self.wheel:
            # Initialize with 3 wheels by default
            self.wheel = [WheelMomentum(number=i + 1) for i in range(3)]


@element_define
class MWOLMetadata(PtrElement):
    """Momentum wheel operations and limitations metadata.

    Contains operational constraints and target values for the spacecraft's
    momentum wheel (reaction wheel) system.

    Attributes:
        wheel_momentum_target: Target angular momentum values for all reaction wheels.
    """

    wheel_momentum_target: WheelMomentumTarget = element(factory=WheelMomentumTarget)


# =============================================================================
# Legacy Format Compatibility Functions
# =============================================================================
#
# TODO: Remove fallback logic for observations.* fields once legacy PTR formats are migrated.
#
# Background:
# -----------
# Legacy formats (ORB17 and earlier) stored metadata in different locations:
# - Block identifiers: observations.definition or observations.obs_id
# - Designer: observations.designer
#
# Modern formats use canonical locations:
# - Block identifiers: planning.block_id
# - Designer: planning.designer
#
# Migration Strategy:
# -------------------
# During deserialization (cattrs hooks), we should automatically migrate values from
# legacy locations to their canonical locations, eliminating the need for runtime
# fallback logic in get/set functions.
#
# Testing Implications:
# ---------------------
# This migration will affect round-trip tests that read/write legacy PTR files.
#
# =============================================================================


def get_block_human_id(planning: Planning | None) -> str | None:
    """
    Independent function to retrieve block ID from planning metadata.

    Priority logic:
    1. Planning.block_id (if set)
    2. First designer prime observation's obs_id (if set)
    3. First designer prime observation's definition (fallback)

    Args:
        planning: The Planning object to extract ID from

    Returns:
        The block ID or None if not found
    """
    if not planning:
        log.debug("Planning is None, cannot retrieve block ID.")
        return None

    # Priority 1: Planning.block_id
    if hasattr(planning, "block_id") and planning.block_id:
        return planning.block_id

    # Priority 2 & 3: Check observations (fallback for legacy formats)
    try:
        observations = (
            planning.observations.designer_prime_observations
            or planning.observations.designer_observations
            or planning.observations.observations
        )
        if not observations:
            log.debug("No designer prime observations found.")
            return None

        first_obs = observations[0]

        # Priority 2: obs_id field
        # the new implementation have obs_id but the one used for orb17 do not have it.
        if hasattr(first_obs, "obs_id") and first_obs.obs_id:
            return first_obs.obs_id

        # Priority 3: definition field (fallback)
        if hasattr(first_obs, "definition") and first_obs.definition:
            return first_obs.definition

        # we resort to identify the block with the designer.
        if planning.designer:
            return f"<{planning.designer}>"

        log.debug("No block_id, obs_id, or definition found.")
        return None

    except (AttributeError, IndexError) as e:
        log.debug(f"Error retrieving block ID from observations: {e}")
        return None


def set_block_human_id(planning: Planning | None, value: str) -> bool:
    """
    Independent function to set block ID in planning metadata.

    Sets Planning.block_id as the primary field, and also sets obs_id and
    definition in the first designer prime observation for consistency.

    Args:
        planning: The Planning object to set ID in
        value: The ID value to set

    Returns:
        True if successful, False otherwise
    """
    if not planning:
        log.warning("Planning is None, cannot set block ID.")
        return False

    # Set Planning.block_id (primary)
    planning.block_id = value

    # Also set in observations for legacy format compatibility
    try:
        observations = planning.observations.designer_prime_observations
        if observations:
            first_obs = observations[0]
            first_obs.obs_id = value
            first_obs.definition = value
            log.debug(f"Set block ID to: {value} (in planning and observation)")
        else:
            log.debug(f"Set block ID to: {value} (only in planning, no observations)")

        return True

    except (AttributeError, IndexError) as e:
        log.warning(f"Set block_id in planning but could not update observation: {e}")
        return True  # Still return True since we set planning.block_id


# def get_observation_id(planning: Planning | None) -> str | None:
#     """
#     Independent function to retrieve observation ID from planning metadata.

#     Priority logic:
#     1. First designer prime observation's obs_id (if set)
#     2. First designer prime observation's definition (fallback)

#     Args:
#         planning: The Planning object to extract ID from

#     Returns:
#         The observation ID or None if not found
#     """
#     if not planning:
#         log.debug("Planning is None, cannot retrieve observation ID.")
#         return None

#     try:
#         observations = planning.observations.designer_prime_observations
#         if not observations:
#             log.debug("No designer prime observations found.")
#             return None

#         first_obs = observations[0]

#         # Priority 1: obs_id field
#         if first_obs.obs_id:
#             return first_obs.obs_id

#         # Priority 2: definition field (fallback)
#         if first_obs.definition:
#             return first_obs.definition

#         log.debug("No obs_id or definition found in first designer prime observation.")
#         return None

#     except (AttributeError, IndexError) as e:
#         log.debug(f"Error retrieving observation ID: {e}")
#         return None


# def set_observation_id(planning: Planning | None, value: str) -> bool:
#     """
#     Independent function to set observation ID in planning metadata.

#     Sets both obs_id (priority) and definition (for backward compatibility).

#     Args:
#         planning: The Planning object to set ID in
#         value: The ID value to set

#     Returns:
#         True if successful, False otherwise
#     """
#     if not planning:
#         log.warning("Planning is None, cannot set observation ID.")
#         return False

#     try:
#         observations = planning.observations.designer_prime_observations
#         if not observations:
#             log.warning("No designer prime observations found to set ID.")
#             return False

#         first_obs = observations[0]

#         # Set both fields for consistency
#         first_obs.obs_id = value
#         first_obs.definition = value

#         log.debug(f"Set observation ID to: {value}")
#         return True

#     except (AttributeError, IndexError) as e:
#         log.warning(f"Could not set observation ID to {value}: {e}")
#         return False


def get_block_designer(planning: Planning | None) -> str | None:
    """
    Independent function to retrieve designer from planning metadata.

    Priority logic:
    1. Planning.designer (if set) - primary location
    2. First observation's designer field (fallback)

    Args:
        planning: The Planning object to extract designer from

    Returns:
        The designer name or None if not found
    """
    if not planning:
        log.debug("Planning is None, cannot retrieve designer.")
        return None

    # Priority 1: Planning.designer (primary location)
    if hasattr(planning, "designer") and planning.designer:
        return planning.designer

    # Priority 2: Check observations.designer field (fallback for legacy formats)
    try:
        if not hasattr(planning, "observations") or not planning.observations:
            log.debug("No observations found in planning.")
            return None

        if (
            hasattr(planning.observations, "designer")
            and planning.observations.designer
        ):
            return planning.observations.designer

        log.debug("No designer found in planning or observations.")
        return None

    except AttributeError as e:
        log.debug(f"Error retrieving designer: {e}")
        return None


def set_block_designer(planning: Planning | None, value: str) -> bool:
    """
    Independent function to set designer in planning metadata.

    Sets Planning.designer as the primary field, and also sets
    observations.designer for consistency.

    Args:
        planning: The Planning object to set designer in
        value: The designer value to set

    Returns:
        True if successful, False otherwise
    """
    if not planning:
        log.warning("Planning is None, cannot set designer.")
        return False

    # Set Planning.designer (primary)
    if hasattr(planning, "designer"):
        planning.designer = value
        log.debug(f"Set designer in planning to: {value}")
        return True

    # Fallback: Set observations.designer for legacy format compatibility
    if (
        hasattr(planning, "observations")
        and planning.observations
        and hasattr(planning.observations, "designer")
    ):
        planning.observations.designer = value
        log.debug(f"Set designer in observations to: {value}")

        return True

    log.warning("Could not set designer in planning or observations.")
    return False
