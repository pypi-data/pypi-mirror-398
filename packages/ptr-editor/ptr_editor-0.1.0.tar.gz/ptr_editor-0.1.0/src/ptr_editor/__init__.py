"""
PTR Editor - A Python library for creating and editing JUICE PTR files.

This package provides tools for working with JUICE Pointing Request (PTR) files,
including reading, writing, and manipulating observation timelines.
"""

from importlib import metadata

from loguru import logger as log
# Package version
__version__ = metadata.version("ptr_editor")

# ============================================================================
# Bootstrap Logging - Must happen FIRST
# ============================================================================

from ptr_editor.core.logging import bootstrap_logging

# Import modules that need logging control BEFORE bootstrap
# This ensures they're loaded and can be properly enabled
import attrs_xml  # noqa: F401
import ptr_solver  # noqa: F401
import time_segments  # noqa: F401

# Initialize logging configuration
bootstrap_logging()

log.info('Logger initialized. Ptr editor Version: {}', __version__)

# ============================================================================
# Bootstrap Services - Must happen BEFORE other imports
# ============================================================================

from ptr_editor.services import bootstrap_ptr_services

# Initialize all services and registries

log.debug('Bootstrapping PTR services...')

bootstrap_ptr_services()

log.debug('Bootstrapping PTR services... done.')

# ============================================================================
# Core Infrastructure
# ============================================================================

from attrs_xml.elements_registry import ElementsRegistry

# ============================================================================
# Accessors
# ============================================================================
from ptr_editor.accessors.accessor import register_accessor

# ============================================================================
# Context Management
# ============================================================================
from ptr_editor.context import (
    DefaultsConfig,
    PointingDefaults,
    ServiceRegistry,
    from_defaults,
    from_service,
    get_defaults_config,
    set_defaults_config,
    get_services,
    janus_defaults,
    set_defaults_config,
)
from ptr_editor.core.logging import (
    IN_JUPYTER,
    bootstrap_logging,
    log,
    set_logger_level,
    setup_logger,
)
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.core.tree_utils import apply_to_attrs_tree, walk_attrs_tree
from ptr_editor.services.quick_access import get_pointing_defaults

# ============================================================================
# Element Classes - Commonly used at package level
# ============================================================================
# Attitudes
from ptr_editor.elements.attitude import (
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

# Blocks
from ptr_editor.elements.blocks import (
    Block,
    DownlinkBlock,
    MNAVBlock,
    MTCMBlock,
    MWOLBlock,
    ObsBlock,
    SlewBlock,
)

# Directions
from ptr_editor.elements.directions import (
    CrossProductDirection,
    DerivedDirection,
    Direction,
    LonLatDirection,
    NamedDirection,
    OriginTargetDirection,
    ProjectedVectorToPlaneDirection,
    RotatedDirection,
    VectorDirection,
)

# Document structure
from ptr_editor.elements.doc import Body, Data, Prm, Segment

# Metadata
from ptr_editor.elements.metadata import (
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

# Offsets
from ptr_editor.elements.offset import (
    CustomOffsetAngles,
    FixedOffsetAngles,
    OffsetAngles,
    RasterOffsetAngles,
    ScanOffsetAngles,
)

# Phase angles
from ptr_editor.elements.phase_angle import (
    AlignedPhaseAngle,
    FlipPhaseAngle,
    PhaseAngle,
    PowerOptimizedPhaseAngle,
)

# Surfaces
from ptr_editor.elements.surface import RefSurface, Surface

# Timeline
from ptr_editor.elements.timeline import Timeline

# Values
from ptr_editor.elements.values import Angle, AngularVelocity, Distance

# Units
from ptr_editor.elements.units import print_known_units  # just the utils

# ============================================================================
# I/O Operations
# ============================================================================
from ptr_editor.io import read_ptr, save_ptr

# ============================================================================
# Registry and Services
# ============================================================================
from ptr_editor.services import quick_access
from ptr_editor.services.quick_access import (
    get_elements_registry,
    get_template_register,
)

from ptr_editor.agm_config import get_agm_configuration



## Utils
from ptr_editor.versioned_file_manager import VersionedFileManager, VersionedFileInfo

# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Version
    "__version__",
    # I/O
    "read_ptr",
    "save_ptr",
    # Context management
    "DefaultsConfig",
    "PointingDefaults",
    "ServiceRegistry",
    "from_defaults",
    "from_service",
    "get_defaults_config",
    "get_services",
    "janus_defaults",
    "set_defaults_config",
    # Registry and services
    "get_elements_registry",
    "get_template_register",
    "get_agm_configuration",
    "quick_access",
    # Core
    "ElementsRegistry",
    "PtrElement",
    "apply_to_attrs_tree",
    "walk_attrs_tree",
    "get_pointing_defaults",
    "set_defaults_config",
    # Accessors
    "register_accessor",
    # Logging
    "IN_JUPYTER",
    "log",
    "set_logger_level",
    "setup_logger",
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
    # Document
    "Body",
    "Data",
    "Prm",
    "Segment",
    # Metadata
    "MWOLMetadata",
    "Metadata",
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
    # Phase angles
    "AlignedPhaseAngle",
    "FlipPhaseAngle",
    "PhaseAngle",
    "PowerOptimizedPhaseAngle",
    # Surfaces
    "RefSurface",
    "Surface",
    # Timeline
    "Timeline",
    # Values
    "Angle",
    "AngularVelocity",
    "Distance",
    # Units
    "print_known_units",
]

