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


def generate_box_tree(node: Node, _list_index: int = None) -> Box | None:
    """
    Recursively walks the DOM tree and builds the Render Tree.

    Args:
        node: The root DOM Node.
        _list_index: Internal counter passed down to `list-item` nodes.

    Returns:
        The root Box of the Render Tree, or None if `display: none`.
    """
    style = getattr(node, "style", {})
    display = style.get("display", "inline").strip().lower()

    if display == "none":
        return None  # Node and its children generate no boxes

    tag = getattr(node, "tag", "")

    # Process form inputs (synthesize text children representing their values)
    if tag in ("input", "textarea") and display != "none":
        # Form inputs don't usually have children in the DOM, so synthesize one
        value = getattr(node, "props", {}).get("value") or getattr(node, "props", {}).get("placeholder") or ""
        if tag == "textarea" and not value and getattr(node, "children", []):
            # For textarea, content might actually be a DOM child
            pass
        elif value:
            text_node = Node(tag="#text", props={})
            text_node.style = {"content": value}
            node.children = [text_node]

    # Determine the fundamental W3C box type and instantiate the Box geometry object
    if tag == "#text":
        box = TextBox(text_content=style.get("content", ""), node=node)
    elif display in ("block", "list-item"):
        box = BlockBox(node=node)
    elif display == "inline-block":
        from pypdfpatra.engine.tree import InlineBlockBox
        box = InlineBlockBox(node=node)
    else:
        # Defaults to inline for spans, anchors, strong, etc.
        box = InlineBox(node=node)

    # Process children, keeping track of list items if this node is an ordered/unordered list
    child_li_counter = 1
    if tag == "ol" or tag == "ul":
        start_val = getattr(node, "props", {}).get("start")
        if start_val is not None:
            try:
                child_li_counter = int(start_val)
            except ValueError:
                pass

    for child in getattr(node, "children", []):
        if isinstance(child, Node):
            child_style = getattr(child, "style", {})
            child_display = child_style.get("display", "inline").strip().lower()
            
            # Pass counter down only if it's a list item
            if child_display == "list-item" or getattr(child, "tag", "") == "li":
                child_box = generate_box_tree(child, _list_index=child_li_counter)
                child_li_counter += 1
            else:
                child_box = generate_box_tree(child)
                
            if child_box is not None:
                box.children.append(child_box)

    # Generate MarkerBox for list-items
    if display == "list-item":
        from pypdfpatra.engine.tree import MarkerBox
        list_style_type = style.get("list-style-type", "disc").strip().lower()
        
        marker_content = "__disc__"
        if list_style_type == "circle":
            marker_content = "__circle__"
        elif list_style_type == "square":
            marker_content = "__square__"
        elif list_style_type in ("decimal", "decimal-leading-zero"):
            val = _list_index if _list_index is not None else 1
            if list_style_type == "decimal-leading-zero" and val < 10:
                marker_content = f"0{val}."
            else:
                marker_content = f"{val}."

        marker_box = MarkerBox(text_content=marker_content, node=node)
        
        # Insert at the beginning of the children list
        box.children.insert(0, marker_box)

    return box
