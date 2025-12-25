from __future__ import annotations

import numpy as np

from attrs_xml import attr, element_define, text
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.units import (
    ANGULAR_UNITS_LITERAL,
    ANGULAR_VELOCITY_UNITS_LITERAL,
    DELTA_TIME_UNITS_LITERAL,
)


@element_define
class VectorWithUnits(PtrElement):
    units: str = attr(default="", kw_only=True, converter=str)
    values: np.ndarray = text(
        factory= lambda: np.array([0, 0, 1.0]),
        converter=np.array,
        eq=lambda arr: arr.tobytes(),
    )



    def __str__(self) -> str:
        return f"{self.values} {self.units}"


@element_define
class TimesVector(VectorWithUnits):
    units: DELTA_TIME_UNITS_LITERAL = attr(
        default="sec",
    )




@element_define
class AnglesVector(VectorWithUnits):
    units: ANGULAR_UNITS_LITERAL = attr(
        default="deg",
    )


@element_define
class AngularVelocityVector(VectorWithUnits):
    units: ANGULAR_VELOCITY_UNITS_LITERAL = attr(
        default="deg/sec",
    )



ARRAYS = (TimesVector | AnglesVector | AngularVelocityVector)
