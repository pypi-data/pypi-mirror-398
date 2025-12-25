import numpy as np
from attrs import define, field
from attrs.validators import instance_of

from ptr_editor.accessors.accessor import register_accessor
from ptr_editor.agm_config import AGMConfiguration, get_agm_configuration
from ptr_editor.elements.directions import (
    DIRECTIONS,
    Direction,
    NamedDirection,
)

from .eval_directions import eval_direction


@define
class SpiceDirectionAccessor:
    _direction: DIRECTIONS = field(repr=True, validator=instance_of(DIRECTIONS))
    _agm_config: AGMConfiguration = field(repr=False, factory=get_agm_configuration)

    is_named: bool = field(
        init=False,
        default=False,
        validator=instance_of(bool),
    )
    is_framed: bool = field(
        init=False,
        default=False,
        validator=instance_of(bool),
    )

    def __attrs_post_init__(self):
        if isinstance(self._direction, NamedDirection):
            self.is_named = True
        if hasattr(self._direction, "frame"):
            self.is_framed = True

    @property
    def frame(self) -> str:
        """
        Get the frame of the direction.
        """

        if not hasattr(self._direction, "frame"):
            msg = f"Direction {self._direction} does not have a frame attribute."
            raise AttributeError(
                msg,
            )

        return self._agm_config.agm_frame_to_spice_name(self._direction.frame)

    def eval(self, time: str | float, frame: str = "J2000") -> np.ndarray:
        return eval_direction(self._direction, time, self._agm_config, frame=frame)


register_accessor(Direction, SpiceDirectionAccessor, "spice")
