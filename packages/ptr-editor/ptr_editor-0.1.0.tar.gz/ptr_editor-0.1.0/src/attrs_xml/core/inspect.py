from typing import Any

import attrs
from attr._make import _CountingAttr


def is_ptr_field(item: _CountingAttr) -> bool:
    """Check if the item is a ptr field."""
    return hasattr(item, "metadata") and "xml_tag" in item.metadata


def ptr_fields(obj: Any):
    """Returns a list of ptr fields from the given object.

    behave exactly like attrs.fields but only returns fields that are ptr fields.
    """
    all_fields = attrs.fields(type(obj))
    return [field for field in all_fields if is_ptr_field(field)]
