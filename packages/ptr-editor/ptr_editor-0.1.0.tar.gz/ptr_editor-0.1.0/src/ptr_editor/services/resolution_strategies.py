"""Custom resolution strategies for ptr_editor.

These strategies extend the base resolution framework with domain-specific
logic for resolving PTR-related values including templates and AGM config.
"""

from __future__ import annotations

from loguru import logger as log

from attrs_xml.resolution.strategies import (
    ResolutionContext,
    ResolutionResult,
    ResolutionStrategy,
)


class TemplateResolutionStrategy(ResolutionStrategy):
    """Resolve template references (strings starting with '#').

    Template references like "#my_template" are looked up in a template
    registry and resolved to actual objects.
    """

    def __init__(self, priority: int = 30, template_getter=None):
        """Initialize template resolution strategy.

        Args:
            priority: Strategy priority
            template_getter: Optional callable that returns the template registry.
                           If None, uses the default ptr template register.
        """
        super().__init__(priority=priority)
        self._template_getter = template_getter

    @property
    def name(self) -> str:
        return "template"

    def _get_registry(self):
        """Get the template registry."""
        if self._template_getter:
            return self._template_getter()

        # Default: use ptr template register
        from ptr_editor.services import get_template_register

        return get_template_register()

    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if value is a template reference string."""
        if not isinstance(context.value, str):
            return False

        if not context.value.startswith("#"):
            return False

        # Always handle template references (even str-only for validation)
        log.debug(f"Template reference detected: {context.value}")
        return True

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Resolve template reference to actual object."""
        if not self.can_resolve(context):
            return ResolutionResult.skipped()

        template_name = context.value[1:]  # Remove '#' prefix
        log.debug(f"Resolving template: '{template_name}'")

        try:
            registry = self._get_registry()

            # Validate template exists
            if template_name not in registry:
                available = registry.list_templates()
                templates_list = ", ".join(available) if available else "none"
                error_msg = (
                    f"Template '{template_name}' not found in registry. "
                    f"Available templates: {templates_list}"
                )
                log.error(f"Template not found: {error_msg}")
                return ResolutionResult.failed(
                    error=ValueError(error_msg),
                    strategy_name=self.name,
                )

            # If target type is str-only, validate but don't resolve
            if len(context.target_types) == 1 and context.target_types[0] is str:
                # Validation passed, return the reference string as-is
                log.debug(
                    f"Template '{template_name}' validated (str-only target), "
                    "returning reference as-is",
                )
                return ResolutionResult.succeeded(
                    context.value,
                    strategy_name=self.name,
                )

            # Build type filter for multi-type scenarios
            if len(context.target_types) == 1:
                child_type = context.target_types[0]
            else:
                # Build union using | operator
                child_type = context.target_types[0]
                for t in context.target_types[1:]:
                    child_type = child_type | t  # type: ignore[assignment]

            # Get template with type filtering
            result = registry.get(template_name, child_type)

            if result is None:
                type_names = [t.__name__ for t in context.target_types]
                error_msg = (
                    f"Template '{template_name}' does not contain a child of "
                    f"type {' | '.join(type_names)}"
                )
                log.warning(f"Template type mismatch: {error_msg}")
                return ResolutionResult.failed(
                    error=ValueError(error_msg),
                    strategy_name=self.name,
                )

            log.debug(
                f"Template '{template_name}' resolved successfully to "
                f"{type(result).__name__}",
            )
            return ResolutionResult.succeeded(result, strategy_name=self.name)

        except Exception as e:
            log.debug(f"Template resolution error for '{template_name}': {e}")
            return ResolutionResult.failed(error=e, strategy_name=self.name)


class AGMCaseNormalizationStrategy(ResolutionStrategy):
    """Normalize AGM object/frame names to canonical casing from AGM config.

    This strategy performs a case-insensitive lookup in the AGM configuration
    and returns the name with the canonical casing found in the config.
    This ensures consistency regardless of user input casing.

    The strategy checks (in order):
    1. Objects (e.g., "Jupiter", "Sun")
    2. Frames (e.g., "J2000", "IAU_JUPITER")
    3. Directions/vectors (e.g., "SUN_DIRECTION")
    4. Surfaces (e.g., "JUPITER_SURFACE")

    Example:
        >>> # User inputs "jupiter" but config has "Jupiter"
        >>> strategy = AGMCaseNormalizationStrategy()
        >>> context = ResolutionContext(
        ...     value="jupiter",
        ...     target_types=(
        ...         str,
        ...     ),
        ... )
        >>> result = strategy.resolve(
        ...     context
        ... )
        >>> result.value
        'Jupiter'
    """

    def __init__(self, priority: int = 35, agm_config_getter=None):
        """Initialize AGM case normalization strategy.

        Args:
            priority: Strategy priority (default: 35, between passthrough
                     and template resolution)
            agm_config_getter: Optional callable that returns the AGM configuration.
                              If None, uses the default from context.
        """
        super().__init__(priority=priority)
        self._agm_config_getter = agm_config_getter

    @property
    def name(self) -> str:
        return "agm_case_normalization"

    def _get_agm_config(self):
        """Get the AGM configuration."""
        if self._agm_config_getter:
            return self._agm_config_getter()

        # Default: get from global context
        from ptr_editor.context import get_services

        return get_services()["agm_config"]

    def can_resolve(self, context: ResolutionContext) -> bool:
        """Check if value is a string that might need AGM case normalization.

        We check if:
        1. Value is a string
        2. Target type includes str
        3. Value is not a template reference (starts with '#')
        """
        if not isinstance(context.value, str):
            return False

        # Don't handle template references
        if context.value.startswith("#"):
            return False

        # Only handle if target type is or includes str
        if str not in context.target_types:
            log.debug(
                "Not trying to normalize the string as it is not in the target types",
            )
            return False

        return True

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Normalize the AGM name to canonical casing."""
        if not self.can_resolve(context):
            return ResolutionResult.skipped()

        try:
            agm_config = self._get_agm_config()
            input_name = context.value

            # Try to find in objects
            obj = agm_config.cfg.object_by_name(input_name)
            if obj is not None:
                canonical_name = obj.parser_name
                log.debug(
                    f"AGM case normalization: '{input_name}' -> '{canonical_name}' (object)",
                )
                return ResolutionResult.succeeded(
                    canonical_name,
                    strategy_name=self.name,
                )

            # Try to find in frames
            frame = agm_config.cfg.frame_by_name(input_name)
            if frame is not None:
                canonical_name = frame.parser_name
                log.debug(
                    f"AGM case normalization: '{input_name}' -> '{canonical_name}' (frame)",
                )
                return ResolutionResult.succeeded(
                    canonical_name,
                    strategy_name=self.name,
                )

            # Try to find in directions/vectors
            vector = agm_config.definitions.vector_by_name(input_name)
            if vector is not None:
                canonical_name = vector.parser_name
                log.debug(
                    f"AGM case normalization: '{input_name}' -> '{canonical_name}' (vector)",
                )
                return ResolutionResult.succeeded(
                    canonical_name,
                    strategy_name=self.name,
                )

            # Try to find in surfaces
            surface = agm_config.definitions.surface_by_name(input_name)
            if surface is not None:
                canonical_name = surface.parser_name
                log.debug(
                    f"AGM case normalization: '{input_name}' -> '{canonical_name}' (surface)",
                )
                return ResolutionResult.succeeded(
                    canonical_name,
                    strategy_name=self.name,
                )

            # Not found in AGM config - pass through unchanged
            # (might be valid for other reasons, or validation will catch it later)
            log.debug(
                f"AGM case normalization: '{input_name}' not found in AGM config, passing through",
            )
            return ResolutionResult.skipped()

        except Exception as e:
            # If AGM config is not available or there's an error,
            # just skip this strategy
            log.debug(f"AGM case normalization failed: {e}")
            return ResolutionResult.skipped()
