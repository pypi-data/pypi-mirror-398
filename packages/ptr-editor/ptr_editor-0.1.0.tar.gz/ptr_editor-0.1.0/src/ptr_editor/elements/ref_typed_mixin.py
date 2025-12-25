from attrs import fields_dict
from attrs_xml.decorators_old import classproperty

from attrs_xml.formatting import to_snake_case


class RefTypedMixin:
    """A mixin class that provides a typed reference attribute."""

    @classproperty
    def type(cls) -> str:
        """Returns the type of the element based on its ref attribute."""
        default = fields_dict(cls).get("ref").default
        return to_snake_case(default).upper()
