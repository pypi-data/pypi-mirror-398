import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from loguru import logger as log

from ptr_editor.elements import ObsBlock, SlewBlock

datetime_regex = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
)
int_regex = re.compile(r"^[+-]?\d+$")
float_regex = re.compile(r"^[+-]?(?:\d*\.\d+|\d+\.\d*)([eE][+-]?\d+)?$")
timedelta_regex = re.compile(r"\s*[+-]?[0-9]{2}:[0-9]{2}:[0-9]{2}.*")


def is_list_of_numbers(val: str) -> bool:
    """Check if a string is a list of numbers."""
    parts = val.strip().split()
    if len(parts) > 1:
        return all(
            int_regex.fullmatch(p.strip()) or float_regex.fullmatch(p.strip())
            for p in parts
        )
    return int_regex.fullmatch(val.strip()) or float_regex.fullmatch(val.strip())


def is_int_representable(x: Any) -> bool:
    """Check if a value can be represented as an integer without loss of precision.

    Args:
        x: Value to check (can be string, float, or int)

    Returns:
        bool: True if the value equals its integer conversion, False otherwise

    Examples:
        >>> is_int_representable(
        ...     "42.0"
        ... )
        True
        >>> is_int_representable(
        ...     "42.5"
        ... )
        False
    """
    try:
        x = float(x)  # must first be float representable
    except ValueError:
        return False
    return x == int(x)


def is_float_representable(val: Any) -> bool:
    """Check if a string can be represented as a float."""
    try:
        float(val)
        return True
    except ValueError:
        return False


def normalize_datetime(val: str | pd.Timestamp) -> str:
    """Normalize a datetime value to ISO format in UTC timezone.

    Ensures consistent datetime representation by:
    1. Converting to pandas Timestamp
    2. Converting to UTC (localizing if naive, converting if timezone-aware)
    3. Formatting as ISO 8601 string

    Args:
        val: Datetime value as string or pandas Timestamp

    Returns:
        str: ISO 8601 formatted datetime string in UTC

    Examples:
        >>> normalize_datetime(
        ...     "2024-01-15T10:30:00+01:00"
        ... )
        '2024-01-15T09:30:00+00:00'
    """
    dt = pd.Timestamp(val)

    dt = dt.tz_localize(UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.isoformat()


def normalize_timedelta(val: str | pd.Timedelta) -> str:
    """Normalize a timedelta"""
    try:
        td = pd.Timedelta(val)
        return str(td)
    except ValueError as e:
        msg = f"Value {val} could not be converted to a valid timedelta."
        log.exception(msg)
        raise ValueError(msg) from e


def normalize_number(val: Any) -> str:
    """Normalize a numeric value to its simplest string representation.

    Converts floats that are whole numbers to integers (e.g., "42.0" -> "42").
    If the value cannot be converted to a number, returns it unchanged.

    Args:
        val: Value to normalize (string, int, or float)

    Returns:
        str: Normalized number as string, or original value if not numeric

    Examples:
        >>> normalize_number(
        ...     "42.0"
        ... )
        '42'
        >>> normalize_number(
        ...     "3.14"
        ... )
        '3.14'
        >>> normalize_number(
        ...     "not_a_number"
        ... )
        'not_a_number'
    """
    try:
        return str(int(val))
    except ValueError:
        try:
            return str(float(val))
        except ValueError:
            # If it can't be converted to int or float, return the original value
            return val
    return val


def normalize_number_list(val: str) -> str:
    """Normalize a space-separated list of numbers.

    Processes each number in the list:
    - Converts whole number floats to integers ("1.0" -> "1")
    - Normalizes float representations
    - Joins with single spaces

    Args:
        val: Space-separated string of numbers

    Returns:
        str: Normalized space-separated string of numbers

    Examples:
        >>> normalize_number_list(
        ...     "1.0  2.5   3.0"
        ... )
        '1 2.5 3'
    """
    parts = val.strip().split()
    newitems = []
    if len(parts) > 1:
        for item in parts:
            if is_int_representable(item):
                item = str(int(float(item)))
            elif is_float_representable(item):
                item = str(float(item))

            newitems.append(item)
        return " ".join(newitems)
    return normalize_number(val)


def auto_normalize(val: str) -> str:
    """Automatically detect and normalize value type.

    Attempts to detect the value type using regex patterns and type checks,
    then applies the appropriate normalization:
    1. Timedelta (HH:MM:SS format) -> normalized timedelta string
    2. Datetime (ISO 8601) -> UTC ISO format
    3. Integer-representable number -> integer string
    4. Float -> float string
    5. Space-separated numbers -> normalized number list
    6. Other -> unchanged

    Args:
        val: String value to normalize

    Returns:
        str: Normalized value as string

    Examples:
        >>> auto_normalize(
        ...     "2024-01-15T10:30:00+01:00"
        ... )
        '2024-01-15T09:30:00+00:00'
        >>> auto_normalize(
        ...     "42.0"
        ... )
        '42'
        >>> auto_normalize(
        ...     "1.0 2.0 3.0"
        ... )
        '1 2 3'
    """
    if timedelta_regex.fullmatch(val):
        log.debug(f"matching timedelta: {val}")
        return normalize_timedelta(val)
    if datetime_regex.fullmatch(val):
        log.debug(f"matching datetime: {val}")
        return normalize_datetime(val)
    if is_int_representable(val):
        log.debug(f"matching int: {val}")
        return str(int(float(val)))
    if is_float_representable(val):
        log.debug(f"matching float: {val}")
        return str(float(val))
    if is_list_of_numbers(val):
        log.debug(f"matching list of numbers: {val}")
        return normalize_number_list(val)

    return val


# Tag-specific normalization rules for text content
# Map tag names to normalization functions
TAG_TEXT_NORMALIZATIONS: dict[str, Callable[[str], str]] = {
    # Add tag-specific text normalizations here as needed
    # "example_tag": lambda text: text.lower(),
}


# Attribute-specific normalization rules
# Map (tag_name, attribute_name) to normalization functions
ATTRIBUTE_NORMALIZATIONS: dict[tuple[str, str], Callable[[str], str]] = {
    ("target", "ref"): lambda val: val.upper(),  # Case-insensitive for target/@ref
    ("boresight", "ref"): lambda val: val.upper(),  # Case-insensitive for boresight/@ref
    # Add more attribute-specific normalizations here as needed
    # ("example_tag", "example_attr"): lambda val: val.lower(),
}


def normalize_tag_text(tag_name: str, text: str) -> str:
    """
    Apply tag-specific normalization to text content.

    Args:
        tag_name: The XML tag name
        text: The text content to normalize

    Returns:
        Normalized text content
    """
    if tag_name in TAG_TEXT_NORMALIZATIONS:
        normalized = TAG_TEXT_NORMALIZATIONS[tag_name](text)
        if normalized != text:
            log.debug(
                f"Tag-specific text normalization for <{tag_name}>: {text!r} -> {normalized!r}",
            )
        return normalized
    return text


def normalize_attribute_value(tag_name: str, attr_name: str, value: str) -> str:
    """
    Apply tag and attribute-specific normalization to attribute values.

    Uses XPath-like targeting: (tag_name, attr_name) tuples identify specific normalizations.

    Args:
        tag_name: The XML tag name
        attr_name: The attribute name
        value: The attribute value to normalize

    Returns:
        Normalized attribute value
    """
    key = (tag_name, attr_name)
    if key in ATTRIBUTE_NORMALIZATIONS:
        normalized = ATTRIBUTE_NORMALIZATIONS[key](value)
        if normalized != value:
            log.debug(
                f"Attribute normalization for <{tag_name} {attr_name}={value!r}>: {value!r} -> {normalized!r}",
            )
        return normalized
    return value


def sort_elements_and_normalize_values(
    elem: ET.Element, normalize_attrs: bool = False,
) -> ET.Element:
    """Recursively sort and normalize an XML element tree.

    Performs the following operations bottom-up:
    1. Recursively processes all child elements
    2. Normalizes attribute values (with optional auto-normalization)
    3. Applies tag-specific attribute normalizations
    4. Sorts attributes alphabetically
    5. Normalizes text content
    6. Applies tag-specific text normalizations
    7. Sorts child elements by tag name and content

    Args:
        elem: XML Element to process (from xml.etree.ElementTree)
        normalize_attrs: If True, auto-normalize attribute values (datetimes, numbers)
                        If False, only strip whitespace from attributes

    Returns:
        The same element (modified in place)

    Note:
        This function modifies the element tree in place.
    """
    # Normalize attributes (including datetimes and numbers)
    # we normalize bottom up, so we can normalize the children first
    for child in elem:
        sort_elements_and_normalize_values(child)

    for k, v in elem.attrib.items():
        original_value = v
        newvalue = auto_normalize(v) if normalize_attrs else v.strip()

        # Apply tag-specific attribute normalization
        newvalue = normalize_attribute_value(elem.tag, k, newvalue)

        elem.attrib[k] = newvalue
        if elem.attrib[k] != original_value:
            log.debug(
                f"Normalized attribute {k} from {original_value} to {elem.attrib[k]}",
            )

    elem.attrib = dict(sorted(elem.attrib.items()))
    # # Normalize text if it's a datetime, else as number or number list if possible
    if elem.text:
        text = auto_normalize(elem.text.strip())
        # Apply tag-specific normalization
        text = normalize_tag_text(elem.tag, text)
        elem.text = text
    if elem.tail:
        elem.tail = elem.tail.strip()
    # Sort children by tag name and then recursively sort their contents

    elem[:] = sorted(
        elem,
        key=lambda e: (e.tag, ET.tostring(e, encoding="unicode")),
    )

    return elem


def normalize_xml(xml_str: str) -> str:
    """Parse and normalize XML for consistent comparison.

    Performs comprehensive normalization:
    - Removes newlines and tabs from input
    - Parses XML to element tree
    - Sorts attributes alphabetically
    - Sorts child elements by tag name and content
    - Normalizes all values (datetimes to UTC, numbers to simplest form)
    - Applies tag-specific and attribute-specific normalizations
    - Pretty-prints with consistent indentation

    This ensures that semantically equivalent XML documents produce identical
    normalized output, regardless of:
    - Attribute order
    - Element order (for same-named siblings)
    - Whitespace formatting
    - Number representation (42.0 vs 42)
    - Datetime timezone representation

    Args:
        xml_str: XML string to normalize

    Returns:
        str: Normalized and pretty-printed XML string

    Examples:
        >>> xml1 = '<root b="2" a="1"><child>42.0</child></root>'
        >>> xml2 = '<root a="1" b="2"><child>42</child></root>'
        >>> normalize_xml(
        ...     xml1
        ... ) == normalize_xml(
        ...     xml2
        ... )
        True
    """
    xml_str = xml_str.strip().replace("\n", "").replace("\t", "")
    root = ET.fromstring(xml_str)
    sort_elements_and_normalize_values(root)
    # Pretty-print using minidom
    import xml.dom.minidom

    text_xml = ET.tostring(root, encoding="unicode")
    return xml.dom.minidom.parseString(text_xml).toprettyxml(indent="  ")


def assert_xml_equal(xml1: str, xml2: str) -> None:
    """Assert that two XML strings are semantically equal after normalization.

    Normalizes both XML strings and compares them for equality.
    This enables testing XML parsing/serialization roundtrips without
    being affected by formatting differences, attribute order, or
    value representation variations.

    Args:
        xml1: First XML string to compare
        xml2: Second XML string to compare

    Raises:
        AssertionError: If the normalized XML strings are not equal

    Examples:
        >>> xml1 = "<root><value>42.0</value></root>"
        >>> xml2 = "<root><value>42</value></root>"
        >>> assert_xml_equal(
        ...     xml1, xml2
        ... )  # Passes - semantically equal

    See Also:
        normalize_xml: For details on normalization process
    """
    norm1 = normalize_xml(xml1)
    norm2 = normalize_xml(xml2)

    assert norm1 == norm2
