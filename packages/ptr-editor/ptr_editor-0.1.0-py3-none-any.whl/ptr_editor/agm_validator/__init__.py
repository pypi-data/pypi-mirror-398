"""
AGM validation package for PTR elements.

This package provides AGM-specific validation for PTR elements.
For general validation, use ptr_editor.validation instead.
"""

from .agm_config_validator import (
    AgmConfigValidator,
    AGMDefinitionType,
    AGMDefinitionTypes,
    HasRef,
    UnknownAGMDefinitionError,
    agm_validation_disabled,
    get_agm_validator,
    validator_for,
)

__all__ = [
    "AGMDefinitionType",
    "AGMDefinitionTypes",
    "AgmConfigValidator",
    "HasRef",
    "UnknownAGMDefinitionError",
    "agm_validation_disabled",
    "get_agm_validator",
    "validator_for",
]
