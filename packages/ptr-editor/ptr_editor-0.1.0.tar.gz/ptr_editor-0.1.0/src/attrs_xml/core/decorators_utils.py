"""Utility functions and classes for attrs_xml core functionality."""

from __future__ import annotations


def remove_empty_items(d):
    """Recursively remove all empty items from a nested dictionary."""
    if not isinstance(d, dict):
        return d

    cleaned_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            nested_dict = remove_empty_items(v)
            if nested_dict:
                cleaned_dict[k] = nested_dict
        elif v:
            cleaned_dict[k] = v

    return cleaned_dict


class classproperty:  # noqa: N801
    """Decorator to create class-level properties."""

    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)
