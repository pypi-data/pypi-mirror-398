from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import ptwrapper
from attrs import define, field
from loguru import logger as log

from attrs_xml.xml.io import load

from . import html as agm_html

if TYPE_CHECKING:
    import os

    from ptr_editor.elements.agm_config import AGMConfig, Definition

targets_to_agm_dir_shortnames = {
    "JUPITER": "JP",
    "GANYMEDE": "GA",
    "CALLISTO": "CA",
    "EUROPA": "EU",
    "IO": "IO",
}


def _get_agm_fix_definition_file() -> Path:
    """
    Get the path to the fixed definitions XML file, for the currently installed ptwrapper.
    """

    return (
        Path(ptwrapper.__file__).parent / "config/agm/cfg_agm_jui_fixed_definitions.xml"
    )


def _get_agm_config_file() -> Path:
    """
    Get the AGM configuration with fixed definitions, for the currently installed ptwrapper.
    """

    return Path(ptwrapper.__file__).parent / "config/agm/cfg_agm_jui.xml"


def _get_agm_predefined_blocks_file() -> Path:
    """
    Get the path to the predefined blocks XML file, for the currently installed ptwrapper.
    """

    return (
        Path(ptwrapper.__file__).parent / "config/agm/cfg_agm_jui_predefined_block.xml"
    )


@define
class AGMConfiguration:
    """
    Wrapper for ptr elements of the AGM configuration.

    This class provides access to AGM configuration data and definitions loaded from XML files
    distributed with ptwrapper. It exposes methods to query known AGM directions, objects, frames,
    and surfaces, and to map AGM names to their corresponding SPICE names.

    """

    fixed_definition_file: os.PathLike = field(
        factory=_get_agm_fix_definition_file,
    )

    cfg_file: os.PathLike = field(factory=_get_agm_config_file)

    # we keep definitions and cfg loaded here for reuse
    _definitions: Definition | None = field(init=False, default=None, repr=False)
    _cfg: AGMConfig | None = field(init=False, default=None, repr=False)

    def _ipython_key_completions_(self) -> list[str]:
        return self.definitions.names

    def __getitem__(self, name: str):
        return self._definitions.__getitem__(name)

    def _repr_html_(self) -> str:
        return agm_html.repr_html(self)

    def _load_fixed_definitions(self):
        """
        Load fixed definitions for AGM configuration.

        Loading of definition file is done with AGM validation disabled as it
        would try to validate agains a config that is not loaded.
        agm_validation_disabled also disable name resolution agains AGM entities.
        """

        # Path to the fixed definitions XML file
        from ptr_editor.agm_validator.agm_config_validator import (
            agm_validation_disabled,
        )
        from ptr_editor.services.quick_access import get_elements_registry

        ptr = get_elements_registry()

        with agm_validation_disabled():  # temporarily disable AGM validation
            got = load(self.fixed_definition_file, registry=ptr)
        if not got:
            msg = f"Failed to load fixed definitions from {self.fixed_definition_file}"
            raise ValueError(msg)
        self._definitions = got

    def _load_agm_config(self):
        """
        Load the AGM configuration from the XML file.
        """

        from ptr_editor.services.quick_access import get_elements_registry

        # Path to the AGM configuration XML file
        ptr = get_elements_registry()
        got = load(self.cfg_file, registry=ptr)
        if not got:
            msg = f"Failed to load AGM configuration from {self.cfg_file}"
            raise ValueError(msg)
        self._cfg = got

    @property
    def definitions(self) -> Definition:
        """
        Get the loaded AGM configuration definitions.
        """
        if self._definitions is None:
            self._load_fixed_definitions()
        return self._definitions

    def north_pole_direction(self, target: str) -> str | None:
        """
        Get the north pole direction name for a given target object.

        Args:
            target: The name of the target object.

        """
        shortname = targets_to_agm_dir_shortnames.get(target.upper())
        if shortname is None:
            return None
        return f"{shortname}NorthPole"

    def sc_target_direction(self, target: str) -> str | None:
        """
        Get the spacecraft target direction name for a given target object.

        Args:
            target: The name of the target object.

        """
        shortname = targets_to_agm_dir_shortnames.get(target.upper())
        if shortname is None:
            return None
        return f"SC2{shortname}"

    @property
    def cfg(self) -> AGMConfig:
        """
        Get the loaded AGM configuration.
        """
        if self._cfg is None:
            self._load_agm_config()
        return self._cfg

    def is_known_agm_direction(self, name: str) -> bool:
        return self.definitions.vector_by_name(name) is not None

    def is_known_agm_object(self, name: str) -> bool:
        return self.cfg.object_by_name(name) is not None

    def is_known_agm_frame(self, name: str) -> bool:
        return self.cfg.frame_by_name(name) is not None

    def is_known_agm_surface(self, name: str) -> bool:
        return self.definitions.surface_by_name(name) is not None

    def agm_direction_to_spice_name(self, name: str) -> str:
        obj = self.cfg.object_by_name(name)
        if obj is None:
            msg = f"Object with name '{name}' not found in AGM configuration"
            raise ValueError(msg)
        return obj.spice_name

    def agm_frame_to_spice_name(self, name: str) -> str:
        frame = self.cfg.frame_by_name(name)
        if frame is None:
            msg = f"Frame with name '{name}' not found in AGM configuration"
            raise ValueError(msg)
        return frame.spice_name

    def agm_object_to_spice_name(self, name: str) -> str:
        obj = self.cfg.object_by_name(name)
        if obj is None:
            msg = f"Object with name '{name}' not found in AGM configuration"
            raise ValueError(msg)
        return obj.spice_name

    def vector_by_name(self, name: str):
        return self.definitions.vector_by_name(name)

    def normalize_name(
        self,
        name: str,
        definition_types: Sequence[str] | None = None,
    ) -> str:
        """
        Normalize an AGM name to its canonical casing.

        Looks up the name in the AGM configuration and returns the canonical
        parser_name. If not found, returns the value unchanged.

        Args:
            name: The name to normalize.
            definition_types: The type(s) of AGM definition to search in.
                If None, searches in all types (object, frame, direction, surface).

        Returns:
            The normalized name, or the original name if not found.

        Example:
            >>> config = get_agm_configuration()
            >>> config.normalize_name(
            ...     "sun",
            ...     ["object"],
            ... )
            "Sun"
        """

        # Convert to list of types to check
        if definition_types is None:
            types_to_check = ["object", "frame", "direction", "surface"]
        else:
            types_to_check = list(definition_types)

        log.debug(f"Normalizing name '{name}' for definition types: {definition_types}")

        # Define lookup strategies for each definition type
        lookup_strategies = {
            "object": (
                lambda: self.cfg.object_by_name(name),
                lambda obj: obj.parser_name,
            ),
            "frame": (
                lambda: self.cfg.frame_by_name(name),
                lambda frame: frame.parser_name,
            ),
            "direction": (
                lambda: self.definitions.vector_by_name(name),
                lambda vector: vector.name,
            ),
            "surface": (
                lambda: self.definitions.surface_by_name(name),
                lambda surface: surface.name,
            ),
        }

        # Check each type in order
        for def_type in types_to_check:
            if def_type not in lookup_strategies:
                continue

            lookup_fn, get_parser_name = lookup_strategies[def_type]
            entity = lookup_fn()

            if entity is not None:
                parser_name = get_parser_name(entity)
                if parser_name is not None:
                    log.opt(lazy=True).trace(
                        f"Found {def_type} '{name}' with parser_name '{parser_name}'"
                    )
                    return parser_name

        log.debug(
            f"Name '{name}' not found in AGM definitions of types {types_to_check}"
        )
        # Not found - return unchanged
        return name

    def as_pandas_objects(self) -> pd.DataFrame:
        """
        Get AGM objects as a pandas DataFrame.

        Returns:
            DataFrame with columns: name, mnemonic, spice_name, is_body,
            buffer_pos, buffer_pos_time_step, buffer_vel, buffer_vel_time_step,
            gravity, orbiting_name, is_target_obj, is_reference_obj,
            eclipse_evt, penumbra_evt, penumbra_factor.

        Example:
            >>> config = get_agm_configuration()
            >>> df = config.as_pandas_objects()
            >>> df[
            ...     [
            ...         "name",
            ...         "spice_name",
            ...         "gravity",
            ...     ]
            ... ]
        """
        if not self.cfg or not self.cfg.objects:
            return pd.DataFrame()

        data = []
        for obj in self.cfg.objects.objects:
            data.append(
                {
                    "name": obj.parser_name,
                    "mnemonic": obj.mnemonic,
                    "spice_name": obj.spice_name,
                    "is_body": obj.is_body,
                    "buffer_pos": obj.buffer_pos,
                    "buffer_pos_time_step": obj.buffer_pos_time_step,
                    "buffer_vel": obj.buffer_vel,
                    "buffer_vel_time_step": obj.buffer_vel_time_step,
                    "gravity": obj.gravity,
                    "orbiting_name": obj.orbiting_name,
                    "is_target_obj": obj.is_target_obj,
                    "is_reference_obj": obj.is_reference_obj,
                    "eclipse_evt": obj.eclipse_evt,
                    "penumbra_evt": obj.penumbra_evt,
                    "penumbra_factor": obj.penumbra_factor,
                }
            )
        return pd.DataFrame(data)

    def as_pandas_frames(self) -> pd.DataFrame:
        """
        Get AGM frames as a pandas DataFrame.

        Returns:
            DataFrame with columns: name, mnemonic, spice_name, buffer_att,
            buffer_att_time_step, is_reference_frame.

        Example:
            >>> config = get_agm_configuration()
            >>> df = config.as_pandas_frames()
            >>> df[
            ...     [
            ...         "name",
            ...         "spice_name",
            ...     ]
            ... ]
        """
        if not self.cfg or not self.cfg.frames:
            return pd.DataFrame()

        data = []
        for frame in self.cfg.frames.frames:
            data.append(
                {
                    "name": frame.parser_name,
                    "mnemonic": frame.mnemonic,
                    "spice_name": frame.spice_name,
                    "buffer_att": frame.buffer_att,
                    "buffer_att_time_step": frame.buffer_att_time_step,
                    "is_reference_frame": frame.is_reference_frame,
                }
            )
        return pd.DataFrame(data)

    def as_pandas_directions(self) -> pd.DataFrame:
        """
        Get AGM directions as a pandas DataFrame.

        Returns:
            DataFrame with columns: name, type, and any additional attributes
            specific to the direction type.

        Example:
            >>> config = get_agm_configuration()
            >>> df = config.as_pandas_directions()
            >>> df[["name", "type"]]
        """
        data = []
        for vec in self.definitions.dir_vectors:
            row = {
                "name": vec.name,
                "type": vec.__class__.__name__,
            }
            # Add any additional attributes from the vector object
            if hasattr(vec, "frame"):
                row["frame"] = getattr(vec, "frame", None)
            if hasattr(vec, "axis"):
                row["axis"] = getattr(vec, "axis", None)
            if hasattr(vec, "from_object"):
                row["from_object"] = getattr(vec, "from_object", None)
            if hasattr(vec, "to_object"):
                row["to_object"] = getattr(vec, "to_object", None)

            data.append(row)
        return pd.DataFrame(data)

    def as_pandas_surfaces(self) -> pd.DataFrame:
        """
        Get AGM surfaces as a pandas DataFrame.

        Returns:
            DataFrame with columns: name, type, and any additional attributes
            specific to the surface.

        Example:
            >>> config = get_agm_configuration()
            >>> df = config.as_pandas_surfaces()
            >>> df[["name", "type"]]
        """
        data = []
        for surf in self.definitions.surfaces:
            row = {
                "name": surf.name,
                "type": "Surface",
            }
            # Add any additional attributes from the surface object
            if hasattr(surf, "body"):
                row["body"] = getattr(surf, "body", None)
            if hasattr(surf, "frame"):
                row["frame"] = getattr(surf, "frame", None)

            data.append(row)
        return pd.DataFrame(data)


def get_agm_configuration() -> AGMConfiguration:
    """
    Get the AGM configuration instance from the global context.

    This is a convenience function that retrieves the AGM configuration
    from the global context registry.

    Returns:
        AGMConfiguration: The AGM configuration instance.

    Example:
        >>> from ptr_editor.agm_config import (
        ...     get_agm_configuration,
        ... )
        >>> config = get_agm_configuration()
        >>> config.is_known_agm_object(
        ...     "Jupiter"
        ... )
        True
    """
    from ptr_editor.context import get_services

    return get_services()["agm_config"]


def set_agm_configuration(cfg: AGMConfiguration):
    """
    Set the AGM configuration instance in the global service registry.

    This is useful for testing with mock configurations or using
    custom configuration files.

    Args:
        cfg: The AGM configuration instance to set.

    Example:
        >>> from ptr_editor.agm_config import (
        ...     set_agm_configuration,
        ...     AGMConfiguration,
        ... )
        >>> custom_config = AGMConfiguration(
        ...     cfg_file="/path/to/custom/config.xml"
        ... )
        >>> set_agm_configuration(
        ...     custom_config
        ... )
    """
    from ptr_editor.context import get_services

    get_services().set_override("agm_config", cfg)
