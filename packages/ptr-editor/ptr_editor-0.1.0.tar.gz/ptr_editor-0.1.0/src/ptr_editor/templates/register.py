import re
from copy import deepcopy
from pathlib import Path
from typing import get_args, get_origin

from attrs import define, field
from loguru import logger as log

from attrs_xml import BaseElement
from ptr_editor.services.quick_access import get_elements_registry

from .html import generate_notebook_html
from .template import Template



def _remove_placeholders(text: str) -> str:
    """Remove ${n:...} placeholder syntax and keep only the default values.
    Also removes placeholders without defaults like ${1}, ${2}, etc.
    Used for snippets.txt"""
    # Pattern: ${number:content} -> content
    pattern_with_default = r"\$\{(\d+):([^}]*)\}"
    text = re.sub(pattern_with_default, r"\2", text)
    
    # Pattern: ${number} -> empty string (remove placeholders without defaults)
    pattern_without_default = r"\$\{\d+\}"
    text = re.sub(pattern_without_default, "", text)
    
    return text


@define
class TemplateRegister:
    """
    A class to register templates for elements.

    Templates can be organized into groups using a namespace prefix.
    For example: 'soc:template_name' or 'custom:another_template'
    """

    _templates: dict[str, Template] = field(factory=dict)

    def get_as_template(self, template_name: str) -> Template | None:
        """
        Retrieve a Template object by name.

        :param template_name: The name of the template to retrieve.
        :return: The Template object if found, otherwise None.
        """
        return self._templates.get(template_name)

    def register(
        self,
        template_name: str,
        template: BaseElement | str,
        group: str | None = None,
        labels: list[str] | None = None,
    ) -> None:
        """
        Register a template with a given name.

        :param template_name: The name of the template to register.
        :param template: The template class or string to register.
        :param group: Optional group/namespace for the template (e.g., 'soc').
                      If provided, template will be stored as 'group:template_name'
        """
        if isinstance(template, str):
            try:
                template = get_elements_registry().from_xml(template)
            except Exception as e:
                log.error(f"Failed to parse template string: {e}")
                return

        # Add group prefix if provided
        full_name = f"{group}:{template_name}" if group else template_name

        # Wrap in Template object for internal storage
        template_obj = Template(
            name=full_name,
            element=template,
            group=group or "",
            labels=labels or [],
        )

        self._templates[full_name] = template_obj
        log.debug(f"Registered template: {full_name}")

    def unregister(self, template_name: str) -> None:
        """
        Unregister a template by name.

        :param template_name: The name of the template to unregister.
        """
        if template_name in self._templates:
            del self._templates[template_name]
            log.debug(f"Unregistered template: {template_name}")
        else:
            log.warning(f"Template {template_name} not found in registry.")

    def get(
        self,
        template_name: str,
        child_type: type | None = None,
    ) -> BaseElement | None:
        """
        Retrieve a template by name, optionally filtering for a child element by type.

        :param template_name: The name of the template to retrieve.
        :param child_type: Optional type or union of types to filter children.
                          If provided, searches the template's children for the
                          first element matching the specified type(s).
        :return: The template (or matching child) if found, otherwise None.

        Examples:
            >>> registry.get(
            ...     "my_template"
            ... )  # Returns the ObsBlock
            >>> registry.get(
            ...     "my_template",
            ...     TrackAttitude,
            ... )  # Returns attitude child
            >>> registry.get(
            ...     "my_template",
            ...     TrackAttitude
            ...     | LimbAttitude,
            ... )  # Union types
        """
        template_obj = self._templates.get(template_name)
        if template_obj is None:
            log.warning(f"Template {template_name} not found in registry.")
            return None

        # Get the underlying BaseElement from the Template wrapper
        template = template_obj.element
        item = deepcopy(template)

        # Clear the name attribute if present
        if hasattr(item, "name") and item.name:
            item.name = None

        # If no child_type specified, return the template itself
        if child_type is None:
            return item

        # Extract types from union if needed
        origin = get_origin(child_type)

        target_types = get_args(child_type) if origin is not None else (child_type,)

        # Search through children for matching type
        visited = set()  # Track visited elements to avoid infinite recursion
        return self._find_child_by_type(item, target_types, visited)

    def _find_child_by_type(
        self,
        element: BaseElement,
        target_types: tuple[type, ...],
        visited: set[int] | None = None,
    ) -> BaseElement | None:
        """
        Recursively search for a child element matching one of the target types.

        :param element: The element to search within.
        :param target_types: Tuple of types to match against.
        :param visited: Set of object IDs already visited to prevent cycles.
        :return: The first matching child element, or None if not found.
        """
        # Initialize visited set if not provided
        if visited is None:
            visited = set()

        # Avoid infinite recursion from circular references
        element_id = id(element)
        if element_id in visited:
            return None
        visited.add(element_id)

        # Get all fields of the element
        if not hasattr(element, "__attrs_attrs__"):
            return None

        for field_attr in element.__attrs_attrs__:
            field_value = getattr(element, field_attr.name, None)

            if field_value is None:
                continue

            # Check if field_value matches any of the target types
            if isinstance(field_value, target_types):
                log.debug(f"Found matching child of type {type(field_value).__name__}")
                return field_value

            # If field_value is a list, check each item
            if isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, target_types):
                        log.debug(
                            f"Found matching child of type {type(item).__name__} in list",
                        )
                        return item
                    # Recursively search within BaseElement items in the list
                    if isinstance(item, BaseElement):
                        result = self._find_child_by_type(item, target_types, visited)
                        if result is not None:
                            return result

            # Recursively search within BaseElement children
            elif isinstance(field_value, BaseElement):
                result = self._find_child_by_type(field_value, target_types, visited)
                if result is not None:
                    return result

        return None

    def __getitem__(self, template_name: str) -> BaseElement:
        """
        Get a template by name using bracket notation.

        :param template_name: The name of the template to retrieve.
        :return: The template.
        :raises KeyError: If template not found.
        """
        result = self.get(template_name)
        if result is None:
            raise KeyError(f"Template '{template_name}' not found in registry")
        return result

    def __contains__(self, template_name: str) -> bool:
        """
        Check if a template exists in the registry.

        :param template_name: The name of the template to check.
        :return: True if template exists, False otherwise.
        """
        return template_name in self._templates

    def list_templates(self, group: str | None = None) -> list[str]:
        """
        Get a list of all registered template names.

        :param group: Optional group filter. If provided, only return templates
                      from that group (e.g., 'soc' returns all 'soc:*' templates)
        :return: List of template names.
        """
        if group is None:
            return list(self._templates.keys())

        prefix = f"{group}:"
        return [key for key in self._templates if key.startswith(prefix)]

    def list_groups(self) -> list[str]:
        """
        Get a list of all groups/namespaces in the registry.

        :return: List of unique group names.
        """
        groups = set()
        for key in self._templates:
            if ":" in key:
                group = key.split(":", 1)[0]
                groups.add(group)
        return sorted(groups)

    def clear(self) -> None:
        """
        Clear all registered templates.
        """
        self._templates.clear()
        log.debug("Cleared all templates from registry.")

    def update(self, templates: dict[str, BaseElement | str]) -> None:
        """
        Update the registry with multiple templates at once.

        :param templates: Dictionary of template names to templates.
        """
        for name, template in templates.items():
            self.register(name, template)
        log.debug(f"Updated registry with {len(templates)} templates.")

    def _ipython_key_completions_(self):
        """
        Provide IPython key completions for template names.
        """
        return self.list_templates()

    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"TemplateRegister(templates={len(self._templates)})"

    def __len__(self) -> int:
        """Return the number of registered templates."""
        return len(self._templates)

    def _repr_html_(self) -> str:
        """
        IPython/Jupyter rich display representation.

        This method is automatically called by Jupyter notebooks to display
        the registry as formatted HTML instead of plain text.
        """
        return generate_notebook_html(self)

    def load_from_snippet_file(
        self,
        file_path: Path,
        group: str | None = None,
    ) -> dict[str, str]:
        """
        Load templates from a file.

        ESA's pointing tool snippet file format has each snippet separated by the
        word "snippet", followed by the snippet name.

        :param file_path: The path to the file containing template definitions.
        :param group: Optional group/namespace to assign to all loaded templates
                      (e.g., 'soc' will make templates accessible as
                      'soc:template_name')
        """
        out = {}
        if not file_path.exists():
            log.error(f"File {file_path} does not exist.")
            return out

        with file_path.open("r") as file:
            content = file.read()
            snippets = content.split("snippet")
            for snippet in snippets:
                if snippet.strip():
                    lines = snippet.strip().splitlines()
                    template_name = lines[0].strip()
                    template_code = "\n".join(lines[1:])

                    out[template_name] = template_code

        items = {key: _remove_placeholders(snippet) for key, snippet in out.items()}

        for key, snippet in items.items():
            self.register(key, snippet, group=group)

        return items

    def load_from_agm_predefined_blocks(self):
        """
        Load predefined blocks from the AGM predefined blocks XML file.
        """
        from ptr_editor.agm_config.agm_config import _get_agm_predefined_blocks_file
        from ptr_editor.agm_config.agm_utils import load_predefined_blocks

        file = _get_agm_predefined_blocks_file()
        predefined_blocks = load_predefined_blocks(file)
        if not predefined_blocks:
            log.warning(f"Failed to load predefined blocks from {file}")
            return

        for block in predefined_blocks.blocks:
            if not block.name:
                continue
            self.register(block.name, block, group="agm")


# def get_template_register() -> TemplateRegister:
#     """
#     Get the global template register instance from the context.

#     Returns:
#         TemplateRegister: The global template register instance, initialized
#                          with snippets and AGM predefined blocks.

#     Example:
#         >>> from ptr_editor.templates.register import get_template_register
#         >>> register = get_template_register()
#         >>> template = register.get("observation_block")
#     """
#     from ptr_editor.context import get_services

#     return get_services()["template_register"]
