from __future__ import annotations

from typing import Literal

import pint
from attr import fields_dict

from attrs_xml import attr, element_define, text
from attrs_xml.core.decorators_utils import classproperty
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.units import (
    ANGULAR_UNITS_LITERAL,
    ANGULAR_VELOCITY_UNITS_LITERAL,
    DELTA_TIME_UNITS_LITERAL,
    DISTANCE_UNITS_LITERAL,
)


def _parse_value_with_units(value_str: str) -> tuple[float | int, str]:
    """
    Parse a string in the format "value units" into a tuple of (parsed_value, units).

    Args:
        value_str: String in format "123.45 km" or "42 deg"

    Returns:
        Tuple of (parsed_value, units) where parsed_value is int if possible, else float

    Raises:
        ValueError: If the string format is invalid or value cannot be parsed as numeric
    """
    parts = value_str.split()
    if len(parts) != 2:
        msg = f"Invalid format for ValueWithUnits: {value_str}"
        raise ValueError(msg)

    value_part, units = parts

    # Try to parse as int first (preserves type), then float
    for converter in (int, float):
        try:
            parsed_value = converter(value_part)
            return parsed_value, units
        except ValueError:
            continue

    # If both failed
    msg = f"Invalid value part in ValueWithUnits: {value_part}"
    raise ValueError(msg)


def parse_value_string(value: str | float) -> int | float:
    """
    Parse a value string into an int or float.

    Args:
        value: The value string to parse.

    Returns:
        int or float: The parsed numeric value.
    """
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)

    try:
        return int(value)
    except ValueError:
        return float(value)


@element_define
class ValueWithUnits(PtrElement):
    value: float | int = text(converter=parse_value_string, eq=float, default=0)
    units: Literal[""] = attr(default="")



    @classmethod
    def _parse_numeric_string(cls, value_str: str) -> int | float:
        """Parse a numeric string, preserving int type if possible."""
        for converter in (int, float):
            try:
                return converter(value_str)
            except ValueError:
                continue
        msg = f"Cannot parse '{value_str}' as a number"
        raise ValueError(msg)

    @classmethod
    def _from_string(cls, value: str) -> ValueWithUnits:
        """Create instance from string, handling both 'value units' and 'value' formats."""
        parts = value.split()

        if len(parts) == 2:
            # Standard "value units" format
            parsed_value, units = _parse_value_with_units(value)
            return cls(value=parsed_value, units=units)

        if len(parts) == 1:
            # Only numeric value, use default units
            parsed_value = cls._parse_numeric_string(parts[0])
            return cls(value=parsed_value, units=cls.default_units)

        # Invalid format
        msg = (
            f"Invalid format for ValueWithUnits: {value}. "
            "Expected 'value units' or just 'value'"
        )
        raise ValueError(msg)

    @classmethod
    def from_string(cls, value: str | ValueWithUnits | None) -> ValueWithUnits | None:
        """
        Create a ValueWithUnits instance from various input types.

        Args:
            value: Input value - can be None, numeric, string, or existing ValueWithUnits

        Returns:
            ValueWithUnits instance or None

        Raises:
            TypeError: If input type is not supported
            ValueError: If string format is invalid
        """
        if value is None:
            return None

        if isinstance(value, ValueWithUnits):
            return value

        if isinstance(value, (int, float)):
            return cls(value=value, units=cls.default_units)

        if isinstance(value, str):
            return cls._from_string(value)

        msg = (
            f"Invalid type for ValueWithUnits: {type(value)}. "
            "Expected str, numeric, or ValueWithUnits."
        )
        raise TypeError(msg)

    @classproperty
    def default_units(cls) -> str:
        import attrs
        
        default_units = fields_dict(cls)["units"].default
        
        # Handle attrs.Factory objects (from disable_defaults wrapping)
        if isinstance(default_units, attrs.Factory):
            return default_units.factory()
        
        # defaults units might be a callable, so we need to call it if it is
        if callable(default_units):
            return default_units()

        return default_units

    def value_to_unit(self, unit: str) -> float:
        """
        Convert the value to the specified unit.

        Args:
            unit: The unit to convert to.

        Returns:
            The value converted to the specified unit.
        """
        q = pint.Quantity(self.value, self.units)
        return q.to(unit).magnitude

    def __str__(self) -> str:
        return f"{self.value} {self.units}"


@element_define
class Angle(ValueWithUnits):
    units: ANGULAR_UNITS_LITERAL = attr(
        default="deg",
        converter=str,
    )


@element_define
class Distance(ValueWithUnits):
    units: DISTANCE_UNITS_LITERAL = attr(
        default="km",
        converter=str,
    )


@element_define
class TimeDelta(ValueWithUnits):
    units: DELTA_TIME_UNITS_LITERAL = attr(
        default="sec",
        converter=str,
    )


@element_define
class AngularVelocity(ValueWithUnits):
    units: ANGULAR_VELOCITY_UNITS_LITERAL = attr(
        default="deg/sec",
        converter=str,
    )


VALUES = Angle | Distance | TimeDelta | AngularVelocity
