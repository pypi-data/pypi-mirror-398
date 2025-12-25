from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import attrs
from cattrs import transform_error
from loguru import logger as log

# from attrs_xml.xml_formatting import style_xml_with_padding
from attrs_xml.core.inspect import ptr_fields
from attrs_xml.xml.utils import is_element_a_list, remove_null_values

if TYPE_CHECKING:
    from attrs_xml.core.base_element import BaseElement
    from attrs_xml.xml.converter import CustomConverter


def _parse_xml_to_dict(xml: str, preprocess: bool = True) -> dict[str, Any]:
    """
    Parse XML string or file path to dictionary.

    Args:
        xml: Either an XML string or path to an XML file
        preprocess: Whether to preprocess XML with lxml parser (recover mode) before
                   parsing with xmltodict. Default is True.

    Returns:
        Dictionary representation of the XML

    Raises:
        Various exceptions from xmltodict.parse or file operations
    """
    from xmltodict import parse

    # Check if it's a file path (but don't use Path for long strings)
    if os.path.isfile(xml):
        with open(xml) as f:
            xml_content = f.read()
    else:
        xml_content = xml

    # Preprocess with lxml if requested
    if preprocess:
        xml_content = _preprocess_xml_with_lxml(xml_content)

    return parse(
        xml_content.encode(),
        force_list=is_element_a_list,
    )


def _preprocess_xml_with_lxml(xml_content: str) -> str:
    """
    Preprocess XML content using lxml parser with recover mode.

    This ensures the XML can be parsed and automatically fixes common issues.

    Args:
        xml_content: The XML content as a string

    Returns:
        The preprocessed XML content as a string

    Raises:
        ValueError: If the XML cannot be parsed even with recovery mode
    """
    from lxml import etree

    try:
        # Create a parser with recover mode enabled
        parser = etree.XMLParser(recover=True, encoding="utf-8")

        # Parse the XML
        tree = etree.fromstring(xml_content.encode("utf-8"), parser=parser)

        # Check for parsing errors
        if parser.error_log:
            log.warning(
                f"XML parsing encountered {len(parser.error_log)} recoverable errors",
            )
            for error in parser.error_log:
                log.debug(
                    f"  Line {error.line}, Column {error.column}: {error.message}",
                )

        # Convert back to string
        preprocessed = etree.tostring(tree, encoding="unicode", pretty_print=False)

        log.debug("XML preprocessing completed successfully")
        return preprocessed

    except etree.XMLSyntaxError as e:
        log.error(f"Failed to preprocess XML: {e}")
        log.error(f"Error on line {e.lineno}, column {e.offset}: {e.msg}")
        msg = f"XML syntax error: {e.msg}"
        raise ValueError(msg) from e
    except Exception as e:
        log.error(f"Unexpected error during XML preprocessing: {e}")
        log.error(f"Error type: {type(e).__name__}")
        msg = f"Failed to preprocess XML: {e}"
        raise ValueError(msg) from e


def _read_xml_to_object(cls, xml: str, converter: CustomConverter) -> BaseElement:
    """
    Read XML and convert it to an object instance.

    Args:
        cls: The class to create an instance of
        xml: Either an XML string or path to an XML file

    Returns:
        Instance of cls created from the XML

    Raises:
        ValueError: If XML parsing or object creation fails
    """
    asdict = _parse_xml_to_dict(xml)
    log.debug(f"as dict {asdict}")

    result = dict_to_object(cls, asdict, converter=converter)
    if result is None:
        msg = "Failed to parse XML document"
        raise ValueError(msg)
    return result


def set_parent_references(obj, parent=None) -> None:
    """
    Recursively traverse the object tree and set _parent attributes.

    Args:
        obj: The object to process (should be a BaseElement)
        parent: The parent object to set (BaseElement or None)
    """
    # Avoid circular import by checking duck-typing instead of isinstance
    if not hasattr(obj, "_parent") or not hasattr(obj, "default_name"):
        return

    # Set the parent for this object
    obj._parent = parent

    # Get all attributes of this object
    if attrs.has(type(obj)):
        for attr in ptr_fields(obj):
            value = getattr(obj, attr.name)
            handle_attribute_value(value, obj)


def handle_attribute_value(value: Any, parent) -> None:
    """
    Handle different types of attribute values for parent setting.

    Args:
        value: The attribute value to process
        parent: The parent object to set
    """
    if hasattr(value, "_parent") and hasattr(value, "default_name"):
        set_parent_references(value, parent)
    elif isinstance(value, (list, tuple)):
        handle_sequence(value, parent)
    elif isinstance(value, dict):
        handle_dict(value, parent)


def handle_sequence(sequence: list | tuple, parent) -> None:
    """
    Handle list/tuple of potential BaseElement children.

    Args:
        sequence: List or tuple to process
        parent: The parent object to set
    """
    for item in sequence:
        if hasattr(item, "_parent") and hasattr(item, "default_name"):
            set_parent_references(item, parent)


def handle_dict(dictionary: dict, parent) -> None:
    """
    Handle dictionary with potential BaseElement values.

    Args:
        dictionary: Dictionary to process
        parent: The parent object to set
    """
    for item in dictionary.values():
        if hasattr(item, "_parent") and hasattr(item, "default_name"):
            set_parent_references(item, parent)


def object_to_dict(
    obj,
    converter: CustomConverter,
    drop_none: bool = True,
    root_key: str = "",
) -> dict[str, Any]:
    """
    Convert an object to dictionary representation.

    Args:
        obj: The object to convert (should have default_name attribute)
        drop_none: Whether to remove None values from the result

    Returns:
        Dictionary representation of the object
    """

    if not root_key:
        root_key = obj.default_name

    got = converter.unstructure({root_key: obj})

    if drop_none:
        got = remove_null_values(got)

    if not got:
        return {root_key: None}

    return got


def dict_to_object(cls, value: dict, converter: CustomConverter) -> BaseElement:
    """
    Convert dictionary to object instance.

    Args:
        cls: The class to create an instance of
        value: Dictionary containing the object data

    Returns:
        Instance of cls created from the dictionary

    Raises:
        Exception: If conversion fails
    """
    from cattrs import transform_error

    try:
        return converter.structure(value[next(iter(value.keys()))], cls)
        # set_parent_references(got)
    except Exception as exc:
        # print(exc.__notes__)
        errors = transform_error(exc)
        log.error(f"Data is {value}")
        for e in errors:
            log.error(e)
        raise


def object_to_xml(
    obj,
    converter: CustomConverter,
    pretty: bool = False,
    root_key: str = "",
) -> str:
    """
    Convert object to XML representation.

    Args:
        obj: The object to convert
        pretty: Whether to format the XML with indentation
        root_key: The root key to use for the XML

    Returns:
        XML string representation of the object
    """
    from xmltodict import unparse

    as_dict = object_to_dict(obj, converter=converter, root_key=root_key)
    # if not as_dict:
    #     return f"<{root_key}/>"

    return unparse(
        as_dict,
        pretty=pretty,
        full_document=False,
        short_empty_elements=True,
        indent=3,
    )


from cattrs.v import format_exception


def _format_exception(exc: BaseException, type: type | None) -> str:
    got = format_exception(exc, type)

    # import rich
    # rich.inspect(exc, all=True)
    # if hasattr(exc, "__notes__"):
    #     for note in exc.__notes__:
    #         got += f"\n  -> Note: {note}"

    return got


def loads(
    xml_text: str,
    elements_registry,
    cls: type | str | None = None,
    preprocess: bool = True,
    raise_on_error: bool = True,
    disable_defaults: bool = True,
) -> BaseElement | None:
    """
    Parse an XML text and return the corresponding element.

    Args:
        xml_text: The XML text to parse
        elements_registry: The registry to use for element resolution
        cls: Optional class or class name to use for structuring
        preprocess: Whether to preprocess XML with lxml parser (recover mode).
                   Default is True.
        raise_on_error: Whether to raise exceptions on parsing errors.
                   Default is True.
        disable_defaults: Whether to disable default values when loading.
                   When True (default), fields not present in XML will be None
                   instead of their default values. This helps distinguish between
                   values explicitly set in the file vs. defaults.

    Returns:
        The parsed element or None if parsing fails
    """
    from attrs_xml.globals import disable_defaults as disable_defaults_ctx

    xml_dict = _parse_xml_to_dict(xml_text, preprocess=preprocess)
    if not xml_dict:
        log.error("Failed to parse XML text.")
        return None

    # Assuming the first key is the element name
    element_name = next(iter(xml_dict))

    cls_ = None
    if isinstance(cls, str):
        cls_ = elements_registry.class_by_name(cls)

    if not cls_:
        log.debug(
            f"Class passed as string {cls} could not be found in the registry. Rolling back to union_by_defname.",
        )

    structure_cls = cls_ if cls_ else elements_registry.union_by_defname(element_name)

    if not structure_cls:
        msg = f"No class could be identified to load element name: {element_name}"
        log.error(msg)
        raise ValueError(msg)

    try:
        # Conditionally disable defaults when structuring
        if disable_defaults:
            with disable_defaults_ctx():
                structured = elements_registry.converter.structure(
                    xml_dict[element_name],
                    structure_cls,
                )
        else:
            structured = elements_registry.converter.structure(
                xml_dict[element_name],
                structure_cls,
            )
    except Exception as exc:
        errors = transform_error(exc, format_exception=_format_exception)
        log.error(f"While parsing XML for element '{element_name}':")
        for e in errors:
            log.error(e)

        if raise_on_error:
            raise exc

        return None

    return structured


def load(
    file: os.PathLike,
    registry,
    preprocess: bool = True,
    raise_on_error: bool = False,
    disable_defaults: bool = True,
) -> BaseElement | None:
    """
    Load an XML file and return the corresponding element.

    Args:
        file: Path to the XML file to load
        registry: The registry to use for element resolution
        preprocess: Whether to preprocess XML with lxml parser (recover mode).
                   Default is True.
        raise_on_error: Whether to raise exceptions on parsing errors.
                   Default is False.
        disable_defaults: Whether to disable default values when loading.
                   When True (default), fields not present in XML will be None
                   instead of their default values. This helps distinguish between
                   values explicitly set in the file vs. defaults.

    Returns:
        The parsed element or None if parsing fails
    """
    log.info(f"Loading XML file: {file}")
    file = Path(file)
    if not file.is_file():
        log.error(f"File not found: {file}")
        return None

    with open(file) as f:
        xml_text = f.read()

    return loads(
        xml_text,
        registry,
        preprocess=preprocess,
        raise_on_error=raise_on_error,
        disable_defaults=disable_defaults,
    )


def dumps(obj, pretty: bool = True, style=True) -> str:
    """
    Convert an object to XML string representation.

    Args:
        obj: The object to convert
        pretty: Whether to format the XML with indentation
        root_key: The root key to use for the XML

    Returns:
        XML string representation of the object
    """
    return object_to_xml(obj, pretty=pretty)
    # if style:
    #     xml = style_xml_with_padding(xml, padding=" ")


def dump(obj, file: os.PathLike, pretty: bool = True) -> None:
    """
    Write an object to an XML file.

    Args:
        obj: The object to write
        file: The file path to write the XML to
        pretty: Whether to format the XML with indentation
    """
    file = Path(file)
    xml_content = dumps(obj, pretty=pretty)

    with open(file, "w") as f:
        f.write(xml_content)


def get_xml_block(
    xml: str | os.PathLike,
    index: int = 0,
    block_xpath: str = "//block",
) -> str | None:
    """
    Extract and print a specific XML block by index using lxml and XPath.

    Args:
        xml: Either an XML string or path to an XML file
        block_xpath: XPath expression to locate blocks (default: '//Block')
        index: Index of the block to extract from the list (0-based, default: 0)

    Returns:
        The XML block as a string, or None if not found

    Example:
        >>> # Get first Block element
        >>> xml_text = (
        ...     get_xml_block(
        ...         "file.xml"
        ...     )
        ... )
        >>> # Get third Block element
        >>> xml_text = (
        ...     get_xml_block(
        ...         "file.xml",
        ...         index=2,
        ...     )
        ... )
        >>> # Get second element from custom XPath
        >>> xml_text = get_xml_block(
        ...     "file.xml",
        ...     "//Timeline/Block",
        ...     index=1,
        ... )
    """
    from lxml import etree

    # Read XML content
    xml_path = Path(xml) if not isinstance(xml, Path) else xml
    if isinstance(xml, (str, Path)) and xml_path.is_file():
        xml_content = xml_path.read_text()
    else:
        xml_content = str(xml)

    try:
        # Parse with lxml
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        tree = etree.fromstring(xml_content.encode("utf-8"), parser=parser)

        # Find the blocks using XPath
        blocks = tree.xpath(block_xpath)

        if not blocks:
            log.warning(f"No blocks found matching XPath: {block_xpath}")
            return None

        log.info(f"Found {len(blocks)} blocks matching XPath: {block_xpath}")

        if index >= len(blocks):
            log.error(
                f"Index {index} out of range. Only {len(blocks)} blocks found.",
            )
            return None

        if index < 0:
            log.error("Index must be non-negative")
            return None

        # Convert the selected block to string
        block_xml = etree.tostring(
            blocks[index],
            encoding="unicode",
            pretty_print=True,
        )

        log.debug(f"Returning block at index {index}")
        log.debug(block_xml)
        return block_xml

    except (etree.XMLSyntaxError, ValueError) as e:
        log.error(f"Failed to extract XML block: {e}")
        return None
