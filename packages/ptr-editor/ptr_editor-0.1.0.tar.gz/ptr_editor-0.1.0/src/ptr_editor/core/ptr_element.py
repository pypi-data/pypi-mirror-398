from __future__ import annotations

from typing import TYPE_CHECKING, Self

from attrs import define

from attrs_xml import BaseElement
from attrs_xml.core.decorators_utils import classproperty
from attrs_xml.formatting import to_snake_case

if TYPE_CHECKING:
    from ptr_editor.generators.processor import GeneratorProcessor
    from ptr_editor.validation import Result, RuleRegistry, RulesetConfig
    from ptr_editor.diffing.xml_diff_result import XmlDiffResult

from copy import deepcopy


def _get_all_subclasses_sorted(klass: type) -> set[type]:
    """Recursively get all subclasses of a class in deterministic order.
    
    This function sorts subclasses by their qualified name to ensure deterministic
    behavior regardless of Python's hash randomization. This is critical for
    avoiding intermittent bugs in type registration and union disambiguation.
    
    **Why this matters:**
    
    Python's `__subclasses__()` returns classes in an order that varies based on
    hash randomization (PYTHONHASHSEED). When this function is called during module
    import (via @element_define decorators), it affects:
    
    1. Class registration order in the ElementsRegistry
    2. Union type construction order (Union[A, B, C] vs Union[C, A, B])
    3. Cattrs disambiguation logic (which type to try first when deserializing)
    
    **Bug this prevents:**
    
    Without sorting, PTR file loading would succeed or fail **intermittently**:
    - Behavior was consistent within a Python session (all success or all failure)
    - Behavior varied between kernel restarts due to different hash seeds
    - Same code/file would work on one run, fail on the next
    
    The root cause was that Union[TypeA, TypeB] and Union[TypeB, TypeA] caused
    cattrs to try types in different orders during XML deserialization, leading
    to different disambiguation results and thus different success/failure outcomes.
    
    Args:
        klass: The base class to find subclasses for
        
    Returns:
        Set of all subclasses (at any depth) in deterministic order
        
    """
    all_subclasses = set()
    # Sort subclasses by qualified name for deterministic ordering
    for subclass in sorted(klass.__subclasses__(), key=lambda c: (c.__module__, c.__qualname__)):
        all_subclasses.add(subclass)
        all_subclasses.update(_get_all_subclasses_sorted(subclass))
    return all_subclasses


@define
class PtrElement(BaseElement):
    # Descriptor for cached accessor - NOT an attrs field

    @classproperty
    def element_type(cls) -> str:
        """Returns the type of the value based on its class name."""
        # get the name of the parent class, if any:
        parent_class_name = to_snake_case(
            cls.__bases__[0].__name__ if cls.__bases__ else None,
        ).upper()
        class_name = to_snake_case(cls.__name__).upper()
        if parent_class_name in class_name:
            return class_name.replace(parent_class_name, "").strip("_")

        return class_name

    def expand(
        self,
        processor: GeneratorProcessor | None = None,
        *,
        inplace: bool = False,
    ) -> Self:
        if processor is None:
            from ptr_editor.generators.processor import GeneratorProcessor

            processor = GeneratorProcessor()

        if not inplace:
            element_copy = deepcopy(self)
            return processor.process(element_copy)
        return processor.process(self)

    @classproperty
    def children_types(cls) -> list[str]:
        """
        Returns a list of all type attributes from known subclasses at any level.

        This recursively collects the 'type' property from the current class
        and all its subclasses, providing a comprehensive list of all known
        types in the class hierarchy.

        Returns:
            list[str]: Sorted list of unique type strings from all subclasses

        Example:
            >>> from ptr_editor import (
            ...     PtrElement,
            ...     Attitude,
            ... )
            >>> all_types = (
            ...     Attitude.children_types
            ... )
            >>> print(all_types)
            ['ATTITUDE', 'CAPTURE', 'FLIP', 'ILLUMINATED_POINT', 'INERTIAL', ...]
        """
        # Collect types from current class and all subclasses
        types_set = set()

        # Add types from all subclasses
        for subclass in _get_all_subclasses_sorted(cls):
            try:
                types_set.add(subclass.element_type)
            except (AttributeError, TypeError):
                pass

        # Return sorted list of unique types (filter to only strings)
        return sorted([t for t in types_set if isinstance(t, str)])

    @classmethod
    def docstring_summary(cls, include_self: bool = True) -> dict[str, str]:
        """
        Generate a summary of docstrings for this class and all its subclasses.

        This method recursively collects the first line of the docstring from
        the current class and all its subclasses, providing a quick overview
        of available types and their purposes.

        Args:
            include_self: Whether to include the current class in the summary.
                Default: True

        Returns:
            dict[str, str]: Dictionary mapping class names to their first
                docstring line. Classes without docstrings are marked as
                "NO DOCSTRING".

        Example:
            >>> from ptr_editor import (
            ...     Attitude,
            ... )
            >>> summary = Attitude.docstring_summary()
            >>> for (
            ...     name,
            ...     doc,
            ... ) in sorted(
            ...     summary.items()
            ... ):
            ...     print(
            ...         f"{name}: {doc}"
            ...     )
            Attitude: Base class for all spacecraft attitudes.
            CaptureAttitude: Capture attitude for spacecraft capture/insertion...
            InertialAttitude: Inertial attitude for pointing at fixed directions...
            ...

            >>> # Print formatted summary
            >>> Attitude.print_docstring_summary()
        """
        summary = {}

        # Add current class if requested
        if include_self:
            doc = cls.__doc__
            if doc:
                first_line = doc.strip().split("\n")[0]
                summary[cls.__name__] = first_line
            else:
                summary[cls.__name__] = "NO DOCSTRING"

        # Add all subclasses
        for subclass in _get_all_subclasses_sorted(cls):
            doc = subclass.__doc__
            if doc:
                first_line = doc.strip().split("\n")[0]
                summary[subclass.__name__] = first_line
            else:
                summary[subclass.__name__] = "NO DOCSTRING"

        return summary

    @classmethod
    def print_docstring_summary(cls, include_self: bool = True, width: int = 70):
        """
        Print a formatted summary of docstrings for this class and subclasses.

        Prints a nicely formatted table showing all subclasses and their
        docstring summaries, useful for quick reference and documentation.

        Args:
            include_self: Whether to include the current class. Default: True
            width: Width of the separator line. Default: 70

        Example:
            >>> from ptr_editor import (
            ...     Attitude,
            ... )
            >>> Attitude.print_docstring_summary()
            ======================================================================
            Docstring Summary for Attitude and subclasses:
            ======================================================================
            Attitude                      : Base class for all spacecraft attitudes.
            CaptureAttitude               : Capture attitude for spacecraft...
            ...
        """
        summary = cls.docstring_summary(include_self=include_self)

        print("=" * width)
        print(f"Docstring Summary for {cls.__name__} and subclasses:")
        print("=" * width)

        # Find max class name length for alignment
        max_name_len = max(len(name) for name in summary.keys()) if summary else 30

        # Print sorted by class name
        for name in sorted(summary.keys()):
            doc_line = summary[name]
            print(f"{name:{max_name_len}s} : {doc_line}")

    def to_xml(self, pretty=True, key: str = "") -> str:
        from ptr_editor.services.quick_access import get_elements_registry

        ptr = get_elements_registry()

        return ptr.to_xml(self, pretty=pretty, root_key=key)

    @property
    def xml(self) -> str:
        """Returns the XML representation of the element."""
        return self.to_xml(pretty=True)

    # def __str__(self) -> str:
    #     return self.to_xml(pretty=True)

    @classmethod
    def from_xml(cls, xml: str, *, disable_defaults: bool = True) -> Self:
        """Load element from XML string.
        
        Args:
            xml: XML string to parse
            disable_defaults: Whether to disable default values when loading.
                When True (default), fields not present in XML will be None
                instead of their default values.
        
        Returns:
            Parsed element instance
        """
        from ptr_editor.services.quick_access import get_elements_registry

        ptr = get_elements_registry()

        return ptr.from_xml(xml, disable_defaults=disable_defaults)

    def _repr_html_(self) -> str:
        """Return syntax-highlighted HTML representation for Jupyter notebooks."""
        from ptr_editor.elements.blocks import render_xml_html2

        return render_xml_html2(self.xml)

    def validate(
        self,
        *,
        registry: RuleRegistry | None = None,
        recursive: bool = True,
        raise_on_error: bool = False,
        ruleset: RulesetConfig | str | list[str] = "ptr",
    ) -> Result:
        """
        Validate this PTR element.

        This method validates the current element (and optionally its children)
        using the validation registry. By default, it uses the global validation
        registry and a default ruleset.

        Args:
            registry: Validation registry to use. If None, uses the global
                registry from context (default: None)
            recursive: Whether to validate nested elements recursively
                (default: True)
            raise_on_error: If True, raises an exception if validation fails
                (default: False)
            ruleset: RulesetConfig to use. If None, creates a default ruleset
                with all PTR rules (default: None)

        Returns:
            Result: Validation result containing all issues found

        Raises:
            ValueError: If raise_on_error=True and validation fails

        Example:
            >>> block = TimedBlock()
            >>> block.start = (
            ...     datetime(
            ...         2024, 1, 2
            ...     )
            ... )
            >>> block.end = datetime(
            ...     2024, 1, 1
            ... )  # Invalid: end before start
            >>> result = (
            ...     block.validate()
            ... )
            >>> if not result.ok:
            ...     for error in result.errors():
            ...         print(error)

            >>> # With custom ruleset
            >>> from ptr_editor.validation import (
            ...     RulesetConfig,
            ... )
            >>> strict = (
            ...     RulesetConfig(
            ...         "strict"
            ...     )
            ... )
            >>> strict.include_rules_with_tags(
            ...     ["critical"]
            ... )
            >>> result = block.validate(
            ...     ruleset=strict
            ... )

            >>> # Raise exception on error
            >>> try:
            ...     block.validate(
            ...         raise_on_error=True
            ...     )
            ... except (
            ...     ValueError
            ... ) as e:
            ...     print(
            ...         f"Validation failed: {e}"
            ...     )
        """
        # Get registry from context if not provided
        if registry is None:
            from ptr_editor.services.quick_access import get_validation_registry

            registry = get_validation_registry()

        if isinstance(ruleset, str) or isinstance(ruleset, list):
            from ptr_editor.validation.ptr_validators import get_ruleset

            ruleset = get_ruleset(ruleset)

        # Validate
        result = registry.validate(self, recursive=recursive, ruleset=ruleset)

        # Optionally raise on error
        if raise_on_error and not result.ok:
            error_messages = [str(error) for error in result.errors()]
            msg = (
                f"Validation failed with {len(error_messages)} error(s):\n"
                + "\n".join(f"  - {msg}" for msg in error_messages)
            )
            raise ValueError(msg)

        return result

    def xml_diff(
        self,
        other: Self,
        *,
        context_lines: int = 3,
    ) -> XmlDiffResult:
        """
        Compare the XML representation of this element with another element.

        This method uses Python's difflib for simple text-based diff comparison,
        which is useful for understanding differences in the serialized PTR format.
        Unlike the `diff()` method which compares Python object attributes, this
        compares the actual XML text.

        The result displays as a side-by-side comparison in Jupyter notebooks,
        similar to the HTML reports generated by the matcher.

        Args:
            other: The other PtrElement to compare against
            context_lines: Number of context lines to show around changes (default: 3)

        Returns:
            XmlDiffResult: Object containing diff information with methods for
                          display and analysis

        Example:
            >>> # Basic XML diff - shows side-by-side in Jupyter
            >>> block1 = ObsBlock(
            ...     id="OBS_001",
            ...     start=...,
            ...     end=...,
            ... )
            >>> block2 = ObsBlock(
            ...     id="OBS_001",
            ...     start=...,
            ...     end=...,
            ... )
            >>> xml_diff = (
            ...     block1.xml_diff(
            ...         block2
            ...     )
            ... )
            >>> xml_diff  # Displays rich side-by-side HTML in Jupyter
            >>>
            >>> # Access diff statistics
            >>> if xml_diff.has_changes:
            ...     print(
            ...         f"Found {xml_diff.change_count} line changes"
            ...     )
            ...     print(
            ...         f"  + {xml_diff.stats['additions']} additions"
            ...     )
            ...     print(
            ...         f"  - {xml_diff.stats['deletions']} deletions"
            ...     )
            >>>
            >>> # Get text summary
            >>> print(
            ...     xml_diff.summary()
            ... )
            >>>
            >>> # Get unified diff text
            >>> print(
            ...     xml_diff.as_text()
            ... )
            >>>
            >>> # Get colored terminal output
            >>> print(
            ...     xml_diff.as_text(
            ...         color=True
            ...     )
            ... )
            >>>
            >>> # Get HTML for embedding
            >>> html = xml_diff.as_html(
            ...     side_by_side=True
            ... )  # Side-by-side (default)
            >>> html = xml_diff.as_html(
            ...     side_by_side=False
            ... )  # Unified diff
        """
        from ptr_editor.diffing.xml_diff_result import XmlDiffResult

        # Get XML representations
        left_xml = self.xml
        right_xml = other.xml

        # Create and return result object
        return XmlDiffResult(
            left_xml=left_xml,
            right_xml=right_xml,
            left_label=f"{self.__class__.__name__} (self)",
            right_label=f"{other.__class__.__name__} (other)",
            context_lines=context_lines,
        )
