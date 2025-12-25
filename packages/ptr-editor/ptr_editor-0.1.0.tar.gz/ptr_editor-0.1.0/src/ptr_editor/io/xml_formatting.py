from xml.etree import ElementTree as ET

import xmlformatter


def strip_whitespace_from_text_elements(xml_string: str) -> str:
    # Parse the XML file
    tree = ET.fromstring(xml_string)
    root = tree

    # Recursively strip whitespace from each element's text and tail
    def strip_whitespace(element):
        if element.text:
            element.text = element.text.strip()
        if element.tail:
            element.tail = element.tail.strip()
        for child in element:
            strip_whitespace(child)

    # Apply whitespace stripping
    strip_whitespace(root)

    return ET.tostring(tree, encoding="unicode")


def sort_xml_elements_and_attributes(xml_string: str) -> str:
    def sort_element(element):
        # Sort child elements by tag name
        element[:] = sorted(element, key=lambda e: e.tag)
        # Sort attributes of each element (convert to dict, sort, and update)
        sorted_attributes = dict(sorted(element.attrib.items()))
        element.attrib.clear()
        element.attrib.update(sorted_attributes)
        # Recursively sort children
        for child in element:
            sort_element(child)

    # Parse and modify the XML tree
    root = ET.fromstring(xml_string)
    sort_element(root)
    return ET.tostring(root, encoding="unicode")


def format_xml_for_comparison(text: str) -> str:
    text = strip_whitespace_from_text_elements(text)
    text = sort_xml_elements_and_attributes(text)

    formatter = xmlformatter.Formatter(
        indent="4",
        indent_char=" ",
        encoding_output="UTF8",
        correct=True,
    )
    formatted = formatter.format_string(text)
    return formatted.decode()


def style_xml_with_padding(xml_string: str, padding: str = " ") -> str:
    """Style XML by adding padding around text content."""

    # Parse the XML
    root = ET.fromstring(xml_string)

    all_blocks = root.findall(".//block")

    def add_padding_to_element(element):
        # if element is named "planning", skip padding
        if element.tag == "planning":
            return

        # Add padding to text content
        if element.text and element.text.strip():
            element.text = f"{padding}{element.text.strip()}{padding}"

        # Add padding to tail content (text after closing tag)
        if element.tail and element.tail.strip():
            element.tail = f"{padding}{element.tail.strip()}{padding}"

        # Recursively process child elements first (before modifying the structure)
        children = list(element)  # Create a copy to avoid modification during iteration
        for child in children:
            add_padding_to_element(child)

    def add_block_comments(element, parent=None):
        """Add comments before block elements in a separate pass"""
        if element.tag == "block" and parent is not None:
            # we add a comment just before the block element
            # comment must be <!-- Block (19) --> and properly indented

            # Find the index of this element in its parent
            element_index = list(parent).index(element)

            block_index = all_blocks.index(element)
            comment = ET.Comment(f" Block ({block_index + 1}) ")

            # Insert comment before the block element
            parent.insert(element_index, comment)

            # Get the indentation from the block element's tail or calculate it
            # The block element should have proper indentation already
            if element.tail and "\n" in element.tail:
                # Extract indentation from the block element's tail
                lines = element.tail.split("\n")
                if len(lines) > 1:
                    block_indent = lines[-1]  # Last line contains the indentation
                else:
                    block_indent = ""
            else:
                # Calculate indentation based on nesting level
                # Count parent levels to determine indentation
                indent_level = 0
                current = parent
                while current is not None:
                    indent_level += 1
                    current = (
                        current.getparent() if hasattr(current, "getparent") else None
                    )
                block_indent = "   " * indent_level  # 3 spaces per level

            # Set the comment's tail to have proper spacing and preserve block indentation
            comment.tail = f"\n{block_indent}"

            # Ensure the block element maintains its indentation after the comment
            if not element.tail or not element.tail.startswith("\n"):
                element.tail = f"\n{block_indent}"

            # Add empty line before the comment by modifying the previous element's tail
            # or the parent's text if this is the first element
            if element_index > 0:
                # There's a previous element, modify its tail
                prev_element = parent[element_index - 1]
                if prev_element.tail:
                    # Preserve existing indentation but add extra newline
                    prev_tail = prev_element.tail.rstrip()
                    prev_element.tail = f"{prev_tail}\n\n{block_indent}"
                else:
                    prev_element.tail = f"\n\n{block_indent}"
            # This is the first element, modify parent's text
            elif parent.text:
                parent.text = parent.text.rstrip() + f"\n\n{block_indent}"
            else:
                parent.text = f"\n\n{block_indent}"

        # Process children
        children = list(element)  # Create a copy to avoid modification during iteration
        for child in children:
            add_block_comments(child, element)

    # First pass: add padding to text content
    add_padding_to_element(root)

    # Third pass: add block comments (after structure is stable)
    add_block_comments(root)

    # Convert back to string
    return ET.tostring(root, encoding="unicode")
