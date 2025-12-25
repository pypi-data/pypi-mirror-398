"""
Centralized registry for all singleton objects in ptr_editor.

This module registers all singleton objects (validators, template registers,
resolution registries, etc.) with the global service registry. Import this module
early in your application to ensure all singletons are properly registered.

Usage:
    >>> from ptr_editor import (
    ...     registry,
    ... )  # Registers all services
    >>> from ptr_editor.context import (
    ...     get_services,
    ... )
    >>> services = (
    ...     get_services()
    ... )
    >>> validator = services[
    ...     "agm_validator"
    ... ]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from attrs_xml.resolution.registry import ResolutionRegistry
    from ptr_editor import ElementsRegistry
    from ptr_editor.agm_config.agm_config import AGMConfiguration
    from ptr_editor.agm_validator.agm_config_validator import AgmConfigValidator
    from ptr_editor.context import PointingDefaults
    from ptr_editor.core.ptr_element import PtrElement
    from ptr_editor.templates.register import TemplateRegister
    from ptr_editor.validation import RuleRegistry


def get_agm_configuration() -> AGMConfiguration:
    """
    Get the global AGM configuration instance.

    Returns:
        AGMConfiguration: The AGM configuration instance.

    Example:
        >>> from ptr_editor.registry import (
        ...     get_agm_configuration,
        ... )
        >>> config = get_agm_configuration()
        >>> config.is_known_agm_object(
        ...     "Jupiter"
        ... )
        True
    """
    from ptr_editor.context import get_services

    return get_services()["agm_config"]


def get_pointing_defaults() -> PointingDefaults:
    """
    Get the global pointing defaults instance.

    Returns:
        PointingDefaults: The pointing defaults instance.

    Example:
        >>> from ptr_editor.registry import (
        ...     get_pointing_defaults,
        ... )
        >>> pointing = get_pointing_defaults()
        >>> pointing.target
        'Jupiter'
    """
    from ptr_editor.context import get_services

    return get_services()["pointing"]


def get_agm_validator() -> AgmConfigValidator:
    """
    Get the global AGM validator instance.

    Returns:
        AgmConfigValidator: The AGM configuration validator.

    Example:
        >>> from ptr_editor.registry import (
        ...     get_agm_validator,
        ... )
        >>> validator = get_agm_validator()
        >>> validator.validate(
        ...     "direction",
        ...     "Sun",
        ... )
    """
    from ptr_editor.context import get_services

    return get_services()["agm_validator"]


def get_validation_registry() -> RuleRegistry:
    """
    Get the global validation registry instance.

    Returns:
        RuleRegistry: The validation registry with PTR rules registered.

    Example:
        >>> from ptr_editor.registry import get_validation_registry
        >>> from ptr_editor.validation import RulesetConfig
        >>> registry = get_validation_registry()
        >>> ruleset = RulesetConfig("default")
        >>> ruleset.include_rules_with_tags(["ptr"])
        >>> result = registry.validate(my_object, ruleset=ruleset, recursive=True)
        >>> if not result.ok:
        ...     for error in result.errors():
        ...         print(error)
    """
    from ptr_editor.context import get_services

    return get_services()["validation_registry"]


def get_template_register() -> TemplateRegister:
    """
    Get the global template register instance.

    Returns:
        TemplateRegister: The template register.

    Example:
        >>> from ptr_editor.registry import (
        ...     get_template_register,
        ... )
        >>> register = get_template_register()
        >>> template = register.get(
        ...     "observation_block"
        ... )
    """
    from ptr_editor.context import get_services

    return get_services()["template_register"]


def get_resolution_registry() -> ResolutionRegistry:
    """
    Get the global resolution registry instance.

    Returns:
        ResolutionRegistry: The resolution registry.

    Example:
        >>> from ptr_editor.registry import (
        ...     get_resolution_registry,
        ... )
        >>> registry = get_resolution_registry()
        >>> result = registry.resolve(
        ...     value,
        ...     target_type,
        ... )
    """
    from ptr_editor.context import get_services

    return get_services()["resolution_registry"]


def get_elements_registry() -> ElementsRegistry[PtrElement]:
    """
    Get the PTR ElementsRegistry instance.

    Returns:
        ElementsRegistry[PtrElement]: The PTR elements registry.

    Example:
        >>> from ptr_editor.registry import (
        ...     get_ptr_registry,
        ... )
        >>> ptr = get_ptr_registry()
        >>> # Use for registering elements, etc.
    """
    from ptr_editor.context import get_services

    return get_services()["ptr"]
