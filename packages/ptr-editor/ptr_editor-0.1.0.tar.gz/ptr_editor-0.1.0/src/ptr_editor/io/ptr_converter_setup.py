from typing import get_args

from cattrs.strategies import include_subclasses

from ptr_editor.elements.array import ARRAYS, VectorWithUnits
from ptr_editor.elements.attitude import ATTITUDES, Attitude
from ptr_editor.elements.blocks import BLOCKS, Block
from ptr_editor.elements.directions import DIRECTIONS, Direction
from ptr_editor.elements.offset import OFFSETS, OffsetAngles
from ptr_editor.elements.phase_angle import PHASE_ANGLES, PhaseAngle
from ptr_editor.elements.values import VALUES, ValueWithUnits


def setup_subclasses_disambiguation(converter):
    include_subclasses(Attitude, converter, subclasses=get_args(ATTITUDES))
    include_subclasses(Direction, converter, subclasses=get_args(DIRECTIONS))
    include_subclasses(Block, converter, subclasses=get_args(BLOCKS))
    include_subclasses(PhaseAngle, converter, subclasses=get_args(PHASE_ANGLES))
    include_subclasses(ValueWithUnits, converter, subclasses=get_args(VALUES))
    include_subclasses(VectorWithUnits, converter, subclasses=get_args(ARRAYS))
    include_subclasses(OffsetAngles, converter, subclasses=get_args(OFFSETS))
