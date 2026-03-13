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


def _get_outer_width(box: Box) -> float:
    """Returns the total horizontal space occupied by a box (margin-box width)."""
    return (
        getattr(box, "margin_left", 0.0)
        + getattr(box, "border_left", 0.0)
        + getattr(box, "padding_left", 0.0)
        + box.w
        + getattr(box, "padding_right", 0.0)
        + getattr(box, "border_right", 0.0)
        + getattr(box, "margin_right", 0.0)
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

    # Determine container's fixed content height
    container_fixed_h = 0.0
    style_h_str = str(style.get("height", "auto")).strip().lower()
    if style_h_str != "auto" and "px" in style_h_str:
        try:
            container_fixed_h = float(style_h_str.replace("px", ""))
        except (ValueError, TypeError):
            pass

    # Gather flow children and sort by 'order'
    flow_children = [
        c
        for c in box.children
        if getattr(c, "position", "static") not in ("absolute", "fixed")
    ]
    flow_children.sort(key=lambda c: int(getattr(c.node, "style", {}).get("order", 0)))

    if "reverse" in flex_direction:
        flow_children.reverse()

    is_row = "row" in flex_direction

    if is_row:
        return _layout_flex_row(
            flow_children,
            box,
            content_x,
            content_y,
            cb_w,
            container_fixed_h,
            style,
            pos_cb,
        )
    else:
        return _layout_flex_column(
            flow_children,
            box,
            content_x,
            content_y,
            cb_w,
            container_fixed_h,
            style,
            pos_cb,
        )


def _layout_flex_row(
    flow_children,
    box,
    content_x,
    content_y,
    cb_w,
    container_fixed_h,
    style,
    pos_cb,
):
    justify_content = style.get("justify-content", "flex-start").strip().lower()
    align_items = style.get("align-items", "stretch").strip().lower()
    align_content = style.get("align-content", "flex-start").strip().lower()
    flex_wrap = style.get("flex-wrap", "nowrap").strip().lower()

    lines = []
    current_line = []
    current_line_outer_w = 0.0

    # Step 1: Divide into lines
    for child_box in flow_children:
        child_style = getattr(child_box.node, "style", {})
        basis = child_style.get("flex-basis", "auto").strip().lower()

        if "px" in basis:
            child_box.w = float(basis.replace("px", ""))
        elif basis == "auto":
            style_w = child_style.get("width", "auto")
            if style_w == "auto":
                layout_block_context(child_box, 0, 0, cb_w, pos_cb=pos_cb)
                child_box.w = _get_intrinsic_width(child_box)
            else:
                layout_block_context(child_box, 0, 0, cb_w, pos_cb=pos_cb)
        else:
            child_box.w = 0.0

        outer_w = _get_outer_width(child_box)
        if (
            flex_wrap == "wrap"
            and current_line
            and current_line_outer_w + outer_w > cb_w
        ):
            lines.append(current_line)
            current_line = []
            current_line_outer_w = 0.0

        current_line.append(child_box)
        current_line_outer_w += outer_w
    if current_line:
        lines.append(current_line)

    # Step 2: Distribution
    total_lines_h = 0.0
    line_configs = []
    for line in lines:
        lw = sum(_get_outer_width(c) for c in line)
        rem = cb_w - lw
        if rem > 0:
            total_grow = sum(
                float(getattr(c.node, "style", {}).get("flex-grow", 0)) for c in line
            )
            if total_grow > 0:
                for c in line:
                    grow = float(getattr(c.node, "style", {}).get("flex-grow", 0))
                    if grow > 0:
                        c.w += (grow / total_grow) * rem
                lw = sum(_get_outer_width(c) for c in line)
        elif rem < 0:
            total_overflow = abs(rem)
            total_scaled_shrink = sum(
                float(getattr(c.node, "style", {}).get("flex-shrink", 1)) * c.w
                for c in line
            )
            if total_scaled_shrink > 0:
                for c in line:
                    shrink = float(getattr(c.node, "style", {}).get("flex-shrink", 1))
                    factor = (shrink * c.w) / total_scaled_shrink
                    c.w = max(0.0, c.w - (factor * total_overflow))
                lw = sum(_get_outer_width(c) for c in line)

        # Re-layout at final width
        for c in line:
            layout_block_context(c, 0, 0, cb_w, pos_cb=pos_cb, override_w=c.w)

        lh = max((_get_outer_height(c) for c in line), default=0.0)
        if len(lines) == 1 and container_fixed_h > lh:
            lh = container_fixed_h

        line_configs.append({"items": line, "lh": lh, "lw": lw})
        total_lines_h += lh

    # Step 3: Vertical line placement
    curr_y = content_y
    line_space = 0.0
    if container_fixed_h > total_lines_h:
        free_h = container_fixed_h - total_lines_h
        if align_content == "flex-end":
            curr_y += free_h
        elif align_content == "center":
            curr_y += free_h / 2
        elif align_content == "space-between" and len(line_configs) > 1:
            line_space = free_h / (len(line_configs) - 1)

    # Step 4: Final positioning
    from .inline import shift_box
    for config in line_configs:
        items, lh, lw = config["items"], config["lh"], config["lw"]
        curr_x = content_x
        item_space = 0.0
        rem_w = cb_w - lw
        if justify_content == "flex-end":
            curr_x += rem_w
        elif justify_content == "center":
            curr_x += rem_w / 2
        elif justify_content == "space-between" and len(items) > 1:
            item_space = rem_w / (len(items) - 1)

        for c in items:
            c_style = getattr(c.node, "style", {})
            c_align = c_style.get("align-self", "auto").strip().lower()
            if c_align == "auto":
                c_align = align_items

            # Settle height
            if c_align == "stretch":
                dec = _get_decorations_h(c)
                mt, mb = getattr(c, "margin_top", 0), getattr(c, "margin_bottom", 0)
                c.h = max(0.0, lh - dec - mt - mb)

            y_off = 0.0
            if c_align == "flex-end":
                y_off = lh - _get_outer_height(c)
            elif c_align == "center":
                y_off = (lh - _get_outer_height(c)) / 2

            # Global coordinate calculation
            ml = getattr(c, "margin_left", 0)
            bl = getattr(c, "border_left", 0)
            pl = getattr(c, "padding_left", 0)
            mt = getattr(c, "margin_top", 0)
            bt = getattr(c, "border_top", 0)
            pt = getattr(c, "padding_top", 0)

            target_x = curr_x + ml + bl + pl
            target_y = curr_y + y_off + mt + bt + pt

            shift_box(c, target_x - c.x, target_y - c.y)

            if c_align == "stretch":
                if isinstance(c, AnonymousBlockBox):
                    from .inline import layout_inline_context
                    layout_inline_context(c, c.x, c.y, c.w, "left")
                else:
                    layout_block_context(
                        c,
                        curr_x,
                        curr_y + y_off,
                        cb_w,
                        pos_cb=pos_cb,
                        override_w=c.w,
                        override_h=c.h,
                    )

            curr_x += _get_outer_width(c) + item_space
        curr_y += lh + line_space

    return curr_y


def _layout_flex_column(
    flow_children,
    box,
    content_x,
    content_y,
    cb_w,
    container_fixed_h,
    style,
    pos_cb,
):
    justify_content = style.get("justify-content", "flex-start").strip().lower()
    align_items = style.get("align-items", "stretch").strip().lower()

    # Pass 1: Measure
    curr_y = content_y
    for c in flow_children:
        layout_block_context(c, content_x, curr_y, cb_w, pos_cb=pos_cb)
        curr_y += _get_outer_height(c)

    total_h = curr_y - content_y
    if container_fixed_h > total_h:
        rem_h = container_fixed_h - total_h
        # Apply grow (simplified)
        total_grow = sum(
            float(getattr(c.node, "style", {}).get("flex-grow", 0))
            for c in flow_children
        )
        if total_grow > 0:
            for c in flow_children:
                grow = float(getattr(c.node, "style", {}).get("flex-grow", 0))
                if grow > 0:
                    c.h += (grow / total_grow) * rem_h
            total_h = container_fixed_h

        # Apply justify-content
        shift_y = 0.0
        if justify_content == "flex-end":
            shift_y = container_fixed_h - total_h
        elif justify_content == "center":
            shift_y = (container_fixed_h - total_h) / 2

        if shift_y > 0:
            from .inline import shift_box
            for c in flow_children:
                shift_box(c, 0, shift_y)

    # Alignment
    from .inline import shift_box
    for c in flow_children:
        c_style = getattr(c.node, "style", {})
        c_align = c_style.get("align-self", "auto").strip().lower()
        if c_align == "auto":
            c_align = align_items

        if c_align == "stretch":
            ml = getattr(c, "margin_left", 0)
            mr = getattr(c, "margin_right", 0)
            bl = getattr(c, "border_left", 0)
            br = getattr(c, "border_right", 0)
            pl = getattr(c, "padding_left", 0)
            pr = getattr(c, "padding_right", 0)
            c.w = cb_w - (ml + mr + bl + br + pl + pr)
            layout_block_context(
                c, content_x, c.y, cb_w, pos_cb=pos_cb, override_w=c.w, override_h=c.h
            )
        else:
            # Re-layout to ensure height is correct (if not already stretched)
            layout_block_context(
                c, content_x, c.y, cb_w, pos_cb=pos_cb, override_w=c.w, override_h=c.h
            )

            dx = 0.0
            if c_align == "flex-end":
                dx = cb_w - _get_outer_width(c)
            elif c_align == "center":
                dx = (cb_w - _get_outer_width(c)) / 2.0

            if dx > 0:
                shift_box(c, dx, 0)

    return content_y + max(total_h, container_fixed_h)
