"""cattrs converter for attrs_xml library to convert towards PTR format."""

from collections.abc import Callable
from functools import wraps, lru_cache
from typing import Any, get_origin, get_args

import cattrs
import cattrs._compat
import numpy as np
import pandas as pd
from attrs import Attribute, asdict, fields, has
from cattr import Converter
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override
from loguru import logger as log

from attrs_xml.formatting import format_timedelta_to_hhmmss, parse_delta_time_string, to_camel_case
from attrs_xml.globals import global_config
from attrs_xml.xml.converters import format_timestamp
from attrs_xml.xml.custom_disambiguator import custom_create_default_dis_func


class CustomConverter(cattrs.Converter):
    """Converter for attrs_xml library to convert towards PTR format.

    Subclassing is used as we need to override the disambiguation function as the default one
    do not support discriminating unions using literals if these were renamed.
    This is needed as we rename also literals as they end up in XML as attributes.

    """

    def _get_dis_func(
        self,
        union,
        use_literals=True,
        overrides=None,
    ) -> Callable[[Any], type]:
        """Override to use a modified disambiguation function.
        Just a copy of the original, but with a custom disambiguation function.
        """
        union_types = union.__args__
        if cattrs._compat.NoneType in union_types:
            union_types = tuple(
                e for e in union_types if e is not cattrs._compat.NoneType
            )

        if not all(
            cattrs._compat.has(cattrs._compat.get_origin(e) or e) for e in union_types
        ):
            msg = (
                "Only unions of attrs classes and dataclasses supported "
                "currently. Register a structure hook manually."
            )
            raise cattrs.errors.StructureHandlerNotFoundError(
                msg,
                type_=union,
            )

        return custom_create_default_dis_func(
            self,
            *union_types,
            use_literals=use_literals,
            overrides=overrides if overrides is not None else "from_converter",
        )


@lru_cache(maxsize=2048)
def generate_converter_overrides(cls: type) -> dict:
    """Generate overrides for a given class based on its attrs fields.

    This currently takes care also of omitting fields marked with cattrs_omit=True but
    should probably be in a different place
    
    Note: Results are cached per class for performance.
    """
    overrides = {}
    for a in fields(cls):
        a: Attribute
        name = a.name

        tag = a.metadata.get("xml_tag", None)
        should_omit = a.metadata.get("cattrs_omit", False)

        newname = tag if tag else to_camel_case(name)

        # apply changes related to xml_type
        if xml_type := a.metadata.get("xml_type", None):
            if xml_type == "text":
                newname = "#text"

            elif xml_type == "attr":
                newname = f"@{newname}"

        if newname == name:
            log.opt(lazy=True).trace(f"disabling rename for {name}")
            newname = None  # do not do anything

        if newname:
            log.opt(lazy=True).trace(f"Parameter {name} renamed to {newname}")

        if global_config.global_disable_dict_renames:
            log.warning("rename of parameters is disabled globally")
            return overrides

        over = override(
            rename=newname,
            omit=should_omit,
        )

        if any(asdict(over).values()):
            overrides[name] = over

    return overrides


def make_unstructure_hook_factory(converter: Converter):
    def unstructure_hook_factory(cls):
        over = generate_converter_overrides(cls)
        unst_hook = make_dict_unstructure_fn(
            cls,
            converter,
            **over,
            _cattrs_include_init_false=True,
        )

        @wraps(unst_hook)
        def _wrapper_unstructure_hook(val: Any) -> Any:
            got = unst_hook(val)

            return got

        return _wrapper_unstructure_hook

    return unstructure_hook_factory


def _expects_list_type(field_type: Any) -> bool:
    """Check if a field type expects a list, handling Optional types.

    Args:
        field_type: The type annotation of the field

    Returns:
        True if the type expects a list/tuple/set, False otherwise

    Examples:
        list[str] -> True
        Optional[list[str]] -> True
        str | None -> False
        Optional[str] -> False
    """
    # Check the direct type
    origin = get_origin(field_type)
    if origin in (list, tuple, set):
        return True

    # Check if it's a Union (includes Optional which is Union[X, None])
    if origin is not None:
        # For Union types, check the non-None arguments
        args = get_args(field_type)
        if args:
            for arg in args:
                # Skip NoneType
                if arg is type(None):
                    continue
                # Check if this argument is a list type
                arg_origin = get_origin(arg)
                if arg_origin in (list, tuple, set):
                    return True

    return False


# Cache for field mappings per class to avoid rebuilding on every call
_FIELD_MAPPING_CACHE: dict[type, dict] = {}


def _resolve_tag_aliases(val: dict, cls: type) -> dict:
    """Resolve tag aliases by renaming aliased keys to their primary tag names.
    
    For each field with tag_aliases defined, check if the primary tag exists in val.
    If not, check each alias in order and rename the first found alias to the primary tag.
    
    Args:
        val: Input dictionary with potentially aliased keys
        cls: The attrs class we're structuring into
        
    Returns:
        Dictionary with aliases resolved to primary tag names
    """
    if not isinstance(val, dict) or not has(cls):
        return val
    
    overrides = generate_converter_overrides(cls)
    cls_fields = fields(cls)
    
    resolved_val = dict(val)  # Create a copy to avoid modifying the input
    
    for field in cls_fields:
        field_name = field.name
        tag_aliases = field.metadata.get("tag_aliases", None)
        
        if not tag_aliases:
            continue
        
        # Determine the primary dict key for this field
        primary_key = field_name
        if field_name in overrides:
            override_obj = overrides[field_name]
            renamed_to = override_obj.rename if hasattr(override_obj, 'rename') else None
            if renamed_to:
                primary_key = renamed_to
        
        # If primary key exists, no need to check aliases
        if primary_key in resolved_val:
            continue
        
        # Check each alias in order
        for alias in tag_aliases:
            if alias in resolved_val:
                log.debug(
                    f"Resolving tag alias: renaming '{alias}' to '{primary_key}' "
                    f"for field '{field_name}' in class {cls.__name__}"
                )
                # Rename the alias to the primary key
                resolved_val[primary_key] = resolved_val.pop(alias)
                break  # Stop after finding the first matching alias
    
    return resolved_val


def _get_field_mapping(cls: type) -> dict:
    """Get or build field mapping for a class.
    
    Caches the mapping of dict keys to (field_name, field) tuples.
    """
    if cls not in _FIELD_MAPPING_CACHE:
        overrides = generate_converter_overrides(cls)
        cls_fields = fields(cls)
        
        dict_key_to_field = {}
        for field in cls_fields:
            field_name = field.name
            if field_name in overrides:
                # Access override attributes directly instead of converting to dict
                override_obj = overrides[field_name]
                renamed_to = override_obj.rename if hasattr(override_obj, 'rename') else None
                if renamed_to:
                    dict_key_to_field[renamed_to] = (field_name, field)
                else:
                    dict_key_to_field[field_name] = (field_name, field)
            else:
                dict_key_to_field[field_name] = (field_name, field)
        
        _FIELD_MAPPING_CACHE[cls] = dict_key_to_field
    
    return _FIELD_MAPPING_CACHE[cls]


def _fix_list_fields_in_dict(val: dict, cls: type) -> dict:
    """Fix fields that are lists but shouldn't be based on the attrs class definition.

    Args:
        val: Input dictionary with potentially problematic list values
        cls: The attrs class we're structuring into

    Returns:
        Fixed dictionary with lists converted to single values where appropriate
    """
    if not isinstance(val, dict) or not has(cls):
        return val

    # Use cached field mapping instead of rebuilding every time
    dict_key_to_field = _get_field_mapping(cls)

    # Process each key-value pair
    fixed_val = {}
    for dict_key, dict_value in val.items():
        if dict_key not in dict_key_to_field:
            # Unknown field, keep as-is
            fixed_val[dict_key] = dict_value
            continue

        field_name, field = dict_key_to_field[dict_key]
        field_type = field.type
        expects_list = _expects_list_type(field_type)

        # Fix list values that shouldn't be lists
        if isinstance(dict_value, list) and not expects_list:
            if len(dict_value) == 1:
                log.warning(
                    f"Field '{field_name}' (dict key '{dict_key}') "
                    f"expects {field_type} but got list, "
                    f"converting: {dict_value} -> {dict_value[0]}",
                )
                fixed_val[dict_key] = dict_value[0]
            elif len(dict_value) > 1:
                log.warning(
                    f"Field '{field_name}' (dict key '{dict_key}') "
                    f"expects {field_type} but got list with multiple "
                    f"values, taking first: {dict_value}",
                )
                fixed_val[dict_key] = dict_value[0]
            else:
                # Empty list
                fixed_val[dict_key] = dict_value
        else:
            # No issue, keep as-is
            fixed_val[dict_key] = dict_value

    return fixed_val


def make_structure_hook_factory(converter: Converter):
    def structure_hook_factory(cls):
        over = generate_converter_overrides(cls)
        st_hook = make_dict_structure_fn(
            cls,
            converter,
            **over,  # forbid_extra_keys=False
        )

        @wraps(st_hook)
        def _wrapper_structure_hook(
            val: Any,
            _: Any,
        ) -> Any:
            # TODO what happens here below is little hacky and probably also slow
            # need to find a better way to do this
            # this is done ONLY to be able to recover from specific errors
            # that were present in real PTRs we had to load (ORB17)
            # in principle one should just fix the PTRs, but in practice
            # we want to be able to load them anyway
            # at least make it optional so that normal usage is not affected
            # we should also probably dig better into cattrs exception handling
            # to see if there is a cleaner way to do this and look for some examples.

            # Pre-process: resolve tag aliases first
            val = _resolve_tag_aliases(val, cls)
            
            # Pre-process: fix list values before attempting to structure
            val = _fix_list_fields_in_dict(val, cls)

            got = None  # Initialize to satisfy type checker
            try:
                got = st_hook(val, _)

            except ExceptionGroup as eg:
                # Check if it contains ForbiddenExtraKeysError
                forbidden_errors = [
                    e
                    for e in eg.exceptions
                    if isinstance(e, cattrs.errors.ForbiddenExtraKeysError)
                ]
                if forbidden_errors:
                    exc = forbidden_errors[0]
                    log.error("Forbidden extra keys encountered during structuring")
                    log.error(f"Extra keys: {exc.extra_fields}")
                    log.debug(f"Original value: {val}")
                    log.exception(eg)
                    # remove the extra keys and retry
                    cleaned_val = {
                        k: v for k, v in val.items() if k not in exc.extra_fields
                    }
                    got = st_hook(cleaned_val, _)

                # Check if it contains validation errors
                # (lists instead of single values)
                validation_errors = [
                    e
                    for e in eg.exceptions
                    if isinstance(e, cattrs.errors.ClassValidationError)
                ]
                if validation_errors:
                    # The list-fixing logic has already been applied via
                    # _fix_list_fields_in_dict() before st_hook was called.
                    # If we still get validation errors, log and re-raise.
                    log.error(
                        "Validation error during structuring despite pre-processing",
                    )
                    log.error(f"Class: {cls.__name__}")
                    log.debug(f"Original value: {val}")
                    log.exception(eg)
                    raise

                # If we didn't handle it, re-raise
                if not forbidden_errors and not validation_errors:
                    raise

            except Exception as e:
                # Transform and re-raise
                log.error("ValueError during structuring")
                log.error(f"Class: {cls.__name__}")
                log.debug(f"Original value type: {type(val)}")
                log.exception(e)
                raise

            # except* cattrs.errors.ClassValidationError as eg:
            #     log.error('attribute val error')
            #     log.error(f"eg type: {type(eg)}")

            #     wnotes, without_notes = eg.group_exceptions()
            #     log.error(f"Exceptions with notes: {len(wnotes)}")
            #     for subexc, note in wnotes:
            #         log.error(f"Subexception: {subexc}")
            #         log.error(f"Note: {note}")

            # except* cattrs.errors.BaseValidationError as e:
            #     # Add context and re-raise
            #     print(f"Validation error during structuring: {e}")
            #     log.exception(e)
            #     e.add_note(f"Failed to structure {cls.__name__} over data {val}")
            #     raise

            return got

        return _wrapper_structure_hook

    return structure_hook_factory


def register_xml_rename_hooks(converter: Converter) -> None:
    converter.register_structure_hook_factory(
        has,
        make_structure_hook_factory(converter),
    )
    converter.register_unstructure_hook_factory(
        has,
        make_unstructure_hook_factory(converter),
    )


def register_pandas_times_hooks(converter: Converter) -> None:
    """Register conversion hooks for pandas Timestamp and Timedelta."""

    @converter.register_unstructure_hook
    def pandas_timestamp_hook_unstructure(val: pd.Timestamp) -> str:
        """This hook will be registered for pandas datetimes"""
        return format_timestamp(val)

    @converter.register_structure_hook
    def pandas_timestamp_hook_structure(val: Any, _: Any) -> pd.Timestamp:
        return pd.Timestamp(val)

    @converter.register_unstructure_hook
    def pandas_timedelta_hook_unstructure(val: pd.Timedelta) -> str:
        """This hook will be registered for timedelta"""
        return format_timedelta_to_hhmmss(val)

    @converter.register_structure_hook
    def pandas_timedelta_hook_structure(val: Any, _: Any) -> pd.Timedelta:
        # Try OPL format first (ddd.hh:mm:ss[.SSS])
        if isinstance(val, str):
            try:
                return parse_delta_time_string(val)
            except ValueError:
                # Fall back to pandas default parsing
                pass
        return pd.Timedelta(val)


def register_numpy_hooks(converter: CustomConverter) -> None:
    """Register conversion hooks for numpy types."""

    @converter.register_structure_hook
    def number_int_hook_structure(val: Any, _: Any) -> int:
        return int(val)

    @converter.register_structure_hook
    def number_hook_structure(val: Any, _: Any) -> int | float:
        try:
            return int(val)
        except:
            return float(val)

    def numpy_to_str(arr: np.ndarray) -> str:
        items = arr.tolist()
        items = [str(int(i)) if i.is_integer() else str(i) for i in items]
        return " ".join(items)

    def str_to_numpy(s: str, _) -> np.ndarray:
        return np.fromstring(s, sep=" ")

    converter.register_unstructure_hook(np.ndarray, numpy_to_str)
    converter.register_structure_hook(np.ndarray, str_to_numpy)


def register_default_xml_hooks(
    converter: Converter,
) -> None:
    """
    Register conversion hooks for the given class.

    Args:
        cls: The class to register hooks for.
        converter: The XMLConverter instance to use.
    """

    register_pandas_times_hooks(converter)

    @converter.register_unstructure_hook
    def bool_hook_unstructure(val: bool) -> str:
        """This hook will be registered for `datetime`s."""
        return "true" if val else "false"

    @converter.register_structure_hook
    def bool_hook_structure(val: Any, _: Any) -> bool:
        return val.lower() == "true"

    @converter.register_unstructure_hook
    def number_float_hook_unstructure(val: float) -> str:
        if val.is_integer():
            return str(int(val))
        return str(val)

    @converter.register_structure_hook
    def number_float_hook_structure(val: Any, _: Any) -> float:
        return float(val)

    @converter.register_unstructure_hook
    def number_int_hook_unstructure(val: int) -> str:
        return str(val)

    register_numpy_hooks(converter)


def make_default_xml_converter(rename=True) -> CustomConverter:
    """
    Create a default XML converter with registered hooks.

    Returns:
        An instance of XMLConverter with default hooks registered.
    """
    conv = CustomConverter(forbid_extra_keys=True)
    register_default_xml_hooks(conv)
    if rename:
        register_xml_rename_hooks(conv)

    return conv
