from loguru import logger as log

log.debug('Importing ptr_editor.elements package')

# AGM Config elements
from .agm_config import (
    AGMConfig,
    Definition,
    Frame,
    Frames,
    Integration,
    IntegrationValues,
    Object,
    Objects,
    Param,
    Parameters,
)

# Array elements
from .array import AnglesVector, AngularVelocityVector, TimesVector, VectorWithUnits

# Attitude elements
from .attitude import (
    ATTITUDES,
    Attitude,
    CaptureAttitude,
    IlluminatedPointAttitude,
    InertialAttitude,
    LimbAttitude,
    SpecularAttitude,
    TerminatorAttitude,
    TrackAttitude,
    VelocityAttitude,
)

# Block elements
from .blocks import (
    BLOCKS,
    Block,
    DownlinkBlock,
    MNAVBlock,
    MTCMBlock,
    MWOLBlock,
    ObsBlock,
    SlewBlock,
    TimedBlock,
)

# Direction elements
from .directions import (
    CrossProductDirection,
    DerivedDirection,
    Direction,
    LonLatDirection,
    NamedDirection,
    OriginTargetDirection,
    ProjectedVectorToPlaneDirection,
    RotatedDirection,
    VectorDirection,
    VelocityDirection,
)

# Document elements
from .doc import Body, Data, Prm, Segment

# Metadata elements
from .metadata import (
    Metadata,
    MWOLMetadata,
    Observation,
    Observations,
    Planning,
    PlanningSegmentation,
    SolarArrays,
    WheelMomentum,
    WheelMomentumTarget,
)

# Offset elements
from .offset import (
    OFFSETS,
    CustomOffsetAngles,
    FixedOffsetAngles,
    OffsetAngles,
    RasterOffsetAngles,
    ScanOffsetAngles,
)

# Phase angle elements
from .phase_angle import (
    PHASE_ANGLES,
    AlignedPhaseAngle,
    FlipPhaseAngle,
    PhaseAngle,
    PowerOptimizedPhaseAngle,
)


# Unit elements
from .units import print_known_units # just the utils

# Surface elements
from .surface import RefSurface, Surface, SurfaceDefinition

# Timeline elements
from .timeline import Timeline

# Value elements
from .values import Angle, AngularVelocity, Distance, TimeDelta, ValueWithUnits

__all__ = [
    # Constants
    "ATTITUDES",
    "BLOCKS",
    "OFFSETS",
    "PHASE_ANGLES",
    # AGM Config
    "AGMConfig",
    "Definition",
    "Frame",
    "Frames",
    "Integration",
    "IntegrationValues",
    "Object",
    "Objects",
    "Param",
    "Parameters",
    # Arrays
    "AnglesVector",
    "AngularVelocityVector",
    "TimesVector",
    "VectorWithUnits",
    # Attitudes
    "Attitude",
    "CaptureAttitude",
    "IlluminatedPointAttitude",
    "InertialAttitude",
    "LimbAttitude",
    "SpecularAttitude",
    "TerminatorAttitude",
    "TrackAttitude",
    "VelocityAttitude",
    # Blocks
    "Block",
    "DownlinkBlock",
    "MNAVBlock",
    "MTCMBlock",
    "MWOLBlock",
    "ObsBlock",
    "SlewBlock",
    "TimedBlock",
    # Directions
    "CrossProductDirection",
    "DerivedDirection",
    "Direction",
    "LonLatDirection",
    "NamedDirection",
    "OriginTargetDirection",
    "ProjectedVectorToPlaneDirection",
    "RotatedDirection",
    "VectorDirection",
    "VelocityDirection",
    # Document
    "Body",
    "Data",
    "Prm",
    "Segment",
    # Metadata
    "Metadata",
    "MWOLMetadata",
    "Observation",
    "Observations",
    "Planning",
    "PlanningSegmentation",
    "SolarArrays",
    "WheelMomentum",
    "WheelMomentumTarget",
    # Offsets
    "CustomOffsetAngles",
    "FixedOffsetAngles",
    "OffsetAngles",
    "RasterOffsetAngles",
    "ScanOffsetAngles",
    # Phase Angles
    "AlignedPhaseAngle",
    "FlipPhaseAngle",
    "PhaseAngle",
    "PowerOptimizedPhaseAngle",
    # Surfaces
    "RefSurface",
    "Surface",
    "SurfaceDefinition",
    # Timeline
    "Timeline",
    # Values
    "Angle",
    "AngularVelocity",
    "Distance",
    "TimeDelta",
    "ValueWithUnits",
    # Unit elements
    "print_known_units",
]
