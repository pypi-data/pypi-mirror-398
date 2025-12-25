"""Elments to parse AGM config files."""

from __future__ import annotations

from functools import cached_property

from attrs_xml import attr, element, element_define, text
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.directions import DIRECTIONS  # noqa: TC001
from ptr_editor.elements.surface import SurfaceDefinition  # noqa: TC001


@element_define
class Definition(PtrElement):
    dir_vectors: list[DIRECTIONS] = element(factory=list, tag="dirVector")
    surfaces: list[SurfaceDefinition] = element(factory=list, tag="surface")

    @property
    def all(self) -> list[DIRECTIONS | SurfaceDefinition]:
        """
        Get all elements in the AGM configuration.
        """
        return self.dir_vectors + self.surfaces

    @property
    def names(self) -> list[str]:
        """
        Get the names of all elements in the AGM configuration.
        """
        return [item.name for item in self.all if item.name]

    @cached_property
    def _vector_cache(self) -> dict[str, DIRECTIONS]:
        """Cached lookup dictionary for direction vectors."""
        return {v.name.casefold(): v for v in self.dir_vectors if v.name}

    @cached_property
    def _surface_cache(self) -> dict[str, SurfaceDefinition]:
        """Cached lookup dictionary for surface definitions."""
        return {s.name.casefold(): s for s in self.surfaces if s.name}

    def vector_by_name(self, name: str) -> DIRECTIONS | None:
        """
        Find a direction vector by its name.

        Args:
            name: The name of the direction vector to find.

        Returns:
            The DIRECTIONS instance if found, otherwise None.
        """
        return self._vector_cache.get(name.casefold())

    def surface_by_name(self, name: str) -> SurfaceDefinition | None:
        """
        Find a surface definition by its name.

        Args:
            name: The name of the surface definition to find.

        Returns:
            The SurfaceDefinition instance if found, otherwise None.
        """
        return self._surface_cache.get(name.casefold())

    def find_by_name(self, name: str) -> DIRECTIONS | SurfaceDefinition | None:
        """
        Find a definition by its name.

        Args:
            name: The name of the definition to find.

        Returns:
            The DIRECTIONS or SurfaceDefinition instance if found, otherwise None.
        """
        for item in self.all:
            if item.name.casefold() == name.casefold():
                return item
        return None

    def __getitem__(self, item: str) -> DIRECTIONS | SurfaceDefinition | None:
        """
        Get an attribute by its name.

        Args:
            item: The name of the attribute to get.

        Returns:
            The DIRECTIONS or SurfaceDefinition instance if found, otherwise None.
        """
        return self.find_by_name(item)

    def _ipython_key_completions_(self):
        """
        Provide IPython key completions for the definition.
        """
        return [item.name for item in self.all if item.name]


@element_define
class Integration(PtrElement):
    """Integration value element."""

    default_name = "integration"

    id: str = attr()
    type: str = attr()
    value: str = text()


@element_define
class IntegrationValues(PtrElement):
    """Container for integration values."""

    default_name = "IntegrationValues"

    integrations: list[Integration] = element(tag="Integration", factory=list)


@element_define
class Param(PtrElement):
    """Parameter element with id, type, description, unit and value."""

    default_name = "Param"

    id: str = attr()
    type: str = attr()
    description: str | None = attr(default=None)
    unit: str | None = attr(default=None)
    value: str | None = text(default=None)


@element_define
class Parameters(PtrElement):
    """Container for parameters."""

    default_name = "Parameters"

    params: list[Param] = element(tag="Param", factory=list)


@element_define
class Object(PtrElement):
    """Object element representing celestial bodies and spacecraft."""

    default_name = "Object"

    # XML attributes mapped to snake_case field names with XML tag names
    parser_name: str = attr()
    mnemonic: str = attr()
    spice_name: str = attr()
    is_body: bool | None = attr(default=None)
    buffer_pos: bool | None = attr(default=None)
    buffer_pos_time_step: float | None = attr(default=None)
    buffer_vel: bool | None = attr(default=None)
    buffer_vel_time_step: float | None = attr(default=None)
    gravity: float | None = attr(default=None)
    orbiting_name: str | None = attr(default=None)
    is_target_obj: bool | None = attr(default=None)
    is_reference_obj: bool | None = attr(default=None)
    eclipse_evt: str | None = attr(default=None)
    penumbra_evt: str | None = attr(default=None)
    penumbra_factor: float | None = attr(default=None)


@element_define
class Objects(PtrElement):
    """Container for objects."""

    default_name = "Objects"

    objects: list[Object] = element(tag="Object", factory=list)


@element_define
class Frame(PtrElement):
    """Frame element representing reference frames."""

    default_name = "Frame"

    parser_name: str = attr(tag="parserName")
    mnemonic: str = attr()
    spice_name: str = attr(tag="spiceName")
    buffer_att: bool | None = attr(tag="bufferAtt", default=None)
    buffer_att_time_step: float | None = attr(tag="bufferAttTimeStep", default=None)
    is_reference_frame: bool | None = attr(tag="isReferenceFrame", default=None)


@element_define
class Frames(PtrElement):
    """Container for frames."""

    default_name = "Frames"

    frames: list[Frame] = element(tag="Frame", factory=list)


@element_define
class AGMConfig(PtrElement):
    """Root AGM configuration element."""

    default_name = "AGMConfig"

    integration_values: IntegrationValues | None = element(
        tag="IntegrationValues",
        default=None,
    )
    parameters: Parameters | None = element(tag="Parameters", default=None)
    objects: Objects | None = element(tag="Objects", default=None)
    frames: Frames | None = element(tag="Frames", default=None)

    def object_by_name(self, name: str) -> Object | None:
        """
        Find an object by its name.

        Args:
            name: The name of the object to find.

        Returns:
            The Object instance if found, otherwise None.
        """
        if not self.objects:
            return None
        for obj in self.objects.objects:
            if obj.parser_name.casefold() == name.casefold():
                return obj
        return None

    def frame_by_name(self, name: str) -> Frame | None:
        """
        Find a frame by its name.

        Args:
            name: The name of the frame to find.

        Returns:
            The Frame instance if found, otherwise None.
        """
        if not self.frames:
            return None
        for frame in self.frames.frames:
            if frame.parser_name.casefold() == name.casefold():
                return frame
        return None
