"""Contains services access for ptr_editor package.

Code used during package initialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from attrs_xml.resolution.registry import ResolutionRegistry
from ptr_editor.context import ServiceRegistry
from ptr_editor.templates.register import TemplateRegister

from loguru import logger as log

from .quick_access import (
    get_agm_configuration,
    get_agm_validator,
    get_pointing_defaults,
    get_elements_registry,
    get_resolution_registry,
    get_template_register,
    get_validation_registry,
)

__all__ = [
    "bootstrap_ptr_services",
    "get_agm_configuration",
    "get_agm_validator",
    "get_pointing_defaults",
    "get_elements_registry",
    "get_resolution_registry",
    "get_template_register",
    "get_validation_registry",
    "register_all_ptr_schemas",
    "register_all_services",
]

if TYPE_CHECKING:
    from attrs_xml import ElementsRegistry
    from attrs_xml.resolution.registry import ResolutionRegistry
    from ptr_editor.agm_config.agm_config import AGMConfiguration
    from ptr_editor.agm_validator.agm_config_validator import AgmConfigValidator
    from ptr_editor.context import PointingDefaults
    from ptr_editor.elements.attitude import PtrElement
    from ptr_editor.templates.register import TemplateRegister
    from ptr_editor.validation import ValidationRegistry


def _create_resolution_registry() -> ResolutionRegistry:
    """Factory that creates and initializes the resolution registry."""
    from attrs_xml.core.protocols import ElementGenerator
    from attrs_xml.resolution.registry import ResolutionRegistry
    from attrs_xml.resolution.strategies import (
        CallableResolutionStrategy,
        ClassAttributeMatchResolutionStrategy,
        ImplicitConversionStrategy,
        MethodResolutionStrategy,
        PassthroughResolutionStrategy,
    )
    from ptr_editor.services.resolution_strategies import TemplateResolutionStrategy

    log.debug('Creating resolution registry...')

    registry_obj = ResolutionRegistry()

    # Register default strategies

    passthrough = PassthroughResolutionStrategy()
    passthrough.add_passthrough_type(ElementGenerator)

    registry_obj.register(passthrough)
    registry_obj.register(CallableResolutionStrategy())
    registry_obj.register(ImplicitConversionStrategy(priority=30))
    registry_obj.register(ClassAttributeMatchResolutionStrategy(attribute_name="element_type"))

    # Register AGM case normalization strategy (priority 35)
    # This runs after passthrough/callable but before template resolution
    # registry_obj.register(AGMCaseNormalizationStrategy())

    registry_obj.register(TemplateResolutionStrategy())

    # FromAny strategy using MethodResolutionStrategy
    registry_obj.register(
        MethodResolutionStrategy(
            methods=["from_string"],
            priority=40,
        ),
    )

    log.debug('Creating resolution registry... done.')

    return registry_obj


def _class_tagger(class_name: str):
    return class_name[0].lower() + class_name[1:]


def register_all_services(services: ServiceRegistry):
    """Register all singleton objects with the global service registry."""
    from attrs_xml import ElementsRegistry
    from ptr_editor.context import PointingDefaults, get_services
    from ptr_editor.core.ptr_element import PtrElement

    log.debug('Registering all PTR services...')

    services.register("resolution_registry", _create_resolution_registry)

    # this is a temporary solution to set the global registry for attrs-xml
    # it should be removed later.
    from attrs_xml.resolution.registry import set_registry

    set_registry(services["resolution_registry"])


    def _create_elements_registry():
        return ElementsRegistry[PtrElement](class_tagger=_class_tagger)

    services.register("ptr", _create_elements_registry)

    # Pointing Defaults
    services.register("pointing", PointingDefaults)

    # AGM Configuration
    from ptr_editor.agm_config.agm_config import AGMConfiguration

    services.register("agm_config", AGMConfiguration)

    # AGM Validator
    from ptr_editor.agm_validator.agm_config_validator import AgmConfigValidator

    services.register("agm_validator", AgmConfigValidator)

    # Global Validation Registry (using new validation system)
    def _create_validation_registry():
        """Factory that creates validation registry with PTR validators."""
        from ptr_editor.validation import RuleRegistry, RulesetConfig
        from ptr_editor.validation.ptr_validators import register_ptr_rules

        # Create a registry with all PTR rules
        validation_registry = RuleRegistry()
        register_ptr_rules(validation_registry)

        return validation_registry

    services.register("validation_registry", _create_validation_registry)

    # Template Register
    def _create_template_register() -> TemplateRegister:
        """Factory that creates and initializes the template register."""
        from pathlib import Path

        from ptr_editor.data import get_snippet_file
        from ptr_editor.templates.register import TemplateRegister

        templates_register = TemplateRegister()

        # Load default templates from cached remote file
        snippet_path = Path(get_snippet_file())
        templates_register.load_from_snippet_file(snippet_path, group="snippets")

        # Load AGM predefined blocks
        templates_register.load_from_agm_predefined_blocks()

        return templates_register

    services.register("template_register", _create_template_register)

    log.debug('Registering all PTR services... done.')


def register_all_ptr_schemas(registry: ElementsRegistry[PtrElement]) -> None:
    
    """Register all PTR element schemas with the global PTR registry."""
    log.debug('Registering all PTR schemas...')
    from ptr_editor.elements import Prm
    from ptr_editor.elements.agm_config import AGMConfig, Definition

    # Register root elements
    registry.register_schema(Prm)  # main PTR files
    registry.register_schema(AGMConfig)  # AGM configuration files
    registry.register_schema(Definition)  # AGM definitions files

    from ptr_editor.agm_config.agm_utils import AGMPredefinedBlocks

    registry.register(AGMPredefinedBlocks)  # AGM predefined blocks

    log.debug('Registering all PTR schemas... done.')

def register_merghing_strategies() -> None:
    """Register merging strategies for PTR timelines."""
    from time_segments.merging import register_safe_replace_variant

    # Register ptr-editor specific merging strategies to handle timelines
    register_safe_replace_variant(
        "id_safe",
        "id",
        skip_if_mismatch=False,
    )

    register_safe_replace_variant(
        "designer_safe",
        "designer",
        skip_if_mismatch=False,
    )


def bootstrap_ptr_services() -> None:
    
    """Bootstrap the ptr_editor package.

    This function initializes necessary components and configurations
    required for the proper functioning of the ptr_editor package.
    """
    log.debug('Bootstrapping PTR services...')
    # Importing here to avoid circular dependencies during package initialization
    from ptr_editor.context import get_services

    # Initialize services
    services = get_services()

    # Register all services when this module is imported
    register_all_services(services)

    # # Inject ptr_editor's resolution registry factory into attrs_xml
    # # This allows attrs_xml to use ptr_editor's enhanced registry without
    # # creating a hard dependency
    # from attrs_xml.resolution import set_registry

    # set_registry(get_resolution_registry())

    # Now we register all ptr schemas
    from ptr_editor.context.defaults import from_defaults

    from .quick_access import get_elements_registry

    elements_registry = get_elements_registry()

    register_all_ptr_schemas(elements_registry)

    log.debug('Bootstrapping PTR services... done.')


    # register also ptr-specific merging strategies to handle timelines

    from time_segments.merging import register_safe_replace_variant
    register_safe_replace_variant("block_safe_replace", "designer", skip_if_mismatch=False)


    register_merghing_strategies()
