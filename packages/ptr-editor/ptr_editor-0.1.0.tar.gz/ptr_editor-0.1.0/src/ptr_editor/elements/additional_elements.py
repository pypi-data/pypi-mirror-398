from attrs_xml.core.decorators import element_define
from ptr_editor import BaseElement
from ptr_editor.elements.blocks import ObsBlock


@element_define
class BlocksList(BaseElement):
    """
    A simple container for blocks.
    """

    blocks: list[ObsBlock] = element(tag="block")
