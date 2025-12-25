from __future__ import annotations

from functools import partial
from typing import Any

import pandas as pd
from attrs import field

from attrs_xml.core.sentinels import _UnsetType


def _time_converter(x:str | pd.Timestamp | _UnsetType) -> pd.Timestamp | None:
    """Convert time values, preserving UNSET sentinel."""

    from attrs_xml.core.sentinels import UNSET

    if callable(x):
        return x  # leave callables unchanged to support lazy initialization

    if x is UNSET:
        return UNSET
    if x:
        ts = pd.Timestamp(x)
        if ts.tz is not None:
            ts = ts.tz_convert("UTC")
            ts = ts.tz_convert(None)  # strip localization
        return ts
    return None


def _custom_field(
    *,
    tag: str | None = None,
    tag_aliases: str | list[str] | None = None,
    xml_type=None,
    cattrs_omit: bool = False,
    post_converter=None,  # function that process the value after the automated one
    **kwargs,
) -> Any:
    """Wraps around attrs.field to add metadata for XML serialization.
    
    Args:
        tag: The primary XML tag name for this field
        tag_aliases: Alternative tag names to look for during structuring if the primary tag is missing.
                    Can be a single string or a list of strings.
        xml_type: Type of XML element ("text", "attr", or None for element)
        cattrs_omit: Whether to omit this field during cattrs structuring
        post_converter: Function to process the value after automated conversion
        **kwargs: Additional arguments passed to attrs.field()
    """
    mdata = kwargs.pop("metadata", {})
    mdata["xml_tag"] = tag
    mdata["xml_type"] = xml_type
    mdata["cattrs_omit"] = cattrs_omit
    
    # Normalize tag_aliases to a list
    if tag_aliases is not None:
        if isinstance(tag_aliases, str):
            tag_aliases = [tag_aliases]
        mdata["tag_aliases"] = tag_aliases
    
    if post_converter:
        mdata["post_converter"] = post_converter

    kwargs["metadata"] = mdata

    return field(**kwargs)


text = partial(_custom_field, xml_type="text")
attr = partial(_custom_field, xml_type="attr")
element = _custom_field
time_element = partial(
    element,
    converter=_time_converter,
)
