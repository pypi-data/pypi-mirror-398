
from attrs_xml.core.decorators import element_define
from attrs_xml.core.fields import element
from attrs_xml.xml.io import loads
from ptr_editor.elements.blocks import ObsBlock


@element_define(defname="AGMPredefinedBlocks")
class AGMPredefinedBlocks:
    blocks: list[ObsBlock] = element(factory=list, tag="block")


def load_predefined_blocks(file):
    """
    Load predefined blocks for AGM configuration.
    """

    # Path to the predefined blocks XML file
    from ptr_editor.agm_validator.agm_config_validator import agm_validation_disabled

    with open(file) as f:
        content = f.read()

    # append an xml root element
    content = f"<AGMPredefinedBlocks>\n{content}\n</AGMPredefinedBlocks>"
    from ptr_editor.services.quick_access import get_elements_registry
    with agm_validation_disabled():
        got = loads(content, elements_registry=get_elements_registry())
    # if not got:
    #     msg = f"Failed to load predefined blocks from {predefined_blocks_file}"
    #     raise ValueError(msg)
    return got
