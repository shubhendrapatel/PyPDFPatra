"""
pypdfpatra.engine.box_generator
~~~~~~~~~~~~~~~~~~~~~~~~AAAA~~~
Converts the parsed DOM Tree (Nodes) into a W3C Render Tree (Boxes).

The Box tree is the actual structure used for layout and painting.
Elements with `display: none` are dropped. Nodes are converted into:
- Block Box (`display: block` or `list-item`)
- Inline Box (`display: inline`)
- Text Box (`tag == 'text'`)
"""

from __future__ import annotations
from pypdfpatra.engine.tree import Node, Box, BlockBox, InlineBox, TextBox


def generate_box_tree(node: Node) -> Box | None:
    """
    Recursively walks the DOM tree and builds the Render Tree.

    Args:
        node: The root DOM Node.

    Returns:
        The root Box of the Render Tree, or None if `display: none`.
    """
    style = node.style
    display = style.get("display", "inline").strip().lower()

    if display == "none":
        return None  # Node and its children generate no boxes

    tag = getattr(node, "tag", "")

    # Determine the fundamental W3C box type and instantiate the Box geometry object
    if tag == "#text":
        box = TextBox(text_content=style.get("content", ""), node=node)
    elif display in ("block", "list-item"):
        box = BlockBox(node=node)
    else:
        # Defaults to inline for spans, anchors, strong, etc.
        box = InlineBox(node=node)

    # Process children
    for child in node.children:
        if isinstance(child, Node):
            child_box = generate_box_tree(child)
            if child_box is not None:
                box.children.append(child_box)

    return box
