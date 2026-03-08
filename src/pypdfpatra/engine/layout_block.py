"""
pypdfpatra.engine.layout_block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
W3C Block Formatting Context (BFC) implementation.

Lays out boxes vertically according to the CSS2.1 Section 9.4.1 specification.
Accepts a Box (part of the Render Tree) and calculates geometry.
"""

from __future__ import annotations
from pypdfpatra.engine.tree import (
    Box,
    BlockBox,
    InlineBox,
    TextBox,
    AnonymousBlockBox,
    InlineBlockBox,
)


def _parse_length(value: str, parent_value: float) -> float:
    """Parse a CSS length string (e.g. '10px', '50%') to a float (points)."""
    if not value:
        return 0.0
    value = value.strip().lower()
    if value == "auto":
        return 0.0
    try:
        if value.endswith("px"):
            return float(value[:-2])
        elif value.endswith("%"):
            return float(value[:-1]) / 100.0 * parent_value
        else:
            return float(value)
    except ValueError:
        return 0.0


def _resolve_box_geometry(box: Box, aw: float, style: dict) -> tuple[str, float]:
    """Resolves margin, padding, border, and width metrics."""
    # Parse spacing.
    margin_top = _parse_length(style.get("margin-top", "0px"), aw)
    margin_bottom = _parse_length(style.get("margin-bottom", "0px"), aw)
    
    margin_left_str = style.get("margin-left", "0px").strip().lower()
    margin_right_str = style.get("margin-right", "0px").strip().lower()
    margin_left = _parse_length(margin_left_str, aw)
    margin_right = _parse_length(margin_right_str, aw)
    
    padding_top = _parse_length(style.get("padding-top", "0px"), aw)
    padding_bottom = _parse_length(style.get("padding-bottom", "0px"), aw)
    padding_left = _parse_length(style.get("padding-left", "0px"), aw)
    padding_right = _parse_length(style.get("padding-right", "0px"), aw)

    border_top = _parse_length(style.get("border-top-width", "0px"), aw)
    border_bottom = _parse_length(style.get("border-bottom-width", "0px"), aw)
    border_left = _parse_length(style.get("border-left-width", "0px"), aw)
    border_right = _parse_length(style.get("border-right-width", "0px"), aw)

    if style.get("border-top-style", "none") in ("none", "hidden"):
        border_top = 0.0
    if style.get("border-bottom-style", "none") in ("none", "hidden"):
        border_bottom = 0.0
    if style.get("border-left-style", "none") in ("none", "hidden"):
        border_left = 0.0
    if style.get("border-right-style", "none") in ("none", "hidden"):
        border_right = 0.0

    box.border_top = border_top
    box.border_bottom = border_bottom
    box.border_left = border_left
    box.border_right = border_right

    # --- W3C Width Calculation ---
    box_sizing = style.get("box-sizing", "content-box").strip().lower()
    css_width_str = style.get("width", "auto").strip().lower()
    css_width = _parse_length(css_width_str, aw)

    if css_width_str != "auto":
        if box_sizing == "border-box":
            box.w = max(0.0, css_width - padding_left - padding_right - border_left - border_right)
        else:  # content-box
            box.w = css_width
            
        # W3C auto margin calculation for centering
        remaining_w = aw - (box.w + padding_left + padding_right + border_left + border_right)
        if remaining_w > 0:
            if margin_left_str == "auto" and margin_right_str == "auto":
                margin_left = remaining_w / 2.0
                margin_right = remaining_w / 2.0
            elif margin_left_str == "auto":
                margin_left = remaining_w - margin_right
            elif margin_right_str == "auto":
                margin_right = remaining_w - margin_left
    else:
        # width: auto
        box.w = max(0.0, aw - margin_left - margin_right - padding_left - padding_right - border_left - border_right)

    box.margin_top = margin_top
    box.margin_bottom = margin_bottom
    box.margin_left = margin_left
    box.margin_right = margin_right
    box.padding_top = padding_top
    box.padding_bottom = padding_bottom
    box.padding_left = padding_left
    box.padding_right = padding_right

    return box_sizing, css_width


def _wrap_inline_children(box: Box) -> None:
    """Pass 1: Wrap contiguous inline/text boxes into W3C anonymous block boxes"""
    new_children = []
    current_anonymous_block = None

    for child_box in box.children:
        if isinstance(child_box, (InlineBox, TextBox, InlineBlockBox)) or child_box.__class__.__name__ == "ImageBox":
            if current_anonymous_block is None:
                current_anonymous_block = AnonymousBlockBox(node=None)
                current_anonymous_block.margin_top = (
                    current_anonymous_block.margin_bottom
                ) = 0.0
                current_anonymous_block.margin_left = (
                    current_anonymous_block.margin_right
                ) = 0.0
                current_anonymous_block.padding_top = (
                    current_anonymous_block.padding_bottom
                ) = 0.0
                current_anonymous_block.padding_left = (
                    current_anonymous_block.padding_right
                ) = 0.0
                new_children.append(current_anonymous_block)
            current_anonymous_block.children.append(child_box)
        else:
            current_anonymous_block = None
            new_children.append(child_box)

    box.children = new_children


def _layout_block_children(box: Box, content_x: float, content_y: float) -> float:
    """Lays out all child boxes and returns the final content bottom Y."""
    current_border_box_bottom = content_y
    prev_margin_bottom = 0.0
    first_child = True

    for child_box in box.children:
        if isinstance(child_box, AnonymousBlockBox):
            # Establish Inline Formatting Context (IFC) for this block
            from pypdfpatra.engine.layout_inline import layout_inline_context

            child_box.x = content_x
            child_box.y = current_border_box_bottom
            child_box.w = box.w
            
            style = getattr(box.node, "style", {}) if box.node else {}
            text_align = style.get("text-align", "left").strip().lower()

            layout_inline_context(
                child_box, content_x, current_border_box_bottom, box.w, text_align
            )

            current_border_box_bottom = child_box.y + child_box.h
            prev_margin_bottom = 0.0
            first_child = False

        elif isinstance(child_box, BlockBox):
            # Prepare child margin_top for sibling margin collapsing
            child_style = (
                getattr(child_box.node, "style", {})
                if getattr(child_box, "node", None)
                else {}
            )
            child_mt = _parse_length(child_style.get("margin-top", "0px"), box.w)

            if first_child:
                collapsed_margin = child_mt
                first_child = False
            else:
                collapsed_margin = max(prev_margin_bottom, child_mt)

            child_margin_box_y = current_border_box_bottom + collapsed_margin - child_mt

            layout_block_context(child_box, content_x, child_margin_box_y, box.w)

            # Advance cursor past the child's entire border box (margin box edge + margin_top + padding + content_h)
            current_border_box_bottom = (
                child_box.y
                + child_box.margin_top
                + child_box.padding_top
                + child_box.h
                + child_box.padding_bottom
            )
            prev_margin_bottom = child_box.margin_bottom

        elif child_box.__class__.__name__ == "TableBox":
            from pypdfpatra.engine.layout_table import layout_table_context
            
            # Setup margins for margin collapsing
            child_style = getattr(child_box.node, "style", {}) if getattr(child_box, "node", None) else {}
            child_mt = _parse_length(child_style.get("margin-top", "0px"), box.w)
            
            if first_child:
                collapsed_margin = child_mt
                first_child = False
            else:
                collapsed_margin = max(prev_margin_bottom, child_mt)
                
            child_margin_box_y = current_border_box_bottom + collapsed_margin - child_mt
            
            layout_table_context(child_box, content_x, child_margin_box_y, box.w)
            
            current_border_box_bottom = (
                child_box.y
                + child_box.margin_top
                + child_box.padding_top
                + child_box.h
                + child_box.padding_bottom
            )
            prev_margin_bottom = child_box.margin_bottom

        elif child_box.__class__.__name__ == "MarkerBox":
            from pypdfpatra.engine.font_metrics import measure_text, get_line_height
            from pypdfpatra.engine.font_metrics import parse_font

            # Use the list-item's style for the marker
            style = getattr(box.node, "style", {}) if box.node else {}
            family, fpdf_style, size = parse_font(style)

            # Layout the marker, placed outside the principal box
            content = child_box.text_content
            if content in ("__disc__", "__circle__", "__square__"):
                marker_w = size * 0.4
                marker_h = size * 0.4
                y_offset = (size * 0.8) - marker_h  # Align visually with text baseline
            else:
                marker_w = measure_text(content, family, size, fpdf_style)
                marker_h = get_line_height(family, size, fpdf_style)
                y_offset = 0.0

            # Position to the left of content_x, vertically aligned with current Y
            child_box.x = content_x - marker_w - 5.0  # 5pt gap
            child_box.y = current_border_box_bottom + y_offset
            child_box.w = marker_w
            child_box.h = marker_h

            # Do NOT advance `current_border_box_bottom`, because the marker floats out of flow
            # relative to the first line of the principal block.

    return current_border_box_bottom


def layout_block_context(box: Box, cb_x: float, cb_y: float, cb_w: float) -> None:
    """
    Recursively calculates the CSS Box Model layout for a block element.
    Coordinates (`box.x`, `box.y`) refer to the MARGIN BOX top-left edge.
    Dimensions (`box.w`, `box.h`) refer to the CONTENT BOX.

    Args:
        box: The Box to layout.
        cb_x: Absolute X position of the containing block's content box.
        cb_y: Absolute Y position for the start of this block's margin box.
        cb_w: Available width (width of containing block's content box).
    """
    style = getattr(box.node, "style", {}) if box.node else {}

    box_sizing, css_width = _resolve_box_geometry(box, cb_w, style)

    # --- Absolute Positioning (Margin Box Origin) ---
    box.x = cb_x
    box.y = cb_y

    # --- Normal Flow Children Layout ---
    content_x = box.x + box.margin_left + box.border_left + box.padding_left
    current_border_box_bottom = (
        box.y + box.margin_top + box.border_top + box.padding_top
    )

    _wrap_inline_children(box)

    current_border_box_bottom = _layout_block_children(
        box, content_x, current_border_box_bottom
    )

    # --- W3C Height Calculation ---
    css_height = _parse_length(style.get("height", "auto"), cb_w)
    if css_height > 0:
        if box_sizing == "border-box":
            box.h = max(0.0, css_height - box.padding_top - box.padding_bottom)
        else:  # content-box
            box.h = css_height
    else:
        # height: auto -> Hugs the content
        content_bottom = current_border_box_bottom
        content_y = box.y + box.margin_top + box.padding_top
        box.h = max(0.0, content_bottom - content_y)

        if isinstance(box, TextBox) and box.h == 0:
            box.h = 20.0  # MVP line-height fallback
