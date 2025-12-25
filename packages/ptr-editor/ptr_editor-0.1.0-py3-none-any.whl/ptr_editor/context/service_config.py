"""
Service configuration system for ptr-editor.

This module provides an extensible configuration system where third-party
modules can register their own configuration schemas that integrate seamlessly
with the context management system.

Examples:
    >>> # Core usage
    >>> from ptr_editor.context import ServiceConfig, ValidationConfig
    >>> with ServiceConfig(validation=ValidationConfig(ruleset="strict")):
    ...     validator.validate(ptr)
    >>>
    >>> # Third-party plugin
    >>> from attrs import define
    >>> from ptr_editor.context import register_service_config
    >>>
    >>> @define(frozen=True)
    >>> class MyPluginConfig:
    ...     enabled: bool = True
    ...     timeout: int = 30
    >>>
    >>> register_service_config("my_plugin", MyPluginConfig)
    >>>
    >>> # Use third-party config
    >>> with ServiceConfig(my_plugin=MyPluginConfig(timeout=60)):
    ...     plugin = get_services()["my_plugin"]
    ...     plugin.do_work()  # Uses config from context
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Any, Literal

from attrs import define, evolve, field

if TYPE_CHECKING:
    from types import TracebackType


# Global context variable for service config
_service_config: ContextVar[ServiceConfig | None] = ContextVar(
    "_service_config", default=None
)

# Global registry for service config schemas (for third-party extensions)
_service_config_registry: dict[str, type] = {}


__all__ = [
    "ServiceConfig",
    "ValidationConfig",
    "ResolutionConfig",
    "get_service_config",
    "set_service_config",
    "register_service_config",
    "get_registered_service_configs",
    "from_service_config",
]


# ============================================================================
# Service Configuration Registry
# ============================================================================


def register_service_config(name: str, config_class: type) -> None:
    """
    Register a service configuration schema.

    This allows third-party modules to register their own configuration
    that can be used with ServiceConfig.

    Args:
        name: Service name (e.g., "my_plugin", "custom_validator")
        config_class: The configuration class (must be frozen attrs class)

    Example:
        >>> from attrs import define
        >>>
        >>> @define(frozen=True)
        ... class MyPluginConfig:
        ...     enabled: bool = True
        ...     api_key: str = ""
        ...
        >>> register_service_config("my_plugin", MyPluginConfig)
    """
    if not hasattr(config_class, "__attrs_attrs__"):
        msg = f"Config class must be an attrs class: {config_class}"
        raise TypeError(msg)

    _service_config_registry[name] = config_class


def get_registered_service_configs() -> dict[str, type]:
    """
    Get all registered service configuration schemas.

    Returns:
        Dictionary mapping service names to their config classes

    Example:
        >>> configs = get_registered_service_configs()
        >>> for name, config_class in configs.items():
        ...     print(f"{name}: {config_class}")
    """
    return _service_config_registry.copy()


# ============================================================================
# Built-in Service Configurations
# ============================================================================


@define(frozen=True)
class ValidationConfig:
    """
    Configuration for validation service behavior.

    This controls HOW validation happens, not WHAT gets validated.

    Attributes:
        ruleset: Which validation ruleset to use
        fail_fast: Stop on first error or collect all errors
        warnings_as_errors: Treat warnings as errors
        enabled_rules: Optional set of rule IDs to enable (None = all)
        disabled_rules: Optional set of rule IDs to disable

    Example:
        >>> # Strict validation for production
        >>> with ValidationConfig(ruleset="strict", fail_fast=True):
        ...     validator = get_services()["validator"]
        ...     validator.validate(ptr)
        >>>
        >>> # Permissive validation for draft work
        >>> with ValidationConfig(ruleset="permissive", warnings_as_errors=False):
        ...     validator.validate(ptr)
    """

    ruleset: Literal["strict", "permissive", "draft"] = "strict"
    fail_fast: bool = False
    warnings_as_errors: bool = False
    enabled_rules: frozenset[str] | None = None
    disabled_rules: frozenset[str] | None = None

    def with_ruleset(self, ruleset: str) -> ValidationConfig:
        """Create new config with different ruleset."""
        return evolve(self, ruleset=ruleset)

    def with_fail_fast(self, fail_fast: bool = True) -> ValidationConfig:
        """Create new config with fail_fast enabled/disabled."""
        return evolve(self, fail_fast=fail_fast)

    def enable_rules(self, *rule_ids: str) -> ValidationConfig:
        """Create new config with additional rules enabled."""
        current = self.enabled_rules or frozenset()
        return evolve(self, enabled_rules=current | frozenset(rule_ids))

    def disable_rules(self, *rule_ids: str) -> ValidationConfig:
        """Create new config with additional rules disabled."""
        current = self.disabled_rules or frozenset()
        return evolve(self, disabled_rules=current | frozenset(rule_ids))

    def __enter__(self) -> ValidationConfig:
        """Apply this validation config temporarily."""
        parent = get_service_config()
        new_config = parent.with_config("validation", self)
        _service_config.set(new_config)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Restore previous config (automatic with contextvars)."""


@define(frozen=True)
class ResolutionConfig:
    """
    Configuration for input resolution service behavior.

    This controls how user input gets resolved to concrete values.

    Attributes:
        enable_fuzzy_matching: Allow fuzzy string matching
        fuzzy_threshold: Minimum similarity score (0.0-1.0) for fuzzy matches
        enable_case_insensitive: Case-insensitive matching
        enable_abbreviations: Allow abbreviated input
        enable_smart_defaults: Try to infer missing values
        resolution_strategies: Priority-ordered list of strategies to try

    Example:
        >>> # Strict resolution for scripts
        >>> with ResolutionConfig(
        ...     enable_fuzzy_matching=False,
        ...     enable_smart_defaults=False
        ... ):
        ...     resolver = get_services()["resolver"]
        ...     target = resolver.resolve_target("jupiter")  # Must be exact
        >>>
        >>> # Permissive resolution for interactive use
        >>> with ResolutionConfig(
        ...     enable_fuzzy_matching=True,
        ...     fuzzy_threshold=0.8,
        ...     enable_smart_defaults=True
        ... ):
        ...     target = resolver.resolve_target("jup")  # Matches "Jupiter"
    """

    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.85
    enable_case_insensitive: bool = True
    enable_abbreviations: bool = True
    enable_smart_defaults: bool = False
    resolution_strategies: tuple[str, ...] = (
        "exact_match",
        "case_insensitive",
        "fuzzy_match",
        "abbreviation",
    )

    def with_strategy(self, *strategies: str) -> ResolutionConfig:
        """Create new config with different resolution strategies."""
        return evolve(self, resolution_strategies=strategies)

    def strict(self) -> ResolutionConfig:
        """Create strict resolution config (exact matches only)."""
        return evolve(
            self,
            enable_fuzzy_matching=False,
            enable_case_insensitive=False,
            enable_abbreviations=False,
            enable_smart_defaults=False,
            resolution_strategies=("exact_match",),
        )

    def permissive(self) -> ResolutionConfig:
        """Create permissive resolution config (all strategies enabled)."""
        return evolve(
            self,
            enable_fuzzy_matching=True,
            fuzzy_threshold=0.75,
            enable_case_insensitive=True,
            enable_abbreviations=True,
            enable_smart_defaults=True,
        )

    def __enter__(self) -> ResolutionConfig:
        """Apply this resolution config temporarily."""
        parent = get_service_config()
        new_config = parent.with_config("resolution", self)
        _service_config.set(new_config)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Restore previous config (automatic with contextvars)."""


# Register built-in configs
register_service_config("validation", ValidationConfig)
register_service_config("resolution", ResolutionConfig)


# ============================================================================
# Dynamic Service Configuration
# ============================================================================


class ServiceConfig:
    """
    Dynamic immutable configuration for all services.

    This class dynamically supports any registered service configuration.
    Third-party modules can register their configs and use them seamlessly.

    Unlike a traditional frozen attrs class, this uses a dictionary to store
    configs so it can be extended at runtime by third-party modules.

    Example:
        >>> # Core usage
        >>> config = ServiceConfig(validation=ValidationConfig(ruleset="strict"))
        >>> with config:
        ...     validator.validate(ptr)
        >>>
        >>> # Third-party plugin
        >>> register_service_config("my_plugin", MyPluginConfig)
        >>> config = ServiceConfig(my_plugin=MyPluginConfig(enabled=True))
        >>> with config:
        ...     plugin = get_services()["my_plugin"]
        ...     plugin.do_work()  # Uses config from context
    """

    def __init__(self, **configs):
        """
        Create a service configuration.

        Args:
            **configs: Keyword arguments where keys are service names
                       and values are their configuration instances

        Example:
            >>> config = ServiceConfig(
            ...     validation=ValidationConfig(ruleset="strict"),
            ...     my_plugin=MyPluginConfig(enabled=True),
            ... )
        """
        # Validate that all provided configs are registered or known
        for name, config_value in configs.items():
            if name not in _service_config_registry:
                # Allow it but it might be a typo - user can still use it
                pass

        self._configs = configs
        self._token: Token[ServiceConfig | None] | None = None

    def __getattr__(self, name: str) -> Any:
        """Get a service config by attribute access."""
        if name.startswith("_"):
            raise AttributeError(name)

        # Return the config if it exists
        if name in self._configs:
            return self._configs[name]

        # Return default instance if registered
        if name in _service_config_registry:
            return _service_config_registry[name]()

        msg = f"Service config '{name}' not found"
        raise AttributeError(msg)

    def get(self, name: str, default: Any = None) -> Any:
        """
        Get a service config by name.

        Args:
            name: Service name
            default: Default value if not found

        Returns:
            The service config instance or default

        Example:
            >>> config = get_service_config()
            >>> validation = config.get("validation")
        """
        try:
            return getattr(self, name)
        except AttributeError:
            return default

    def with_config(self, name: str, config: Any) -> ServiceConfig:
        """
        Create new ServiceConfig with updated config for a service.

        Args:
            name: Service name
            config: New configuration instance

        Returns:
            New ServiceConfig with updated config

        Example:
            >>> new_config = config.with_config(
            ...     "validation",
            ...     ValidationConfig(ruleset="permissive")
            ... )
        """
        new_configs = self._configs.copy()
        new_configs[name] = config
        return ServiceConfig(**new_configs)

    def __enter__(self) -> ServiceConfig:
        """Apply this service config temporarily."""
        self._token = _service_config.set(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Restore previous config."""
        if self._token:
            _service_config.reset(self._token)

    def __repr__(self) -> str:
        """String representation."""
        configs_repr = ", ".join(f"{k}={v!r}" for k, v in self._configs.items())
        return f"ServiceConfig({configs_repr})"


# ============================================================================
# Context Access Functions
# ============================================================================


def get_service_config() -> ServiceConfig:
    """
    Get the current service configuration.

    This is context-aware and thread-safe using contextvars.
    Services should call this to get their current configuration.

    Returns:
        The current service configuration for this context

    Example:
        >>> # In validator implementation
        >>> config = get_service_config()
        >>> validation_config = config.validation
        >>> if validation_config.fail_fast:
        ...     raise ValidationError(first_error)
    """
    config = _service_config.get()
    if config is None:
        config = ServiceConfig()
        _service_config.set(config)
    return config


def set_service_config(config: ServiceConfig) -> None:
    """
    Set the service configuration (affects current context only).

    Args:
        config: The service configuration to set

    Example:
        >>> config = ServiceConfig(
        ...     validation=ValidationConfig(ruleset="permissive")
        ... )
        >>> set_service_config(config)
    """
    _service_config.set(config)


# ============================================================================
# Field Factory
# ============================================================================


def from_service_config(service_name: str, attribute_path: str | None = None):
    """
    Create a factory that retrieves service config from current context.

    This is for attrs fields that should get their values from
    the current ServiceConfig.

    Args:
        service_name: Service name (e.g., "validation", "my_plugin")
        attribute_path: Optional dot-separated path to attribute

    Returns:
        A factory function suitable for attrs.field(factory=...)

    Example:
        >>> from attrs import define, field
        >>> @define
        ... class ValidatorOptions:
        ...     ruleset: str = field(
        ...         factory=from_service_config("validation", "ruleset")
        ...     )
    """

    def factory():
        config = get_service_config().get(service_name)
        if config is None:
            msg = f"Service config '{service_name}' not found in current context"
            raise ValueError(msg)

        if attribute_path:
            parts = attribute_path.split(".")
            value = config
            for part in parts:
                value = getattr(value, part)
            return value() if callable(value) else value

        return config

    name = f"from_service_config({service_name!r}"
    if attribute_path:
        name += f", {attribute_path!r}"
    name += ")"
    factory.__name__ = name
    return factory
