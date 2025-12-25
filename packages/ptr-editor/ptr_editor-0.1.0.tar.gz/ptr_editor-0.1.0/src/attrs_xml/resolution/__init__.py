"""Value resolution system for converting strings and other values to target types.

This module provides a pluggable system for registering and using different
resolution strategies for automatic type conversion.

Core strategies included:
- PassthroughResolutionStrategy: Values already of correct type
- CallableResolutionStrategy: Factory functions/generators
- ImplicitConversionStrategy: Safe type conversions (int to float, etc.)
- MethodResolutionStrategy: Classes with from_any() or from_string() methods
"""

from .registry import (
    ResolutionRegistry,
    set_registry,
    get_default_registry,
    reset_default_registry,
    set_default_registry_factory,
)
from .strategies import (
    CallableResolutionStrategy,
    ClassAttributeMatchResolutionStrategy,
    ImplicitConversionStrategy,
    MethodResolutionStrategy,
    PassthroughResolutionStrategy,
    ResolutionContext,
    ResolutionStrategy,
)

__all__ = [
    # Registry
    "ResolutionRegistry",
    "get_default_registry",
    "reset_default_registry",
    "set_default_registry_factory",
    "set_registry",
    # Strategies
    "ResolutionStrategy",
    "ResolutionContext",
    "MethodResolutionStrategy",
    "CallableResolutionStrategy",
    "PassthroughResolutionStrategy",
    "ImplicitConversionStrategy",
    "ClassAttributeMatchResolutionStrategy",
]
