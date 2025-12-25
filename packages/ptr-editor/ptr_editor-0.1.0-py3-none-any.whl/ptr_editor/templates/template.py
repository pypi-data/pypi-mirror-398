from attrs import define, field

from attrs_xml import BaseElement


@define
class Template:
    name: str = field()
    element: BaseElement = field()  # the actual template element
    group: str = field(default="")  # optional group name for grouping templates
    description: str = field(default="")  # optional description
    labels: list[str] = field(factory=list)  # optional list of labels for filtering
