"""XML serialization and deserialization components.

This module provides functionality for converting between attrs classes
and XML format, including converters, I/O operations, and utilities.
"""

from .converter import (
    CustomConverter,
    make_default_xml_converter,
    register_default_xml_hooks,
)
from .converters import decode_bool, encode_bool, format_timestamp, to_timestamp
from .io import dump, dumps, get_xml_block, load, loads

__all__ = [
    "CustomConverter",
    "decode_bool",
    "dump",
    "dumps",
    "encode_bool",
    "format_timestamp",
    "get_xml_block",
    "load",
    "loads",
    "make_default_xml_converter",
    "register_default_xml_hooks",
    "to_timestamp",
]
