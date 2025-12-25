"""Registry for managing resolution strategies.

The registry maintains a collection of resolution strategies and applies them
in priority order to resolve values.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from attrs import define, field
from loguru import logger as log

from .strategies import (
    ResolutionContext,
    ResolutionStrategy,
)


@define
class ResolutionRegistry:
    """Registry for managing value resolution strategies.

    The registry maintains a prioritized list of strategies and applies them
    in order until one succeeds or all fail.

    Example:
        >>> registry = ResolutionRegistry()
        >>> registry.register(
        ...     MyCustomStrategy()
        ... )
        >>> context = ResolutionContext(
        ...     value="foo",
        ...     target_types=(
        ...         MyType,
        ...     ),
        ... )
        >>> result = registry.resolve(
        ...     context
        ... )
    """

    _strategies: dict[str, ResolutionStrategy] = field(factory=dict)
    _sorted_strategies: list[ResolutionStrategy] = field(factory=list)
    _dirty: bool = field(default=False)
    enabled: bool = field(default=True)

    def register(self, strategy: ResolutionStrategy) -> None:
        """Register a resolution strategy.

        If a strategy with the same name already exists, it will be replaced.

        Args:
            strategy: The strategy to register
        """
        self._strategies[strategy.name] = strategy
        self._dirty = True
        log.debug(f"Registered resolution strategy: {strategy}")

    def unregister(self, name: str) -> bool:
        """Unregister a strategy by name.

        Args:
            name: Name of the strategy to remove

        Returns:
            True if the strategy was removed, False if not found
        """
        if name in self._strategies:
            del self._strategies[name]
            self._dirty = True
            log.debug(f"Unregistered resolution strategy: {name}")
            return True
        return False

    def get_strategy(self, name: str) -> ResolutionStrategy | None:
        """Get a registered strategy by name.

        Args:
            name: Name of the strategy

        Returns:
            The strategy if found, None otherwise
        """
        return self._strategies.get(name)

    def enable_strategy(self, name: str) -> bool:
        """Enable a strategy by name.

        Args:
            name: Name of the strategy

        Returns:
            True if enabled, False if not found
        """
        strategy = self.get_strategy(name)
        if strategy:
            strategy.enabled = True
            return True
        return False

    def disable_strategy(self, name: str) -> bool:
        """Disable a strategy by name.

        Args:
            name: Name of the strategy

        Returns:
            True if disabled, False if not found
        """
        strategy = self.get_strategy(name)
        if strategy:
            strategy.enabled = False
            return True
        return False

    def list_strategies(
        self, *, enabled_only: bool = False,
    ) -> list[ResolutionStrategy]:
        """List all registered strategies in priority order.

        Args:
            enabled_only: If True, only return enabled strategies

        Returns:
            List of strategies sorted by priority
        """
        self._ensure_sorted()
        if enabled_only:
            return [s for s in self._sorted_strategies if s.enabled]
        return self._sorted_strategies.copy()

    def _ensure_sorted(self) -> None:
        """Ensure strategies are sorted by priority."""
        if self._dirty:
            self._sorted_strategies = sorted(self._strategies.values())
            self._dirty = False

    def resolve(self, context: ResolutionContext) -> Any:
        """Resolve a value using registered strategies.

        Tries each enabled strategy in priority order until one succeeds.

        Args:
            context: The resolution context

        Returns:
            The resolved value

        Raises:
            ValueError: If a strategy raises a validation error
            RuntimeError: If no strategy could resolve the value
        """
        if not self.enabled:
            return context.value

        self._ensure_sorted()

        log.opt(lazy=True).trace(f"Starting resolution for context: {context} ")
        log.opt(lazy=True).trace(f"Using strategies: {self._sorted_strategies}")


        for strategy in self._sorted_strategies:
            if not strategy.enabled:
                log.opt(lazy=True).trace(f"Skipping disabled strategy: {strategy.name}")
                continue

            # Quick check if strategy can handle this
            if not strategy.can_resolve(context):
                log.opt(lazy=True).trace(f"Strategy {strategy.name} cannot resolve the context, skipping.")
                continue

            # Attempt resolution
            log.opt(lazy=True).trace(f"Trying resolution strategy: {strategy.name}")
            result = strategy.resolve(context)

            if result.success:
                log.opt(lazy=True).trace(f"Resolution succeeded with strategy: {strategy.name}")
                return result.value

            if result.error:
                # If it's a validation error, propagate it
                if isinstance(result.error, ValueError):
                    raise result.error
                log.opt(lazy=True).trace(f"Strategy {strategy.name} failed: {result.error}")

        # No strategy succeeded - raise ValueError for backwards compatibility
        type_names = [t.__name__ for t in context.target_types]
        error_msg = (
            f"Could not resolve value {context.value!r} to type "
            f"{' | '.join(type_names)}"
        )
        if context.field_name:
            error_msg += f" for field '{context.field_name}'"
        if context.class_name:
            error_msg += f" in class '{context.class_name}'"

        log.opt(lazy=True).trace(f"Resolution failed: {error_msg}")
        log.opt(lazy=True).trace(f"Resolution context: {context}")

        raise ValueError(error_msg)

    def resolve_value(
        self,
        value: Any,
        target_type: type | tuple[type, ...],
        *,
        is_optional: bool = False,
        has_unset: bool = False,
        field_name: str | None = None,
        class_name: str | None = None,
    ) -> Any:
        """Resolve a value to a target type using registered strategies.

        This is a convenience method that creates a ResolutionContext and
        attempts resolution with all registered strategies in priority order.

        Args:
            value: The value to resolve/convert
            target_type: The target type(s) to convert to (single type or tuple)
            is_optional: Whether None is an acceptable value
            has_unset: Whether UNSET sentinel is acceptable
            field_name: Optional field name for better error messages
            class_name: Optional class name for better error messages

        Returns:
            The resolved value

        Raises:
            ValueError: If no strategy could resolve the value or validation fails

        Example:
            >>> registry = ResolutionRegistry()
            >>> # Resolve a string to an int
            >>> result = registry.resolve_value("42", int)
            >>> assert result == 42
            >>>
            >>> # Resolve with union types
            >>> result = registry.resolve_value("123", (int, str))
            >>> assert result == 123
        """
        # Normalize target_type to tuple
        if not isinstance(target_type, tuple):
            target_types = (target_type,)
        else:
            target_types = target_type

        # Create resolution context
        context = ResolutionContext(
            value=value,
            target_types=target_types,
            is_optional=is_optional,
            has_unset=has_unset,
            field_name=field_name,
            class_name=class_name,
        )

        return self.resolve(context)

    def __repr__(self) -> str:
        enabled = sum(1 for s in self._strategies.values() if s.enabled)
        total = len(self._strategies)
        return f"ResolutionRegistry({enabled}/{total} strategies enabled)"

    @contextmanager
    def disabled(self):
        """Context manager to temporarily disable the resolution registry.

        When disabled, the registry will return values unchanged without
        attempting any resolution strategies.

        Example:
            >>> registry = ResolutionRegistry()
            >>> with registry.disabled():
            ...     # Resolution is bypassed, values returned as-is
            ...     result = registry.resolve_value("42", int)
            >>> # Resolution is re-enabled here
        """
        previous_state = self.enabled
        self.enabled = False
        try:
            yield self
        finally:
            self.enabled = previous_state


# ============================================================================
# Global Default Registry
# ============================================================================

# Module-level default registry (used when no context is available)
_default_registry: ResolutionRegistry | None = None
_registry_factory: callable[[], ResolutionRegistry] | None = None


def set_default_registry_factory(factory: callable[[], ResolutionRegistry]) -> None:
    """Set a custom factory function for creating the default registry.
    
    This allows external packages (like ptr_editor) to inject their own
    registry with additional strategies without creating a hard dependency.
    
    Args:
        factory: Function that returns a configured ResolutionRegistry
        
    Example:
        >>> def my_custom_registry():
        ...     registry = ResolutionRegistry()
        ...     registry.register(MyCustomStrategy())
        ...     return registry
        >>> set_default_registry_factory(my_custom_registry)
    """
    global _registry_factory
    _registry_factory = factory


def set_registry(registry: ResolutionRegistry) -> None:
    """Set the default global resolution registry directly.
    
    This overrides any custom factory that was set.
    
    Args:
        registry: The ResolutionRegistry to set as default
        
    Example:
        >>> from attrs_xml.resolution.registry import set_registry, ResolutionRegistry
        >>> my_registry = ResolutionRegistry()
        >>> set_registry(my_registry)
    """
    global _default_registry, _registry_factory
    _default_registry = registry
    _registry_factory = None


def _create_basic_registry() -> ResolutionRegistry:
    """Create a basic resolution registry with core strategies.
    
    This creates the default registry with attrs_xml core strategies:
    - PassthroughResolutionStrategy (priority 10)
    - CallableResolutionStrategy (priority 20)  
    - ImplicitConversionStrategy (priority 30)
    - MethodResolutionStrategy for from_any (priority 40)
    - MethodResolutionStrategy for from_string (priority 50)
    
    You can add custom strategies to this registry using registry.register().
    """
    from .strategies import (
        CallableResolutionStrategy,
        ImplicitConversionStrategy,
        MethodResolutionStrategy,
        PassthroughResolutionStrategy,
    )

    registry = ResolutionRegistry()

    # Register core strategies
    registry.register(PassthroughResolutionStrategy(priority=10))
    registry.register(CallableResolutionStrategy(priority=20))
    registry.register(ImplicitConversionStrategy(priority=30))
    registry.register(MethodResolutionStrategy(
        methods=["from_any"],
        priority=40,
        strategy_name="from_any",
    ))
    registry.register(MethodResolutionStrategy(
        methods=["from_string"],
        priority=50,
        strategy_name="from_string",
    ))

    return registry


def get_default_registry() -> ResolutionRegistry:
    """Get the default global resolution registry.

    If a custom registry factory has been set via set_default_registry_factory(),
    that will be used. Otherwise, returns a basic registry with core strategies:
    - Passthrough (priority 10)
    - Callable (priority 20)
    - ImplicitConversion (priority 30) - handles int to float, etc.
    - FromAny (priority 40) - uses MethodResolutionStrategy with from_any
    - FromString (priority 50) - uses MethodResolutionStrategy with from_string

    Returns:
        ResolutionRegistry: The resolution registry.

    Example:
        >>> from attrs_xml.resolution.registry import get_default_registry
        >>> registry = get_default_registry()
        >>> result = registry.resolve("some_value", TargetType)
    """
    global _default_registry

    # Use custom factory if one was set (e.g., by ptr_editor)
    if _registry_factory is not None:
        return _registry_factory()

    # Create basic standalone registry if not already created
    if _default_registry is None:
        _default_registry = _create_basic_registry()

    return _default_registry


def reset_default_registry() -> None:
    """Reset the default registry (mainly for testing).

    Note: This does not reset any custom factory that was set.
    
    Example:
        >>> from attrs_xml.resolution.registry import reset_default_registry
        >>> reset_default_registry()  # Clear and recreate registry
    """
    global _default_registry

    # Reset module-level registry
    _default_registry = None
