from lxml import etree


def add_block_comments(xml_content, id_generator):
    """
    Add comment strings before and after each <block> element in XML.

    Parameters
    ----------
    xml_content : str or bytes
        The XML content to process
    id_generator : callable
        Function that takes the block index (int) and returns a tuple of
        (start_comment, end_comment) strings

    Returns
    -------
    str
        The modified XML with comments added around each <block> element

    Examples
    --------
    >>> def my_id_gen(idx):
    ...     return (
    ...         f"BLOCK_{idx}_START",
    ...         f"BLOCK_{idx}_END",
    ...     )
    >>> xml = '<root><block id="1"/><block id="2"/></root>'
    >>> result = add_block_comments(
    ...     xml, my_id_gen
    ... )
    """
    # Parse the XML
    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8")

    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.fromstring(xml_content, parser)

    # Find all <block> elements
    blocks = tree.xpath(".//block")

    # Process each block in reverse order to maintain correct positions
    for idx, block in enumerate(reversed(blocks)):
        # Get the actual index (since we're reversing)
        actual_idx = len(blocks) - idx - 1

        # Generate the comment strings
        start_comment, end_comment = id_generator(actual_idx)

        # Get parent and position
        parent = block.getparent()
        position = list(parent).index(block)

        # Create comment nodes with newlines
        start_comment_node = etree.Comment(start_comment)
        end_comment_node = etree.Comment(end_comment)

        # Add tail newline to start comment to ensure block is on new line
        start_comment_node.tail = "\n" + (block.tail or "")
        block.tail = "\n"

        # Preserve any existing tail on the block for the end comment
        end_comment_node.tail = block.tail

        # Insert comments before and after the block
        parent.insert(position, start_comment_node)
        parent.insert(position + 2, end_comment_node)

    # Return the modified XML as string
    return etree.tostring(tree, encoding="unicode", pretty_print=True)


def add_block_comments_to_file(input_file, output_file, id_generator):
    """
    Read XML from file, add block comments, and write to output file.

    Parameters
    ----------
    input_file : str or Path
        Path to input XML file
    output_file : str or Path
        Path to output XML file
    id_generator : callable
        Function that takes the block index (int) and returns a tuple of
        (start_comment, end_comment) strings
    """
    with open(input_file, "rb") as f:
        xml_content = f.read()

    result = add_block_comments(xml_content, id_generator)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    # Example usage
    sample_xml = """<?xml version="1.0"?>
<root>
    <block id="block1">
        <data>Content 1</data>
    </block>
    <block id="block2">
        <data>Content 2</data>
    </block>
    <other>
        <block id="block3">
            <data>Content 3</data>
        </block>
    </other>
</root>"""

    def example_id_generator(idx):
        """Generate start and end comment strings for a block."""
        return (f"BLOCK_{idx}_START", f"BLOCK_{idx}_END")

    result = add_block_comments(sample_xml, example_id_generator)
    print(result)
