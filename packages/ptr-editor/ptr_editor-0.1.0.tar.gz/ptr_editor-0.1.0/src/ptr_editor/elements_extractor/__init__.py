"""Human-readable field extractor for PTR attrs classes.

This module provides utilities for extracting and formatting PTR element fields
for human-readable display.
"""

import attrs
from attrs import define, field
from cattrs.gen import make_dict_unstructure_fn_from_attrs
from cattrs.preconf.json import JsonConverter, make_converter

from attrs_xml.xml.converter import register_default_xml_hooks
from ptr_editor import NamedDirection


def unstructure_hook_factory(cls):
    def unstructure_hook(obj):
        result = {}
        for attribute in attrs.fields(cls):
            value = getattr(obj, attribute.name)
            if value is not None:
                result[attribute.name] = str(value)
        return result

    return unstructure_hook


def _setup_initial_converter() -> JsonConverter:
    converter = make_converter()
    register_default_xml_hooks(converter)
    # converter.register_unstructure_hook_factory(
    #     attrs.has, unstructure_hook_factory
    # )
    return converter


@define
class ClassExtractionConfig:
    """Configuration for extracting human-readable fields from a class."""

    props: list[str] = field(factory=list)  # list of property names to extract

    renames: dict[str, str] = field(
        factory=dict,
    )  # mapping of property names to human-readable names


@define
class AttrsHumanReadableFieldExtractor:
    """Processes attrs objects to produce simplified and flat human-readable dict properties."""

    configs: dict[type, ClassExtractionConfig] = field(
        factory=dict,
    )
    _converter = field(factory=_setup_initial_converter, init=False)

    def __attrs_post_init__(self):
        # configure the converter with unstructure hooks for each class
        self._converter.register_unstructure_hook_factory(
            attrs.has, self._unstructure_hook_factory,
        )

    def configure_class(
        self, cls: type, props: list[str], renames: dict[str, str] = {},
    ) -> None:
        self.configs[cls] = ClassExtractionConfig(props=props, renames=renames)

    def _unstructure_hook_factory(self, cls):
        config = self.configs.get(cls)
        if not config:
            return make_dict_unstructure_fn_from_attrs([], cls, self._converter)


        export_attrs = [f for f in attrs.fields_dict(cls).values() if f.name in config.props]
        return make_dict_unstructure_fn_from_attrs(export_attrs, cls, self._converter)

        return unstructure_hook

    def extract_properties(self, obj: object) -> dict[str, str]:
        """Extract human-readable properties from an attrs object.

        Args:
            obj: The attrs object to extract properties from.
        Returns:
            A dictionary of human-readable property names and their string values.
        """

        return self._converter.unstructure(obj)
