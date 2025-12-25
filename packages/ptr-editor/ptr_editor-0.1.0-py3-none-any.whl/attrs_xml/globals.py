from contextlib import contextmanager
from contextvars import ContextVar

from attrs import define


@define
class GlobalConfig:
    global_disable_dict_renames: bool = False


global_config = GlobalConfig()

# Context variable to control whether defaults should be applied
_defaults_disabled: ContextVar[bool] = ContextVar("_defaults_disabled", default=False)


def are_defaults_disabled() -> bool:
    """Check if defaults are currently disabled."""
    return _defaults_disabled.get()


@contextmanager
def disable_defaults():
    """Context manager to disable default value handling.
    
    When active, fields with defaults will return None instead of their
    default values. This is useful when loading from files where you want
    to distinguish between explicitly set values and defaults.
    
    Example:
        >>> with disable_defaults():
        ...     obj = MyClass()  # All defaults become None
    """
    token = _defaults_disabled.set(True)
    try:
        yield
    finally:
        _defaults_disabled.reset(token)
