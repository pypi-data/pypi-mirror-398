"""
Service registry for ptr-editor.

This module provides a mutable singleton registry for application services.
Unlike defaults (which are immutable and context-scoped), services are
global singletons with lazy initialization.

Examples:
    >>> # Registering services
    >>> get_services().register("agm_config", AGMConfiguration)
    >>> get_services().register("validator", PTRValidator)
    >>>
    >>> # Using services
    >>> config = get_services()["agm_config"]  # Lazy initialization
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

# Global service registry (singleton)
_services: ServiceRegistry | None = None


__all__ = [
    "ServiceRegistry",
    "get_services",
    "from_service",
]


# ============================================================================
# Service Registry
# ============================================================================


class ServiceRegistry:
    """
    Global registry for application services and singletons.

    This is a mutable singleton registry for services like:
    - AGM configuration
    - Validators
    - Template engines
    - Data accessors

    Unlike defaults, services are NOT context-dependent - they're
    global application state.

    Example:
        >>> services = get_services()
        >>> services.register("agm_config", AGMConfiguration)
        >>> config = services["agm_config"]  # Lazy initialization
    """

    def __init__(self):
        self._factories: dict[str, Callable[[], Any]] = {}
        self._instances: dict[str, Any] = {}
        self._overrides: dict[str, Any] = {}

    def register(self, name: str, factory: Callable[[], T]) -> None:
        """
        Register a factory for lazy initialization.

        Args:
            name: Service name (e.g., "agm_config", "validator")
            factory: Callable that creates the service instance

        Example:
            >>> services = get_services()
            >>> services.register("agm_config", AGMConfiguration)
            >>> services.register("validator", lambda: PTRValidator())
        """
        self._factories[name] = factory

    def get(self, name: str, default: Any = None) -> Any:
        """
        Get a service, creating it lazily if needed.

        Priority:
        1. Explicit override (set via set_override)
        2. Cached instance
        3. Create from factory
        4. Return default

        Args:
            name: Service name
            default: Value to return if service not found

        Returns:
            The service instance

        Raises:
            KeyError: If service not registered and no default provided

        Example:
            >>> services = get_services()
            >>> config = services.get("agm_config")
        """
        if name in self._overrides:
            return self._overrides[name]

        if name in self._instances:
            return self._instances[name]

        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance

        if default is not None:
            return default

        msg = f"Service '{name}' not registered"
        raise KeyError(msg)

    def set_override(self, name: str, instance: Any) -> None:
        """
        Temporarily override a service instance.

        Useful for testing with mocks.

        Args:
            name: Service name
            instance: Instance to use as override

        Example:
            >>> services = get_services()
            >>> services.set_override("agm_config", MockAGMConfig())
        """
        self._overrides[name] = instance

    def clear_override(self, name: str) -> None:
        """
        Remove an override, reverting to cached or factory instance.

        Args:
            name: Service name

        Example:
            >>> services = get_services()
            >>> services.clear_override("agm_config")
        """
        self._overrides.pop(name, None)

    def clear_all_overrides(self) -> None:
        """Remove all overrides."""
        self._overrides.clear()

    def reset(self, name: str) -> None:
        """
        Reset a service to its factory default (clear cache and override).

        Args:
            name: Service name

        Example:
            >>> services = get_services()
            >>> services.reset("agm_config")
        """
        self._overrides.pop(name, None)
        self._instances.pop(name, None)

    def reset_all(self) -> None:
        """Reset all services (clear all caches and overrides)."""
        self._overrides.clear()
        self._instances.clear()

    def has(self, name: str) -> bool:
        """
        Check if a service is registered.

        Args:
            name: Service name

        Returns:
            True if service is registered

        Example:
            >>> services = get_services()
            >>> if services.has("agm_config"):
            ...     config = services["agm_config"]
        """
        return name in self._factories or name in self._overrides

    def __getitem__(self, name: str) -> Any:
        """Dictionary-style access."""
        return self.get(name)

    def __setitem__(self, name: str, value: Any) -> None:
        """Dictionary-style override."""
        self.set_override(name, value)

    def __contains__(self, name: str) -> bool:
        """Check if service exists using 'in' operator."""
        return self.has(name)


def get_services() -> ServiceRegistry:
    """
    Get the global service registry.

    This is a singleton - same instance everywhere in the application.

    Returns:
        The global service registry

    Example:
        >>> services = get_services()
        >>> services.register("agm_config", AGMConfiguration)
    """
    global _services
    if _services is None:
        _services = ServiceRegistry()
    return _services


# ============================================================================
# Field Factory
# ============================================================================


def from_service(service_name: str, attribute_path: str | None = None):
    """
    Create a factory that retrieves from service registry.

    This is for attrs fields that should get their values from
    a registered service.

    Args:
        service_name: Name of the registered service
        attribute_path: Optional dot-separated path to attribute of service

    Returns:
        A factory function suitable for attrs.field(factory=...)

    Example:
        >>> from attrs import define, field
        >>> @define
        ... class Processor:
        ...     config = field(factory=from_service("agm_config"))
    """

    def factory():
        service = get_services().get(service_name)
        if attribute_path:
            parts = attribute_path.split(".")
            value = service
            for part in parts:
                value = getattr(value, part)
            return value() if callable(value) else value
        return service

    name = f"from_service({service_name!r}"
    if attribute_path:
        name += f", {attribute_path!r}"
    name += ")"
    factory.__name__ = name
    return factory
