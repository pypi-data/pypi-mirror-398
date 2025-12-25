"""Resolution strategies for converting values to target types.

Each strategy implements a specific way to resolve/convert values,
such as template references, from_any methods, from_string methods, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from attrs import define, field
from typing import Any, Literal, get_args, get_origin

from loguru import logger as log


@define(frozen=True)
class ResolutionContext:
    """Context information for value resolution.

    This contains all the information a resolution strategy needs to
    attempt converting a value to a target type.
    """

    value: Any
    """The value to be resolved/converted."""

    target_types: tuple[type, ...]
    """The target type(s) the value should be converted to."""

    is_optional: bool = False
    """Whether None is an acceptable value."""

    has_unset: bool = False
    """Whether UNSET sentinel is acceptable."""

    field_name: str | None = None
    """Optional field name for better error messages."""

    class_name: str | None = None
    """Optional class name for better error messages."""

    def with_value(self, new_value: Any) -> ResolutionContext:
        """Create a new context with a different value."""
        return ResolutionContext(
            value=new_value,
            target_types=self.target_types,
            is_optional=self.is_optional,
            has_unset=self.has_unset,
            field_name=self.field_name,
            class_name=self.class_name,
        )


@define
class ResolutionResult:
    """Result of a resolution attempt.

    Indicates whether resolution succeeded and provides the resolved value
    or error information.
    """

    success: bool
    value: Any = None
    error: Exception | None = None
    strategy_name: str | None = None

    @classmethod
    def succeeded(
        cls,
        value: Any,
        strategy_name: str | None = None,
    ) -> ResolutionResult:
        """Create a successful resolution result."""
        return cls(True, value, strategy_name=strategy_name)

    @classmethod
    def failed(
        cls,
        error: Exception | None = None,
        strategy_name: str | None = None,
    ) -> ResolutionResult:
        """Create a failed resolution result."""
        return cls(False, error=error, strategy_name=strategy_name)

    @classmethod
    def skipped(cls) -> ResolutionResult:
        """Create a result indicating the strategy was not applicable."""
        return cls(False)

    def __repr__(self) -> str:
        if self.success:
            return f"ResolutionResult(success=True, value={self.value!r}, strategy={self.strategy_name})"
        if self.error:
            return f"ResolutionResult(success=False, error={self.error!r})"
        return "ResolutionResult(skipped)"


@define
class ResolutionStrategy(ABC):
    """Base class for value resolution strategies.

    A resolution strategy implements a specific way to convert/resolve values,
    such as looking up templates, calling from_any methods, etc.

    Strategies are tried in priority order until one succeeds.
    """

    priority: int = field(default=100)
    """Lower numbers are tried first (default: 100)"""
    
    enabled: bool = field(default=True)
    """Whether this strategy is enabled"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this strategy."""

    @abstractmethod
    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if this strategy can handle the given context.

        This is a fast check to see if the strategy should even be attempted.
        Should not do expensive operations or side effects.

        Args:
            context: The resolution context

        Returns:
            True if this strategy might be able to resolve the value
        """

    @abstractmethod
    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Attempt to resolve the value.

        Args:
            context: The resolution context

        Returns:
            ResolutionResult indicating success or failure
        """

    def __lt__(self, other: ResolutionStrategy) -> bool:
        """Compare strategies by priority for sorting."""
        return self.priority < other.priority

    def __repr__(self) -> str:
        enabled_str = "enabled" if self.enabled else "disabled"
        return f"{self.__class__.__name__}(priority={self.priority}, {enabled_str})"


# ============================================================================
# Built-in Resolution Strategies
# ============================================================================


@define
class PassthroughResolutionStrategy(ResolutionStrategy):
    """Pass through values that are already the correct type.

    This should typically have the lowest priority (tried first) as it's
    the fastest check.
    """

    priority: int = field(default=10)
    passthrough_types: tuple[type, ...] = field(factory=lambda: (list, tuple, dict, set))
    """Additional types to pass through without conversion."""
    
    check_unset: bool = field(default=True)
    """Whether to check for and pass through UNSET sentinel."""
    
    _unset_sentinel: Any = field(init=False, repr=False)

    def __attrs_post_init__(self):
        """Initialize UNSET sentinel after attrs initialization."""
        if self.check_unset:
            from attrs_xml.core.sentinels import UNSET
            object.__setattr__(self, '_unset_sentinel', UNSET)
        else:
            object.__setattr__(self, '_unset_sentinel', None)

    def add_passthrough_type(self, new_type: type) -> None:
        """Add a new type to the passthrough types.
        
        Args:
            new_type: The type to add to passthrough types
        """
        if new_type not in self.passthrough_types:
            object.__setattr__(self, 'passthrough_types', self.passthrough_types + (new_type,))

    @property
    def name(self) -> str:
        return "passthrough"

    def add_type(self, new_type: type) -> None:
        """Add a new type to the passthrough types."""
        if new_type not in self.passthrough_types:
            object.__setattr__(self, 'passthrough_types', self.passthrough_types + (new_type,))

    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if value is already one of the target types."""
        # Always pass through None - let attrs handle default/factory
        if context.value is None:
            return True

        # Check UNSET sentinel if configured
        if self.check_unset and context.value is self._unset_sentinel:
            return True

        # Don't pass through template references - let TemplateStrategy handle them
        if isinstance(context.value, str) and context.value.startswith("#"):
            return False

        # Check Literal types
        for target_type in context.target_types:
            if get_origin(target_type) is Literal:
                # For Literal types, check if value is one of the allowed values
                allowed_values = get_args(target_type)
                if context.value in allowed_values:
                    return True

        # Pass through collections (configured types) - handled by cattrs
        # not by our converter. If the type annotation is a union of element
        # types but the value is a list, just pass it through.
        if isinstance(context.value, self.passthrough_types):
            return True

        # Check if already correct type (including inheritance)
        try:
            # Check exact type matches
            value_type = type(context.value)
            if value_type in context.target_types:
                return True

            # Check isinstance for inheritance
            return any(isinstance(context.value, t) for t in context.target_types)
        except TypeError:
            # Generic types may fail isinstance check
            return False

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Return the value unchanged."""
        if self.can_resolve(context):
            return ResolutionResult.succeeded(context.value, strategy_name=self.name)
        return ResolutionResult.skipped()


@define
class CallableResolutionStrategy(ResolutionStrategy):
    """Resolve callable values by invoking them or passing them through.

    This strategy handles callable values in two modes:
    - Immediate (lazy=False): Invokes the callable immediately and returns the result
    - Lazy (lazy=True): Passes through the callable unchanged for later invocation

    This allows fields to be initialized with lambdas or factory functions
    that can be called either at resolution time or when first accessed.
    """

    priority: int = field(default=20)
    lazy: bool = field(default=False)
    """If True, pass through callables unchanged. If False, invoke them immediately."""

    @property
    def name(self) -> str:
        mode = "lazy" if self.lazy else "immediate"
        return f"callable({mode})"

    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if value is callable."""
        return callable(context.value)

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Handle callable based on lazy configuration.

        If lazy=False: Invoke the callable and return its result.
        If lazy=True: Pass through the callable unchanged.
        """
        if not self.can_resolve(context):
            return ResolutionResult.skipped()

        # Lazy mode: just pass through the callable unchanged
        if self.lazy:
            return ResolutionResult.succeeded(context.value, strategy_name=self.name)

        # Immediate mode: invoke the callable
        try:
            result = context.value()
            # Note: We don't recursively resolve here; the caller should
            # create a new context with the result if needed
            return ResolutionResult.succeeded(result, strategy_name=self.name)
        except Exception as e:
            log.debug(f"Callable resolution failed: {e}")
            return ResolutionResult.failed(error=e, strategy_name=self.name)


# ============================================================================
# Method Resolution Strategy
# ============================================================================


@define
class MethodResolutionStrategy(ResolutionStrategy):
    """Resolve values by calling methods on target types.

    This is a flexible strategy that tries calling specified methods
    on target types to convert values. Common examples include:
    - from_any: accepts multiple input types
    - from_string: converts strings to the target type
    - parse: parses input values
    - create: factory method

    The strategy tries each method in the order specified until one succeeds.
    """

    priority: int = field(default=40)
    methods: list[str] = field(factory=lambda: ["from_any", "from_string"])
    """List of method names to try."""
    
    strategy_name: str = field(default="method")
    """Strategy name."""
    
    value_type_filter: type | tuple[type, ...] | None = field(default=None)
    """If provided, only resolve values of this type(s)."""

    @property
    def name(self) -> str:
        return self.strategy_name

    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if any target type has one of the specified methods."""
        # Check value type filter if specified
        if self.value_type_filter is not None:
            if not isinstance(context.value, self.value_type_filter):
                return False

        # Check if any target type has any of the methods
        for target_type in context.target_types:
            for method_name in self.methods:
                if hasattr(target_type, method_name):
                    return True
        return False

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Try calling methods on each target type."""
        if not self.can_resolve(context):
            return ResolutionResult.skipped()

        # Try each method in order
        for method_name in self.methods:
            # Try each target type
            for target_type in context.target_types:
                if not hasattr(target_type, method_name):
                    continue

                try:
                    method = getattr(target_type, method_name)
                    result = method(context.value)

                    # Some methods might return None to indicate failure
                    if result is not None:
                        return ResolutionResult.succeeded(
                            result, strategy_name=self.name,
                        )
                except ValueError:
                    # Validation errors should propagate
                    raise
                except Exception as e:
                    log.debug(
                        f"{method_name} failed for {target_type.__name__}: {e}",
                    )
                    # Continue trying other methods/types
                    continue

        return ResolutionResult.skipped()


@define
class ImplicitConversionStrategy(ResolutionStrategy):
    """Resolve values using implicit type conversions.

    This strategy handles obvious, safe type conversions that can be done
    automatically, such as:
    - int to float: 42 -> 42.0
    - int to bool: 0 -> False, 1+ -> True
    - float to int: 42.0 -> 42 (lossless conversion)
    - str to bool: "true"/"false" -> True/False

    This strategy is useful for resolving values when the input type is
    different but can be safely converted to the target type.
    """

    priority: int = field(default=30)

    @property
    def name(self) -> str:
        return "implicit_conversion"

    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if value can be implicitly converted to any target type."""
        value = context.value
        value_type = type(value)

        # Skip None and special cases
        if value is None or isinstance(value, (list, dict, tuple, set)):
            return False

        for target_type in context.target_types:
            if self._can_convert(value, value_type, target_type):
                return True

        return False

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Convert value to first compatible target type."""
        if not self.can_resolve(context):
            return ResolutionResult.skipped()

        value = context.value

        for target_type in context.target_types:
            if self._can_convert(value, type(value), target_type):
                try:
                    converted = self._perform_conversion(value, target_type)
                    return ResolutionResult.succeeded(
                        converted, strategy_name=self.name
                    )
                except Exception as e:
                    log.debug(
                        f"Implicit conversion of {value!r} to {target_type.__name__} failed: {e}"
                    )
                    continue

        return ResolutionResult.skipped()

    def _can_convert(self, value: Any, from_type: type, to_type: type) -> bool:
        """Check if value can be implicitly converted from one type to another."""
        # int to float: always safe
        if from_type is int and to_type is float:
            return True

        # float to int: safe only if lossless (no fractional part)
        if from_type is float and to_type is int:
            return isinstance(value, float) and value == int(value)

        # int/float to bool: always safe
        if from_type in (int, float) and to_type is bool:
            return True

        # bool to int/float: always safe
        if from_type is bool and to_type in (int, float):
            return True

        # str to bool: only for recognized values
        if from_type is str and to_type is bool:
            return str(value).lower() in ("true", "false", "1", "0", "yes", "no")

        return False

    def _perform_conversion(self, value: Any, target_type: type) -> Any:
        """Perform the actual conversion."""
        if target_type is float:
            return float(value)

        if target_type is int:
            return int(value)

        if target_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)

        return value


@define
class ClassAttributeMatchResolutionStrategy(ResolutionStrategy):
    """Resolve string values by matching against a class attribute.

    This strategy is useful when you have a union of attrs classes and want
    to convert a string to the appropriate class based on a class attribute
    (e.g., a "type" field).

    Example:
        @attrs.define
        class TypeA:
            type: str = "type_a"  # class attribute

        @attrs.define
        class TypeB:
            type: str = "type_b"  # class attribute

        # With this strategy, the string "TYPE_A" can be converted to TypeA()
        strategy = ClassAttributeMatchResolutionStrategy(attribute_name="type")
    """

    priority: int = field(default=35)
    attribute_name: str = field(default="element_type")
    """Name of the class attribute to check for matches."""
    
    case_sensitive: bool = field(default=False)
    """Whether to perform case-sensitive matching."""

    @property
    def name(self) -> str:
        return f"class_attribute_match({self.attribute_name})"

    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if value is a string and any target type has the attribute."""
        # Only works for string input
        if not isinstance(context.value, str):
            return False

        # Check if any target type has the specified attribute
        for target_type in context.target_types:
            if self._is_attrs_class(target_type) and hasattr(
                target_type, self.attribute_name
            ):
                return True
        return False

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Match string value against class attribute and instantiate matching class."""
        if not self.can_resolve(context):
            return ResolutionResult.skipped()

        value_str = context.value
        if not self.case_sensitive:
            value_str = value_str.lower()

        # Try each target type
        for target_type in context.target_types:
            if not self._is_attrs_class(target_type):
                continue

            if not hasattr(target_type, self.attribute_name):
                continue

            try:
                # Get the attribute value from the class
                attr_value = getattr(target_type, self.attribute_name)

                # Handle case where attribute is a property or descriptor
                # that requires an instance - skip those
                if not isinstance(attr_value, str):
                    continue

                # Compare values
                compare_value = (
                    attr_value if self.case_sensitive else attr_value.lower()
                )

                if value_str == compare_value:
                    # Found a match! Instantiate the class
                    log.debug(
                        f"Matched '{context.value}' to {target_type.__name__} "
                        f"via attribute '{self.attribute_name}'"
                    )
                    try:
                        # Try to instantiate with no arguments
                        instance = target_type()
                        return ResolutionResult.succeeded(
                            instance, strategy_name=self.name
                        )
                    except TypeError as e:
                        # Class requires arguments, try to pass the original value
                        # as a keyword argument matching the attribute name
                        log.error(
                            f"matched class {target_type.__name__} requires arguments, "
                        )
                        log.exception(f"Could not instantiate: {e}")
                        # try:
                        #     instance = target_type(**{self._attribute_name: attr_value})
                        #     return ResolutionResult.succeeded(
                        #         instance, strategy_name=self.name
                        #     )
                        # except TypeError as e:
                        #     log.debug(
                        #         f"Could not instantiate {target_type.__name__}: {e}"
                        #     )
                        #     continue

            except Exception as e:
                log.debug(
                    f"Error checking attribute '{self.attribute_name}' "
                    f"on {target_type.__name__}: {e}"
                )
                continue

        return ResolutionResult.skipped()

    @staticmethod
    def _is_attrs_class(cls: type) -> bool:
        """Check if a class is an attrs class."""
        try:
            import attrs

            return attrs.has(cls)
        except ImportError:
            # If attrs is not available, check for __attrs_attrs__
            return hasattr(cls, "__attrs_attrs__")
