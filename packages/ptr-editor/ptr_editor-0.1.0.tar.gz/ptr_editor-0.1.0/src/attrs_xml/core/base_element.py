from __future__ import annotations

from typing import ClassVar, Self

from attrs import asdict, define, field, fields, fields_dict


def _set_child_parent(child, parent: BaseElement):
    """Set the parent for a child, handling both single elements and lists."""
    if isinstance(child, list):
        for sub_child in child:
            _set_child_parent(sub_child, parent)

    if not hasattr(child, "parent"):
        return

    if isinstance(child, BaseElement):
        child.parent = parent


def _update_parents_for_all_children(parent: BaseElement):
    """Ensure that all children of the parent have their parent set to the parent."""
    for name in fields_dict(parent.__class__):
        child = getattr(parent, name)
        _set_child_parent(child, parent)


@define
class BaseElement:
    default_name: ClassVar[str | None] = None

    _parent: BaseElement | None = field(
        default=None,
        init=False,
        repr=False,
        eq=False,
        hash=False,
        metadata={"cattrs_omit": True},
    )

    _cache: dict = field(
        factory=dict,
        init=False,
        repr=False,
        hash=False,
        eq=False,
        metadata={"cattrs_omit": True},
    )

    def as_dict(self, recurse=False) -> dict:
        """Returns a dictionary representation of the element, excluding the parent."""
        return asdict(self, filter=lambda x, _: x.init, recurse=recurse)

    def __attrs_post_init__(self):
        """Post-initialization to set parent references."""
        _update_parents_for_all_children(self)

    @property
    def children(self) -> list[BaseElement]:
        """Returns a list of child base elements. No leaf elements."""
        return [
            getattr(self, attr.name)
            for attr in fields(self.__class__)
            if isinstance(getattr(self, attr.name), BaseElement)
            and attr.name != "_parent"
        ]

    @property
    def parent(self) -> BaseElement | None:
        """Returns the parent element of this element."""
        return self._parent

    @parent.setter
    def parent(self, value: BaseElement | None):
        self._parent = value

    def __copy__(self) -> Self:
        """Create a shallow copy of the element, without parent or cache."""
        # Create a new instance with the same class
        new_instance = self.__class__.__new__(self.__class__)

        # Copy all attributes except _parent and _cache
        for attr in fields(self.__class__):
            if attr.name not in ("_parent", "_cache"):
                setattr(new_instance, attr.name, getattr(self, attr.name))

        # Set _parent to None and create a new empty cache
        new_instance._parent = None
        new_instance._cache = {}

        return new_instance

    def __deepcopy__(self, memo) -> Self:
        """Create a deep copy of the element, without parent or cache."""
        from copy import deepcopy

        # Create a new instance with the same class
        new_instance = self.__class__.__new__(self.__class__)

        # Add to memo to handle circular references
        memo[id(self)] = new_instance

        # Deep copy all attributes except _parent and _cache
        for attr in fields(self.__class__):
            if attr.name not in ("_parent", "_cache"):
                value = deepcopy(getattr(self, attr.name), memo)
                setattr(new_instance, attr.name, value)

        # Set _parent to None and create a new empty cache
        new_instance._parent = None
        new_instance._cache = {}

        # Update parent references for all children
        _update_parents_for_all_children(new_instance)

        return new_instance

    def copy(self) -> Self:
        """Create a deep copy of the element, without parent or cache."""
        from copy import deepcopy
        return deepcopy(self)
