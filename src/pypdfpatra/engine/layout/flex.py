"""
pypdfpatra.engine.layout.flex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
W3C Flexbox Formatting Context (FFC) implementation.
"""

from __future__ import annotations

from pypdfpatra.engine.tree import AnonymousBlockBox, Box

from .block import PosCB, layout_block_context


def _get_intrinsic_width(box: Box) -> float:
    """Finds the maximum content edge (max-content) of a box."""
    if box.__class__.__name__ == "TextBox":
        return box.w

    children = getattr(box, "children", [])
    if not children:
        return box.w if box.w > 0 else 0.0

    max_edge = 0.0
    for child in children:
        child_w = _get_intrinsic_width(child)
        # Handle cases where child.x might not be set yet (dry run)
        child_x = getattr(child, "x", 0.0) or 0.0
        max_edge = max(max_edge, child_x + child_w)

    padding_r = getattr(box, "padding_right", 0.0)
    border_r = getattr(box, "border_right", 0.0)
    return max_edge + padding_r + border_r


def _get_outer_height(box: Box) -> float:
    """Returns the total vertical space occupied by a box (margin-box height)."""
    return (
        getattr(box, "margin_top", 0.0)
        + getattr(box, "border_top", 0.0)
        + getattr(box, "padding_top", 0.0)
        + box.h
        + getattr(box, "padding_bottom", 0.0)
        + getattr(box, "border_bottom", 0.0)
        + getattr(box, "margin_bottom", 0.0)
    )


def _get_decorations_h(box: Box) -> float:
    """Returns the sum of borders and paddings."""
    return (
        getattr(box, "border_top", 0.0)
        + getattr(box, "padding_top", 0.0)
        + getattr(box, "padding_bottom", 0.0)
        + getattr(box, "border_bottom", 0.0)
    )


def layout_flex_context(
    box: Box, content_x: float, content_y: float, cb_w: float, pos_cb: PosCB = None
) -> float:
    """
    Lays out children in a flex container.
    """
    style = getattr(box.node, "style", {}) if box.node else {}
    flex_direction = style.get("flex-direction", "row").strip().lower()
    justify_content = style.get("justify-content", "flex-start").strip().lower()
    align_items = style.get("align-items", "stretch").strip().lower()

    # Determine container's fixed content height if specified
    # (Since box.h is currently 0 in layout_block_context before this call)
    container_fixed_h = 0.0
    style_h_str = str(style.get("height", "auto")).strip().lower()
    if style_h_str != "auto" and "px" in style_h_str:
        try:
            container_fixed_h = float(style_h_str.replace("px", ""))
        except (ValueError, TypeError):
            pass

    # Gather flow children
    flow_children = [
        c
        for c in box.children
        if getattr(c, "position", "static") not in ("absolute", "fixed")
    ]

    if not flow_children:
        return content_y

    if flex_direction == "column":
        curr_y = content_y
        for child in flow_children:
            layout_block_context(child, content_x, curr_y, cb_w, pos_cb=pos_cb)
            # Increment by outer height to prevent overlap
            curr_y += _get_outer_height(child)
        return curr_y

    # Default: Flex Row
    total_children_w = 0.0
    tallest_outer_h = 0.0

    # Pass 1: Measure children
    for child_box in flow_children:
        # Dry run for width
        style_w = getattr(child_box.node, "style", {}).get("width", "auto")
        if style_w == "auto":
            layout_block_context(child_box, 0, 0, cb_w, pos_cb=pos_cb)
            child_box.w = _get_intrinsic_width(child_box)
        else:
            layout_block_context(child_box, 0, 0, cb_w, pos_cb=pos_cb)

        total_children_w += child_box.w
        tallest_outer_h = max(tallest_outer_h, _get_outer_height(child_box))

    # Determine line height
    line_h = max(container_fixed_h, tallest_outer_h)

    curr_x = content_x
    spacing = 0.0
    remaining_w = cb_w - total_children_w

    if justify_content == "flex-end":
        curr_x += remaining_w
    elif justify_content == "center":
        curr_x += remaining_w / 2.0
    elif justify_content == "space-between" and len(flow_children) > 1:
        spacing = remaining_w / (len(flow_children) - 1)

    # Pass 2: Positioning and Alignment
    for child_box in flow_children:
        child_outer_h = _get_outer_height(child_box)
        y_offset = 0.0

        if align_items == "stretch":
            # Set child height to fill available line space
            # (minus its own decorations/margins)
            decor = _get_decorations_h(child_box)
            mt = getattr(child_box, "margin_top", 0.0)
            mb = getattr(child_box, "margin_bottom", 0.0)
            margins = mt + mb
            child_box.h = max(0.0, line_h - decor - margins)
            y_offset = 0.0
        elif align_items == "flex-end":
            y_offset = line_h - child_outer_h
        elif align_items == "center":
            y_offset = (line_h - child_outer_h) / 2.0

        if isinstance(child_box, AnonymousBlockBox):
            from .inline import layout_inline_context
            child_box.x = curr_x
            child_box.y = content_y + y_offset
            layout_inline_context(
                child_box, curr_x, content_y + y_offset, child_box.w, "left"
            )
        else:
            layout_block_context(
                child_box, curr_x, content_y + y_offset, child_box.w, pos_cb=pos_cb
            )
            # Re-apply stretch if layout_block_context modified height
            if align_items == "stretch":
                decor = _get_decorations_h(child_box)
                mt = getattr(child_box, "margin_top", 0.0)
                mb = getattr(child_box, "margin_bottom", 0.0)
                margins = mt + mb
                child_box.h = max(0.0, line_h - decor - margins)

        curr_x += child_box.w + spacing

    return content_y + line_h
