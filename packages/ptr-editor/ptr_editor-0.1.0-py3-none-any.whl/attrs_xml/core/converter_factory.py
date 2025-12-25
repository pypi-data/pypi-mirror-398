"""Converter factory for automatic type conversion.

This module provides the ValueConverter and ConverterFactory classes that
handle automatic type conversion using the resolution system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any



if TYPE_CHECKING:
    from collections.abc import Callable

    from attrs_xml.core.type_utils import TypeInfo


class ValueConverter:
    """Handles conversion of values to target types using resolution strategies.

    This class uses the pluggable resolution system to convert values.
    The resolution system applies registered strategies in priority order.
    """

    def __init__(self, type_info: TypeInfo, registry=None):
        self.type_info = type_info
        self._registry = registry


    @property
    def registry(self):
        """Get the resolution registry."""
        from attrs_xml.resolution.registry import get_default_registry
        return self._registry or get_default_registry()

    def convert(self, value: Any) -> Any:
        """Convert value to the target type(s) using resolution strategies."""
        from attrs_xml.resolution import ResolutionContext

        # Create resolution context with all necessary information
        context = ResolutionContext(
            value=value,
            target_types=self.type_info.resolved_types,
            is_optional=self.type_info.is_optional,
            has_unset=self.type_info.has_unset,
        )

        # Let the resolution registry handle it
        return self.registry.resolve(context)


class ConverterFactory:
    """Creates converter functions using the resolution system.

    This factory builds converter functions that delegate to the resolution
    system for type conversion.
    """

    def __init__(self, type_info: TypeInfo):
        self.type_info = type_info

    def create(self) -> Callable[[str], Any]:
        """Create a converter function."""
        value_converter = ValueConverter(self.type_info)

        def convert_value(value: str) -> Any:
            return value_converter.convert(value)

        # Add metadata for debugging
        type_name = self._format_type_name()
        convert_value.__name__ = f"converter_for_{type_name}"
        convert_value.__doc__ = f"Auto-generated converter for {type_name}"

        return convert_value

    def _format_type_name(self) -> str:
        """Format type name for debugging."""
        if self.type_info.is_union:
            names = [
                getattr(t, "__name__", str(t)) for t in self.type_info.resolved_types
            ]
            return "_or_".join(names)
        return getattr(
            self.type_info.single_type,
            "__name__",
            str(self.type_info.single_type),
        )
