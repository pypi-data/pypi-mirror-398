"""
Context management system for ptr-editor.

This module provides:

1. **Defaults**: Immutable, context-managed default values (defaults.py)
2. **Services**: Mutable global service registry (services.py)
3. **Presets**: Pre-configured defaults for common use cases (presets.py)

Key Principles:
- Defaults are configuration (immutable, context-scoped, thread-safe)
- Services are singletons (mutable, global, application-wide)
- Clear separation prevents confusion about what's being configured vs accessed

Examples:
    >>> # Using defaults with context management
    >>> from ptr_editor.context import PointingDefaults
    >>> with PointingDefaults(target="Mars"):
    ...     obs = ObservationRequest()  # Uses Mars as target
    >>> # Automatically restored after context
    >>>
    >>> # Registering and using services
    >>> from ptr_editor.context import get_services
    >>> get_services().register("agm_config", AGMConfiguration)
    >>> config = get_services()["agm_config"]  # Lazy initialization
    >>>
    >>> # Using presets
    >>> from ptr_editor.context import janus_defaults
    >>> with janus_defaults():
    ...     obs = ObservationRequest()  # Uses JANUS configuration
"""

from __future__ import annotations

# Import from submodules
from ptr_editor.context.defaults import (
    DefaultsConfig,
    PointingDefaults,
    from_defaults,
    get_defaults_config,
    set_defaults_config,
)
from ptr_editor.context.presets import janus_defaults, set_janus_defaults
from ptr_editor.context.service_config import (
    ResolutionConfig,
    ServiceConfig,
    ValidationConfig,
    from_service_config,
    get_registered_service_configs,
    get_service_config,
    register_service_config,
    set_service_config,
)
from ptr_editor.context.services import (
    ServiceRegistry,
    from_service,
    get_services,
)

# For backward compatibility, expose internal variables for testing
from ptr_editor.context.defaults import _defaults
from ptr_editor.context.service_config import _service_config
from ptr_editor.context.services import _services

# Import from attrs_xml for convenience
from attrs_xml import are_defaults_disabled, disable_defaults

__all__ = [
    # Defaults
    "DefaultsConfig",
    "PointingDefaults",
    "get_defaults_config",
    "set_defaults_config",
    "from_defaults",
    # Services
    "ServiceRegistry",
    "get_services",
    "from_service",
    # Service Config
    "ServiceConfig",
    "ValidationConfig",
    "ResolutionConfig",
    "get_service_config",
    "set_service_config",
    "register_service_config",
    "get_registered_service_configs",
    "from_service_config",
    # Presets
    "janus_defaults",
    "set_janus_defaults",
    # Default disabling (from attrs_xml)
    "are_defaults_disabled",
    "disable_defaults",
    # Internal (for testing)
    "_defaults",
    "_services",
    "_service_config",
]
