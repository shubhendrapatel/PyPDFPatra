"""
pypdfpatra.engine.layout.box_generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Converts the parsed DOM Tree (Nodes) into a W3C Render Tree (Boxes).

The Box tree is the actual structure used for layout and painting.
Elements with `display: none` are dropped. Nodes are converted into:
- Block Box (`display: block` or `list-item`)
- Inline Box (`display: inline`)
- Text Box (`tag == 'text'`)
"""

from __future__ import annotations

from pypdfpatra.engine.image import get_image_info
from pypdfpatra.engine.tree import (
    BlockBox,
    Box,
    ImageBox,
    InlineBlockBox,
    InlineBox,
    MarkerBox,
    Node,
    TableBox,
    TableCellBox,
    TableRowBox,
    TableRowGroupBox,
    TextBox,
)


def generate_box_tree(
    node: Node, base_url: str = "", _list_index: int = None
) -> Box | None:
    """
    Recursively processes an HTML DOM Node and generates the appropriate W3C
    Formatting Context Box geometries based on the computed CSS `display` style.
    """
    if not isinstance(node, Node):
        return None
    style = getattr(node, "style", {})
    display = style.get("display", "inline").strip().lower()

    if display == "none":
        return None  # Node and its children generate no boxes

    tag = getattr(node, "tag", "")

    # Process form inputs (synthesize text children representing their values)
    if tag in ("input", "textarea") and display != "none":
        # Form inputs don't usually have children in the DOM, so synthesize one
        value = (
            getattr(node, "props", {}).get("value")
            or getattr(node, "props", {}).get("placeholder")
            or ""
        )
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
    elif tag == "img":
        src = getattr(node, "props", {}).get("src", "")
        alt_text = getattr(node, "props", {}).get("alt", "")

        info = get_image_info(src, base_url)

        img_w = info["width"] if info else 100.0  # Default fallback box
        img_h = info["height"] if info else 100.0

        box = ImageBox(
            img_src=info["src"] if info else src,
            image_w=img_w,
            image_h=img_h,
            alt_text=alt_text,
            node=node,
        )
    elif display == "inline-block":
        box = InlineBlockBox(node=node)
    elif display == "table":
        box = TableBox(node=node)
    elif display in ("table-row-group", "table-header-group", "table-footer-group"):
        box = TableRowGroupBox(node=node)
    elif display == "table-row":
        box = TableRowBox(node=node)
    elif display == "table-cell":
        box = TableCellBox(node=node)
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
                child_box = generate_box_tree(
                    child, base_url, _list_index=child_li_counter
                )
                child_li_counter += 1
            else:
                child_box = generate_box_tree(child, base_url)

            if child_box is not None:
                box.children.append(child_box)

    # 3. Generate MarkerBox for list-items
    if display == "list-item":
        _inject_list_marker(box, style, _list_index)

    # 4. Generate Pseudo-Elements (Phase 8 - Refactored)
    _process_pseudo_elements(node, box, base_url)

    return box


def _process_pseudo_elements(node: Node, box: Box, base_url: str):
    """
    Synthesizes virtual nodes for ::before and ::after pseudo-elements.
    """
    # Handle ::before
    before_style = node.pseudos.get("before")
    if before_style and "content" in before_style:
        content_val = before_style["content"].strip("'\"")
        if content_val and content_val != "none":
            pseudo_node = Node(tag="#text", props={})
            pseudo_node.parent = node
            pseudo_node.style = before_style.copy()
            pseudo_node.style["content"] = content_val
            pseudo_box = generate_box_tree(pseudo_node, base_url)
            if pseudo_box:
                box.children.insert(0, pseudo_box)

    # Handle ::after
    after_style = node.pseudos.get("after")
    if after_style and "content" in after_style:
        content_val = after_style["content"].strip("'\"")
        if content_val and content_val != "none":
            pseudo_node = Node(tag="#text", props={})
            pseudo_node.parent = node
            pseudo_node.style = after_style.copy()
            pseudo_node.style["content"] = content_val
            pseudo_box = generate_box_tree(pseudo_node, base_url)
            if pseudo_box:
                box.children.append(pseudo_box)


def _inject_list_marker(box: Box, style: dict, _list_index: int):
    """Generates the bullet/number marker for a list item."""
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

    marker_box = MarkerBox(text_content=marker_content, node=box.node)
    box.children.insert(0, marker_box)
