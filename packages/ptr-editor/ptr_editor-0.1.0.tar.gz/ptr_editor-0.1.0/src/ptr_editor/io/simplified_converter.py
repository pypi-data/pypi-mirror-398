from collections.abc import Callable

import attrs

from attrs_xml.xml.converter import make_default_xml_converter
from ptr_editor.ptr_converter_setup import setup_subclasses_disambiguation
from ptr_editor.elements.array import VectorWithUnits
from ptr_editor.elements.attitude import (
    Attitude,
    InertialAttitude,
    LimbAttitude,
    TrackAttitude,
)
from ptr_editor.elements.blocks import ObsBlock, SlewBlock, TimedBlock
from ptr_editor.elements.directions import (
    LonLatDirection,
    NamedDirection,
    VectorDirection,
)
from ptr_editor.elements.phase_angle import (
    PhaseAngle,
    PowerOptimizedPhaseAngle,
)
from ptr_editor.elements.timeline import Timeline
from ptr_editor.elements.values import ValueWithUnits


def make_unstruct_fn(
    cls: type,
    converter,
    attributes_to_export: list | None = None,
    renames: dict | None = None,
    merge_on_top: list | None = None,
    additional_fields: dict | None = None,
) -> Callable:
    """Generate an unstructure function for a class.

    Args:
        cls: The class to generate the function for
        converter: The cattrs converter to use for unstructuring
        attributes_to_export: List of attribute names to export.
            If empty, exports all.
        renames: Dict mapping original attribute names to new keys
        merge_on_top: List of attributes whose unstructured dict values
            should be merged into the top level (instead of nested)
        additional_fields: Dict mapping field names to callables that
            compute values from the object

    Returns:
        An unstructure function that can be registered with cattrs
    """
    # Handle mutable defaults
    if attributes_to_export is None:
        attributes_to_export = []
    if renames is None:
        renames = {}
    if merge_on_top is None:
        merge_on_top = []
    if additional_fields is None:
        additional_fields = {}

    def unstruct_fn(obj) -> dict:
        data = {}

        # Get all attributes to process
        attrs_to_process = attributes_to_export or [
            f.name for f in attrs.fields(cls)
        ]

        # Process each attribute
        for attr_name in attrs_to_process:
            value = getattr(obj, attr_name)
            unstructured_value = converter.unstructure(value)
            key = renames.get(attr_name, attr_name)

            # Check if this attribute should be merged on top
            if attr_name in merge_on_top and isinstance(
                unstructured_value,
                dict,
            ):
                data.update(unstructured_value)
            else:
                data[key] = unstructured_value

        # Add additional computed fields
        for field_name, compute_fn in additional_fields.items():
            data[field_name] = compute_fn(obj)

        return data

    return unstruct_fn

def _make_extending_unstruct_fn(converter, parent_cls):
    """Create a function that unstructures a subclass by extending parent.

    Args:
        converter: The cattrs converter to use
        parent_cls: The parent class to delegate to for base fields

    Returns:
        A function that takes (obj, additional_fields_dict) and returns dict
    """

    def extend_parent(obj, additional_fields: dict) -> dict:
        """Unstructure by extending parent class serialization."""
        data = converter.unstructure(obj, parent_cls)
        for field_name, field_value in additional_fields.items():
            data[field_name] = converter.unstructure(field_value)
        return data

    return extend_parent


def create_simplified_converter():
    """Create and configure a simplified converter for PTR elements.

    This factory function creates a new converter instance and registers
    all the necessary unstructure hooks for simplified serialization.

    Returns:
        A configured cattrs converter instance
    """
    conv = make_default_xml_converter(rename=False)

    def unstruct_named_direction(obj: NamedDirection) -> str:
        """Simple string extraction for NamedDirection."""
        return obj.ref

    # Generate unstructure functions using make_unstruct_fn

    unstruct_phase_angle = make_unstruct_fn(
        PhaseAngle,
        conv,
        attributes_to_export=["element_type"],
    )

    # PowerOptimizedPhaseAngle: export with field renaming
    unstruct_power_optimized_phase_angle = make_unstruct_fn(
        PowerOptimizedPhaseAngle,
        conv,
        attributes_to_export=["element_type", "angle", "y_dir"],
        renames={"element_type": "phase_angle"},
    )

    # Attitude: export specific fields + merge phase_angle on top + rename type
    unstructure_attitude = make_unstruct_fn(
        Attitude,
        conv,
        attributes_to_export=[
            "element_type",
            "boresight",
            "phase_angle",
            "offset_ref_axis",
            "offset_angles",
        ],
        renames={"element_type": "attitude_type"},
        merge_on_top=["phase_angle"],
    )

    # Create helper for extending parent unstructure
    _extend_attitude = _make_extending_unstruct_fn(conv, Attitude)

    # TrackAttitude: extends Attitude with target field
    def unstruct_tracking_attitude(obj: TrackAttitude) -> dict:
        """Custom unstructure for TrackAttitude that extends Attitude."""
        return _extend_attitude(obj, {"target": obj.target})

    # InertialAttitude: extends Attitude with target field
    def unstruct_inertial_attitude(obj: InertialAttitude) -> dict:
        """Custom unstructure for InertialAttitude that extends Attitude."""
        return _extend_attitude(obj, {"target": obj.target})

    # LimbAttitude: extends Attitude with target_dir, height, and surface
    def unstruct_limb_attitude(obj: LimbAttitude) -> dict:
        """Custom unstructure for LimbAttitude that extends Attitude."""
        return _extend_attitude(
            obj,
            {
                "target_dir": obj.target_dir,
                "height": obj.height,
                "surface": obj.surface,
            },
        )

    # TimedBlock: export all fields + add calculated duration_s
    unstruct_block = make_unstruct_fn(
        TimedBlock,
        conv,
        attributes_to_export=["element_type", "start", "end", "duration"],
        additional_fields={
            "duration_s": lambda obj: obj.duration.total_seconds(),
        },
    )

    # ObsBlock: extends TimedBlock with attitude, observation_id, and designer
    def unstruct_obs_block(obj: ObsBlock) -> dict:
        """Custom unstructure for ObsBlock that extends TimedBlock."""
        data = unstruct_block(obj)
        att = conv.unstructure(obj.attitude)
        data.update(att)
        data["observation_id"] = obj.id
        data["designer"] = obj.designer
        return data

    # SlewBlock: simple type-only export
    unstruct_slew_block = make_unstruct_fn(
        SlewBlock,
        conv,
        attributes_to_export=["element_type"],
    )

    def unstruct_timeline(obj: Timeline) -> list:
        return [conv.unstructure(block) for block in obj.segments]

    # Register all hooks
    conv.register_unstructure_hook(NamedDirection, unstruct_named_direction)
    conv.register_unstructure_hook(PhaseAngle, unstruct_phase_angle)
    conv.register_unstructure_hook(
        PowerOptimizedPhaseAngle,
        unstruct_power_optimized_phase_angle,
    )
    conv.register_unstructure_hook(Attitude, unstructure_attitude)
    conv.register_unstructure_hook(
        TrackAttitude,
        unstruct_tracking_attitude,
    )
    conv.register_unstructure_hook(
        InertialAttitude,
        unstruct_inertial_attitude,
    )
    conv.register_unstructure_hook(LimbAttitude, unstruct_limb_attitude)
    conv.register_unstructure_hook(TimedBlock, unstruct_block)
    conv.register_unstructure_hook(ObsBlock, unstruct_obs_block)
    conv.register_unstructure_hook(SlewBlock, unstruct_slew_block)

    # String conversion hooks - these return str(obj) for various types
    conv.register_unstructure_hook(LonLatDirection, str)
    conv.register_unstructure_hook(ValueWithUnits, str)
    conv.register_unstructure_hook(VectorWithUnits, str)
    conv.register_unstructure_hook(VectorDirection, str)
    conv.register_unstructure_hook(Timeline, unstruct_timeline)

    setup_subclasses_disambiguation(conv)

    return conv


# Module-level converter for backward compatibility
conv = create_simplified_converter()



def unstruct_named_direction(obj: NamedDirection) -> str:
    """Simple string extraction for NamedDirection."""
    return obj.ref



# Generate unstructure functions using make_unstruct_fn

unstruct_phase_angle = make_unstruct_fn(
    PhaseAngle,
    conv,
    attributes_to_export=["element_type"],
)

# PowerOptimizedPhaseAngle: export with field renaming
unstruct_power_optimized_phase_angle = make_unstruct_fn(
    PowerOptimizedPhaseAngle,
    conv,
    attributes_to_export=["element_type", "angle", "y_dir"],
    renames={"element_type": "phase_angle"},
)

# Attitude: export specific fields + merge phase_angle on top + rename type
unstructure_attitude = make_unstruct_fn(
    Attitude,
    conv,
    attributes_to_export=[
        "element_type",
        "boresight",
        "phase_angle",
        "offset_ref_axis",
        "offset_angles",
    ],
    renames={"element_type": "attitude_type"},
    merge_on_top=["phase_angle"],
)


# Create helper for extending parent unstructure
_extend_attitude = _make_extending_unstruct_fn(conv, Attitude)


# TrackAttitude: extends Attitude with target field
def unstruct_tracking_attitude(obj: TrackAttitude) -> dict:
    """Custom unstructure for TrackAttitude that extends Attitude."""
    return _extend_attitude(obj, {"target": obj.target})


# InertialAttitude: extends Attitude with target field
def unstruct_inertial_attitude(obj: InertialAttitude) -> dict:
    """Custom unstructure for InertialAttitude that extends Attitude."""
    return _extend_attitude(obj, {"target": obj.target})


# LimbAttitude: extends Attitude with target_dir, height, and surface fields
def unstruct_limb_attitude(obj: LimbAttitude) -> dict:
    """Custom unstructure for LimbAttitude that extends Attitude."""
    return _extend_attitude(
        obj,
        {
            "target_dir": obj.target_dir,
            "height": obj.height,
            "surface": obj.surface,
        },
    )


# TimedBlock: export all fields + add calculated duration_s
unstruct_block = make_unstruct_fn(
    TimedBlock,
    conv,
    attributes_to_export=["element_type", "start", "end", "duration"],
    additional_fields={"duration_s": lambda obj: obj.duration.total_seconds()},
)


# ObsBlock: extends TimedBlock with attitude, observation_id, and designer
def unstruct_obs_block(obj: ObsBlock) -> dict:
    """Custom unstructure for ObsBlock that extends TimedBlock."""
    data = unstruct_block(obj)
    att = conv.unstructure(obj.attitude)
    data.update(att)
    data["observation_id"] = obj.id
    data["designer"] = obj.designer
    return data


# SlewBlock: simple type-only export
unstruct_slew_block = make_unstruct_fn(
    SlewBlock,
    conv,
    attributes_to_export=["element_type"],
)


conv.register_unstructure_hook(NamedDirection, unstruct_named_direction)
conv.register_unstructure_hook(PhaseAngle, unstruct_phase_angle)
conv.register_unstructure_hook(
    PowerOptimizedPhaseAngle,
    unstruct_power_optimized_phase_angle,
)
conv.register_unstructure_hook(Attitude, unstructure_attitude)
conv.register_unstructure_hook(TrackAttitude, unstruct_tracking_attitude)
conv.register_unstructure_hook(InertialAttitude, unstruct_inertial_attitude)
conv.register_unstructure_hook(LimbAttitude, unstruct_limb_attitude)
conv.register_unstructure_hook(TimedBlock, unstruct_block)
conv.register_unstructure_hook(ObsBlock, unstruct_obs_block)
conv.register_unstructure_hook(SlewBlock, unstruct_slew_block)

# String conversion hooks - these return str(obj) for various types
conv.register_unstructure_hook(LonLatDirection, str)
conv.register_unstructure_hook(ValueWithUnits, str)
conv.register_unstructure_hook(VectorWithUnits, str)
conv.register_unstructure_hook(VectorDirection, str)


def unstruct_timeline(obj: Timeline) -> list:
    return [conv.unstructure(block) for block in obj.segments]


conv.register_unstructure_hook(Timeline, unstruct_timeline)

setup_subclasses_disambiguation(conv)
