import sys
from importlib import metadata

from loguru import logger as log

log.disable("attrs_xml")  # disable prior to anything else


# Try to get version from parent package (ptr_editor), otherwise use a default
try:
    __version__ = metadata.version("ptr_editor")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0-dev"


def log_enable(
    level: str = "INFO",
    mod: str = "attrs_xml",
    remove_handlers: bool = True,
) -> None:
    """Enable logging for a given module at specific level, by default it operates on the whole module."""
    if remove_handlers:
        log.remove()
    log.enable(mod)
    log.add(sys.stderr, level=level)


def log_enable_debug() -> None:
    """Enable debug logging for a given module, by default it operates on the whole module."""
    log_enable(level="DEBUG")


def log_disable(mod: str = "attrs_xml") -> None:
    """Totally disable logging from this module, by default it operates on the whole module."""
    log.disable(mod)


# Import from reorganized structure
from attrs_xml.core import (
    UNSET,
    BaseElement,
    ElementGenerator,
    PtrElementGenerator,
    _UnsetType,
    attr,
    element,
    element_define,
    is_set,
    require_set,
    text,
    time_element,
)
from attrs_xml.elements_registry import ElementsRegistry
from attrs_xml.globals import are_defaults_disabled, disable_defaults

__all__ = [
    "UNSET",
    "BaseElement",
    "ElementGenerator",
    "ElementsRegistry",
    "PtrElementGenerator",
    "_UnsetType",
    "__version__",
    "are_defaults_disabled",
    "attr",
    "disable_defaults",
    "element",
    "element_define",
    "is_set",
    "log_disable",
    "log_enable",
    "log_enable_debug",
    "require_set",
    "text",
    "time_element",
]
