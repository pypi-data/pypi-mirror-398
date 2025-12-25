from __future__ import annotations

from attrs_xml import attr, element, element_define
from ptr_editor.agm_validator.agm_config_validator import is_known_agm_definition
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.directions import (
    NamedDirection,
    VectorDirection,
)
from ptr_editor.elements.values import Distance


@element_define
class Surface(PtrElement):
    name: str | None = attr(default=None, kw_only=True)

    @classmethod
    def from_string(cls, value: str) -> Surface:
        """
        Create a Surface instance from a string.
        The string should be in the format "ref".
        """

        if isinstance(value, str):
            return RefSurface(ref=value)

        msg = f"Invalid type for Surface: {type(value)}. Expected str or Surface."
        raise TypeError(msg)


@element_define
class RefSurface(Surface):
    ref: str = attr(validator = is_known_agm_definition("surface"))


@element_define
class SurfaceDefinition(Surface):
    frame: str = attr(validator = is_known_agm_definition("frame"))
    origin: NamedDirection = element()
    a: Distance = element()
    b: Distance = element()
    c: Distance = element()
    axis_a: VectorDirection = element()
    axis_b: VectorDirection = element()
    axis_c: VectorDirection = element()


SURFACES = RefSurface | SurfaceDefinition
