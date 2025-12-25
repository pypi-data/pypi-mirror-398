from __future__ import annotations

from attrs_xml import element, element_define
from ptr_editor.core.ptr_element import PtrElement
from ptr_editor.elements.timeline import Timeline

from .blocks import BLOCKS, ObsBlock


@element_define
class Data(PtrElement):
    timeline: Timeline = element(factory=Timeline)


@element_define
class Segment(PtrElement):
    data: Data = element(factory=Data)


@element_define
class Body(PtrElement):
    segment: Segment = element(factory=Segment)


@element_define
class Prm(PtrElement):
    body: Body = element(factory=Body)

    @property
    def blocks(self) -> list[BLOCKS]:
        return self.body.segment.data.timeline.blocks

    @property
    def obs_blocks(self) -> list[ObsBlock]:
        return [
            block
            for block in self.body.segment.data.timeline.blocks
            if isinstance(block, ObsBlock)
        ]

    @property
    def timeline(self) -> Timeline:
        """Shorthand to access the timeline."""
        return self.body.segment.data.timeline


    @timeline.setter
    def timeline(self, value: Timeline) -> None:
        self.body.segment.data.timeline = value

    def _solvable_ptr_(self) -> str:
        """Serialize the timeline to PTR XML for solving."""
        return self.xml
