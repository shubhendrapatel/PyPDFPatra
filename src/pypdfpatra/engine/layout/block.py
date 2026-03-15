"""
pypdfpatra.engine.layout.block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
W3C Block Formatting Context (BFC) implementation.

Lays out boxes vertically according to the CSS2.1 Section 9.4.1 specification.
Accepts a Box (part of the Render Tree) and calculates geometry.
"""

from __future__ import annotations

import math

from pypdfpatra.defaults import (
    DEFAULT_MARGIN_TOP,
    PAGE_HEIGHT,
)
from pypdfpatra.engine.layout.inline import shift_box
from pypdfpatra.engine.tree import (
    AnonymousBlockBox,
    BlockBox,
    Box,
    ImageBox,
    InlineBlockBox,
    InlineBox,
    TextBox,
)

from .common import PosCB

# Context for positioning relative ancestors


class FloatManager:
    def __init__(self):
        self.floats = []

    def add_float(self, box: Box):
        self.floats.append(box)

    def get_clearance_y(self, clear_mode: str) -> float:
        if clear_mode == "none":
            return 0.0
        max_y = 0.0
        for f in self.floats:
            # Calculate the bottom edge of the float's margin box
            val = (
                f.y
                + f.h
                + getattr(f, "padding_bottom", 0.0)
                + getattr(f, "border_bottom", 0.0)
                + getattr(f, "margin_bottom", 0.0)
            )
            if clear_mode == "both":
                max_y = max(max_y, val)
            elif clear_mode == "left" and f.float_mode == "left":
                max_y = max(max_y, val)
            elif clear_mode == "right" and f.float_mode == "right":
                max_y = max(max_y, val)
        return max_y

    def get_line_geometry(
        self, y: float, h: float, cb_x: float, cb_w: float
    ) -> tuple[float, float]:
        """Returns (line_x, line_w) avoiding all active floats at the given Y range."""
        line_left = cb_x
        line_right = cb_x + cb_w

        for f in self.floats:
            # f.x, f.y are Margin Box origins.
            # Calculate total margin box width and height.
            m_l = getattr(f, "margin_left", 0.0)
            b_l = getattr(f, "border_left", 0.0)
            p_l = getattr(f, "padding_left", 0.0)
            m_r = getattr(f, "margin_right", 0.0)
            b_r = getattr(f, "border_right", 0.0)
            p_r = getattr(f, "padding_right", 0.0)
            m_t = getattr(f, "margin_top", 0.0)
            b_t = getattr(f, "border_top", 0.0)
            p_t = getattr(f, "padding_top", 0.0)
            m_b = getattr(f, "margin_bottom", 0.0)
            b_b = getattr(f, "border_bottom", 0.0)
            p_b = getattr(f, "padding_bottom", 0.0)

            f_total_w = m_l + b_l + p_l + f.w + p_r + b_r + m_r
            f_total_h = m_t + b_t + p_t + f.h + p_b + b_b + m_b

            f_top = f.y
            f_bottom = f.y + f_total_h

            if not (f_bottom <= y or f_top >= y + h):
                if f.float_mode == "left":
                    # Right edge of the left float's margin box
                    f_right_edge = f.x + f_total_w
                    line_left = max(line_left, f_right_edge)
                elif f.float_mode == "right":
                    # Left edge of the right float's margin box
                    f_left_edge = f.x
                    line_right = min(line_right, f_left_edge)

        return line_left, max(0.0, line_right - line_left)


def _parse_length(
    value: str,
    parent_value: float,
    default_auto: float | None = 0.0,
    font_size: float = 12.0,
    root_font_size: float = 12.0,
) -> float | None:
    """Parse a CSS length string (e.g. '10px', '50%', '10pt') to a float (points)."""
    if not value:
        return default_auto
    value = value.strip().lower()
    if value == "auto":
        return default_auto
    try:
        if value.endswith("px"):
            return float(value[:-2])
        elif value.endswith("pt"):
            return float(value[:-2])
        elif value.endswith("in"):
            return float(value[:-2]) * 72.0
        elif value.endswith("cm"):
            return float(value[:-2]) * 72.0 / 2.54
        elif value.endswith("mm"):
            return float(value[:-2]) * 72.0 / 25.4
        elif value.endswith("em"):
            return float(value[:-2]) * font_size
        elif value.endswith("rem"):
            return float(value[:-3]) * root_font_size
        elif value.endswith("%"):
            return float(value[:-1]) / 100.0 * parent_value
        else:
            return float(value)
    except ValueError:
        return 0.0


def _resolve_box_geometry(
    box: Box,
    aw: float,
    style: dict,
    pos_cb: PosCB = None,
    root_font_size: float = 12.0,
) -> tuple[str, float]:
    """Resolves margin, padding, border, and width metrics."""
    # W3C: For fixed-position elements, ALL percentage-based lengths resolve
    # against the viewport (full page dimensions), not the parent's cb_w.
    if box.position == "fixed":
        from pypdfpatra.defaults import PAGE_WIDTH

        aw = PAGE_WIDTH

    # Resolve font-size for 'em' units
    fs_str = style.get("font-size", "12pt").strip().lower()
    font_size = 12.0
    if fs_str.endswith("pt"):
        try:
            font_size = float(fs_str[:-2])
        except ValueError:
            pass
    elif fs_str.endswith("px"):
        try:
            font_size = float(fs_str[:-2])
        except ValueError:
            pass

    # Parse spacing.
    margin_top = _parse_length(
        style.get("margin-top", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )
    margin_bottom = _parse_length(
        style.get("margin-bottom", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )

    margin_left_str = style.get("margin-left", "0px").strip().lower()
    margin_right_str = style.get("margin-right", "0px").strip().lower()

    margin_left = _parse_length(
        margin_left_str, aw, font_size=font_size, root_font_size=root_font_size
    )
    margin_right = _parse_length(
        margin_right_str, aw, font_size=font_size, root_font_size=root_font_size
    )

    padding_top = _parse_length(
        style.get("padding-top", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )
    padding_bottom = _parse_length(
        style.get("padding-bottom", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )
    padding_left = _parse_length(
        style.get("padding-left", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )
    padding_right = _parse_length(
        style.get("padding-right", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )

    border_top = _parse_length(
        style.get("border-top-width", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )
    border_bottom = _parse_length(
        style.get("border-bottom-width", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )
    border_left = _parse_length(
        style.get("border-left-width", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )
    border_right = _parse_length(
        style.get("border-right-width", "0px"),
        aw,
        font_size=font_size,
        root_font_size=root_font_size,
    )

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
    css_width = _parse_length(
        css_width_str,
        aw,
        default_auto=None,
        font_size=font_size,
        root_font_size=root_font_size,
    )

    if css_width is not None:
        if box_sizing == "border-box":
            box.w = max(
                0.0,
                css_width - padding_left - padding_right - border_left - border_right,
            )
        else:  # content-box
            box.w = css_width

        # W3C auto margin calculation for centering
        remaining_w = aw - (
            box.w + padding_left + padding_right + border_left + border_right
        )
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
        box.w = max(
            0.0,
            aw
            - margin_left
            - margin_right
            - padding_left
            - padding_right
            - border_left
            - border_right,
        )

    box.margin_top = margin_top
    box.margin_bottom = margin_bottom
    box.margin_left = margin_left
    box.margin_right = margin_right
    box.padding_top = padding_top
    box.padding_bottom = padding_bottom
    box.padding_left = padding_left
    box.padding_right = padding_right

    # Positioning (Phase 9)
    box.top = _parse_length(
        style.get("top", "nan"),
        aw,
        default_auto=float("nan"),
        root_font_size=root_font_size,
    )
    box.bottom = _parse_length(
        style.get("bottom", "nan"),
        aw,
        default_auto=float("nan"),
        root_font_size=root_font_size,
    )
    box.left = _parse_length(
        style.get("left", "nan"),
        aw,
        default_auto=float("nan"),
        root_font_size=root_font_size,
    )
    box.right = _parse_length(
        style.get("right", "nan"),
        aw,
        default_auto=float("nan"),
        root_font_size=root_font_size,
    )

    # --- W3C Absolute/Fixed Dimension Calculation (CSS2.1 10.3.7 & 10.6.4) ---
    if (box.position == "absolute" or box.position == "fixed") and pos_cb is not None:
        # Use viewport for fixed positioning stretching
        if box.position == "fixed":
            from pypdfpatra.defaults import PAGE_HEIGHT, PAGE_WIDTH

            pcb_w, pcb_h = PAGE_WIDTH, PAGE_HEIGHT
        else:
            pcb_w, pcb_h = pos_cb.w, pos_cb.h

        # Width calculation
        if math.isnan(box.w) or css_width_str == "auto":
            if not math.isnan(box.left) and not math.isnan(box.right):
                # Stretching width
                total_horizontal_box = pcb_w - box.left - box.right
                # Width is total minus horizontal padding/borders/margins
                extra_w = (
                    padding_left
                    + padding_right
                    + border_left
                    + border_right
                    + margin_left
                    + margin_right
                )
                box.w = max(0.0, total_horizontal_box - extra_w)

        # Height calculation (Preliminary based on offsets)
        if not math.isnan(box.top) and not math.isnan(box.bottom):
            total_vertical_box = pcb_h - box.top - box.bottom
            extra_h = (
                padding_top
                + padding_bottom
                + border_top
                + border_bottom
                + margin_top
                + margin_bottom
            )
            box.h = max(0.0, total_vertical_box - extra_h)

    return box_sizing, css_width, margin_top, margin_bottom


def _wrap_inline_children(box: Box) -> None:
    """Pass 1: Wrap contiguous inline/text boxes into W3C anonymous block boxes"""
    new_children = []
    current_anonymous_block = None

    for child_box in box.children:
        if isinstance(
            child_box, (InlineBox, TextBox, InlineBlockBox)
        ) or child_box.__class__.__name__ in ("ImageBox", "LineBox"):
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


def _layout_block_children(
    box: Box,
    content_x: float,
    content_y: float,
    pos_cb: PosCB = None,
    root_font_size: float = 12.0,
    current_page_name: str = "default",
    page_map: dict | None = None,
    page_rules: list | None = None,
    is_root: bool = False,
    float_manager: FloatManager | None = None,
) -> tuple[float, str]:
    style = getattr(box.node, "style", {}) if box.node else {}
    display = style.get("display", "block").strip().lower()

    if display == "flex":
        from .flex import layout_flex_context

        return layout_flex_context(
            box,
            content_x,
            content_y,
            box.w,
            pos_cb=pos_cb,
            root_font_size=root_font_size,
            current_page_name=current_page_name,
            page_rules=page_rules,
        ), current_page_name

    if float_manager is None:
        float_manager = FloatManager()

    from ..page import get_resolved_margins

    current_border_box_bottom = content_y
    if pos_cb and pos_cb.is_icb:
        idx_initial = int(current_border_box_bottom / PAGE_HEIGHT)
        mt_initial, _, _, _ = get_resolved_margins(
            page_rules, idx_initial, current_page_name
        )
        if current_border_box_bottom % PAGE_HEIGHT < mt_initial:
            current_border_box_bottom = (idx_initial * PAGE_HEIGHT) + mt_initial

    prev_margin_bottom = 0.0
    first_child = True

    # Use a running horizontal baseline that can change per page
    current_content_x = content_x
    current_cb_w = box.w
    from pypdfpatra.defaults import PAGE_WIDTH

    for child_box in box.children:
        # Phase 9: Remove absolute/fixed from flow
        if child_box.position in ("absolute", "fixed"):
            continue

        # Handle Clearance
        if child_box.clear_mode != "none":
            clear_y = float_manager.get_clearance_y(child_box.clear_mode)
            current_border_box_bottom = max(current_border_box_bottom, clear_y)

        # Pagination: Determine if the child box overflows the current page area.
        current_page_idx = int(current_border_box_bottom / PAGE_HEIGHT)
        mt, mb, ml, mr = get_resolved_margins(
            page_rules, current_page_idx, current_page_name
        )

        # If we are in the main document flow (ICB) AND at a page boundary,
        # update horizontal baselines to match the current page's margins.
        if pos_cb and pos_cb.is_icb:
            # Only update if we actually hit a page boundary or start
            if current_border_box_bottom % PAGE_HEIGHT < mt + 1.0:
                current_content_x = ml
                current_cb_w = PAGE_WIDTH - ml - mr

            # Vertical Snapping: Ensure content does not start above top margin.
            local_start_y = current_border_box_bottom % PAGE_HEIGHT
            if local_start_y < mt:
                # Snap to current page's top margin
                proposed_y = (current_page_idx * PAGE_HEIGHT) + mt
                current_border_box_bottom = max(current_border_box_bottom, proposed_y)

        page_boundary = (current_page_idx + 1) * PAGE_HEIGHT - mb

        if (
            isinstance(child_box, AnonymousBlockBox)
            or child_box.__class__.__name__ == "LineBox"
        ):
            # Establish Inline Formatting Context (IFC) for this block
            from .inline import layout_inline_context

            child_box.x = current_content_x
            child_box.y = current_border_box_bottom
            child_box.w = current_cb_w

            style = getattr(box.node, "style", {}) if box.node else {}
            text_align = style.get("text-align", "left").strip().lower()

            layout_inline_context(
                child_box,
                current_content_x,
                current_border_box_bottom,
                current_cb_w,
                text_align,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                float_manager=float_manager,
            )
            child_box.page_name = current_page_name

            current_border_box_bottom = child_box.y + child_box.h
            prev_margin_bottom = 0.0
            first_child = False

        elif (
            isinstance(child_box, (BlockBox, ImageBox))
            or child_box.__class__.__name__ == "TableBox"
        ):
            from .table import layout_table_context

            child_style = getattr(child_box.node, "style", {}) if child_box.node else {}
            # Support page-break-before: always or NAMED page transitions.
            # IMPORTANT: A child only changes the page context if it EXPLICITLY
            # declares a different 'page:' property. Without 'page:', the child
            # inherits the current page context and does NOT trigger a break.
            child_page_prop = child_style.get("page")
            if child_page_prop is not None:
                next_page_name = child_page_prop.strip().lower()
            else:
                next_page_name = current_page_name  # Inherit, don't reset

            force_break = child_style.get("page-break-before") == "always"
            if next_page_name != current_page_name:
                force_break = True
                current_page_name = next_page_name

            if force_break:
                target_page_idx = current_page_idx + 1
                next_mt, next_mb, next_ml, next_mr = get_resolved_margins(
                    page_rules, target_page_idx, current_page_name
                )
                current_border_box_bottom = target_page_idx * PAGE_HEIGHT + next_mt
                current_page_idx = target_page_idx
                page_boundary = (current_page_idx + 1) * PAGE_HEIGHT - next_mb

                # Update horizontal baselines for the new forced page
                if pos_cb and pos_cb.is_icb:
                    current_content_x = next_ml
                    current_cb_w = PAGE_WIDTH - next_ml - next_mr
                # Forced breaks reset margin collapsing
                prev_margin_bottom = 0.0
                first_child = True

            if page_map is not None:
                current_page_idx = int(current_border_box_bottom / PAGE_HEIGHT)
                page_map[current_page_idx] = current_page_name
            child_box.page_name = current_page_name

            # Phase 10: Clearance (CSS2.1 9.5.2)
            if child_box.clear_mode != "none":
                clear_y = float_manager.get_clearance_y(child_box.clear_mode)
                if clear_y > current_border_box_bottom:
                    current_border_box_bottom = clear_y

            child_mt = _parse_length(
                child_style.get("margin-top", "0px"),
                current_cb_w,
                root_font_size=root_font_size,
            )
            # ... existing margin collapse logic ...
            if first_child:
                collapsed_margin = child_mt
            else:
                collapsed_margin = max(prev_margin_bottom, child_mt)

            child_margin_box_y = current_border_box_bottom + collapsed_margin - child_mt

            is_atomic = (
                child_box.__class__.__name__ in ("ImageBox", "TableBox")
                or child_style.get("page-break-inside") == "avoid"
            )

            if is_atomic:
                _, predicted_w, _, _ = _resolve_box_geometry(
                    child_box, current_cb_w, child_style, root_font_size=root_font_size
                )
                css_h = _parse_length(
                    child_style.get("height", "auto"),
                    current_cb_w,
                    default_auto=None,
                    root_font_size=root_font_size,
                )
                predicted_h = css_h if css_h is not None else 0.0
                total_h = (
                    predicted_h
                    + child_box.padding_top
                    + child_box.padding_bottom
                    + child_box.border_top
                    + child_box.border_bottom
                )

                if (
                    child_margin_box_y + total_h > page_boundary
                    and child_margin_box_y % PAGE_HEIGHT > mt + 5
                ):
                    target_page_idx = current_page_idx + 1
                    next_mt, _, next_ml, next_mr = get_resolved_margins(
                        page_rules, target_page_idx, current_page_name
                    )
                    current_border_box_bottom = target_page_idx * PAGE_HEIGHT + next_mt

                    if pos_cb and pos_cb.is_icb:
                        current_content_x = next_ml
                        current_cb_w = PAGE_WIDTH - next_ml - next_mr

                    child_margin_box_y = (
                        current_border_box_bottom + collapsed_margin - child_mt
                    )
            else:
                # Predictive break for normal blocks: only if they have content
                has_content = child_box.children or getattr(
                    child_box.node, "pseudos", {}
                )
                if has_content and child_margin_box_y + 15 > page_boundary:
                    target_page_idx = current_page_idx + 1
                    next_mt, _, next_ml, next_mr = get_resolved_margins(
                        page_rules, target_page_idx, current_page_name
                    )
                    current_border_box_bottom = target_page_idx * PAGE_HEIGHT + next_mt

                    if pos_cb and pos_cb.is_icb:
                        current_content_x = next_ml
                        current_cb_w = PAGE_WIDTH - next_ml - next_mr

                    child_margin_box_y = (
                        current_border_box_bottom + collapsed_margin - child_mt
                    )

            if child_box.__class__.__name__ == "TableBox":
                layout_table_context(
                    child_box,
                    current_content_x,
                    child_margin_box_y,
                    current_cb_w,
                    root_font_size=root_font_size,
                    current_page_name=current_page_name,
                    page_rules=page_rules,
                    pos_cb=pos_cb,
                )
            elif child_box.__class__.__name__ == "ImageBox":
                _resolve_box_geometry(
                    child_box, current_cb_w, child_style, root_font_size=root_font_size
                )
                child_box.x = current_content_x
                child_box.y = child_margin_box_y
                child_box.h = child_box.image_h * (child_box.w / child_box.image_w)
            else:
                # If it's a float, pre-calculate its width to determine target x
                target_x = current_content_x
                if child_box.float_mode != "none":
                    _resolve_box_geometry(
                        child_box,
                        current_cb_w,
                        child_style,
                        root_font_size=root_font_size,
                    )
                    total_w = (
                        child_box.margin_left
                        + child_box.border_left
                        + child_box.padding_left
                        + child_box.w
                        + child_box.padding_right
                        + child_box.border_right
                        + child_box.margin_right
                    )
                    if child_box.float_mode == "left":
                        target_x = current_content_x
                    else:  # right
                        target_x = current_content_x + current_cb_w - total_w
                else:
                    target_x = current_content_x

                _, current_page_name = layout_block_context(
                    child_box,
                    target_x,
                    child_margin_box_y,
                    current_cb_w,
                    pos_cb=pos_cb,
                    root_font_size=root_font_size,
                    current_page_name=current_page_name,
                    page_map=page_map,
                    page_rules=page_rules,
                    is_root=False,
                    float_manager=FloatManager()
                    if child_box.float_mode != "none"
                    else float_manager,
                )

            # If the child was a float, add it to manager (don't advance flow)
            if child_box.float_mode != "none":
                float_manager.add_float(child_box)
            else:
                current_border_box_bottom = (
                    child_box.y
                    + child_box.margin_top
                    + child_box.padding_top
                    + child_box.h
                    + child_box.padding_bottom
                )
                prev_margin_bottom = child_box.margin_bottom
                first_child = False  # Ensure subsequent children aren't first_child

            # Phase 11: Support page-break-after: always
            if child_style.get("page-break-after") == "always":
                page_idx_after = int(current_border_box_bottom / PAGE_HEIGHT)
                target_page_idx = page_idx_after + 1
                next_mt, _, next_ml, next_mr = get_resolved_margins(
                    page_rules, target_page_idx, current_page_name
                )
                current_border_box_bottom = target_page_idx * PAGE_HEIGHT + next_mt
                if pos_cb and pos_cb.is_icb:
                    current_content_x = next_ml
                    current_cb_w = PAGE_WIDTH - next_ml - next_mr

        elif child_box.__class__.__name__ == "MarkerBox":
            from pypdfpatra.engine.font_metrics import (
                get_line_height,
                measure_text,
                parse_font,
            )

            style = getattr(box.node, "style", {}) if box.node else {}
            family, fpdf_style, size = parse_font(style)

            content = child_box.text_content
            if content in ("__disc__", "__circle__", "__square__"):
                marker_w = size * 0.4
                marker_h = size * 0.4
                y_offset = (size * 0.8) - marker_h
            else:
                marker_w = measure_text(content, family, size, fpdf_style)
                marker_h = get_line_height(family, size, fpdf_style)
                y_offset = 0.0

            child_box.x = current_content_x - marker_w - 5.0
            child_box.y = current_border_box_bottom + y_offset
            child_box.w = marker_w
            child_box.h = marker_h

    return current_border_box_bottom, current_page_name


def layout_block_context(
    box: Box,
    cb_x: float,
    cb_y: float,
    cb_w: float,
    pos_cb: PosCB = None,
    override_w: float | None = None,
    override_h: float | None = None,
    root_font_size: float = 12.0,
    current_page_name: str = "default",
    page_map: dict | None = None,
    page_rules: list | None = None,
    is_root: bool = False,
    float_manager: FloatManager | None = None,
) -> tuple[float, str]:
    """
    Recursively calculates the CSS Box Model layout for a block element.
    """
    if is_root:
        from ..page import resolve_page_style

        rule = resolve_page_style(page_rules, 0, current_page_name)

        def _p(k, d):
            return float(
                str(rule.style.get(k, str(d)))
                .replace("pt", "")
                .replace("px", "")
                .replace("in", "")
            )

        mt_root = _p("margin-top", DEFAULT_MARGIN_TOP)
        cb_y = max(cb_y, mt_root)
    if pos_cb is None:
        # Default to initial containing block (the page)
        # Using A4 default dimensions 519.0 (CONTENT_WIDTH)
        # But for positioning it's usually the full page area or the first page.
        from pypdfpatra.defaults import PAGE_WIDTH

        pos_cb = PosCB(0.0, 0.0, PAGE_WIDTH, PAGE_HEIGHT, is_icb=True)

    style = getattr(box.node, "style", {}) if box.node else {}
    box_sizing, css_width, mt, mb = _resolve_box_geometry(
        box, cb_w, style, pos_cb=pos_cb, root_font_size=root_font_size
    )
    box.page_name = current_page_name

    if override_w is not None:
        box.w = override_w

    css_height = _parse_length(
        style.get("height", "auto"),
        cb_w,
        default_auto=None,
        root_font_size=root_font_size,
    )
    if override_h is not None:
        css_height = override_h

    if css_height is not None:
        total_h = css_height
        if box_sizing == "content-box":
            total_h += (
                box.padding_top
                + box.padding_bottom
                + box.border_top
                + box.border_bottom
            )

        current_page_idx = int(cb_y / PAGE_HEIGHT)

        # Update page_map if needed
        if page_map is not None:
            page_map[current_page_idx] = current_page_name

        from ..page import get_resolved_margins

        mt_curr, mb_curr, _, _ = get_resolved_margins(
            page_rules, current_page_idx, current_page_name
        )
        page_boundary = (current_page_idx + 1) * PAGE_HEIGHT - mb_curr

        if cb_y + total_h > page_boundary and cb_y % PAGE_HEIGHT > mt_curr + 5:
            target_page_idx = current_page_idx + 1
            mt_next, _, _, _ = get_resolved_margins(
                page_rules, target_page_idx, current_page_name
            )
            cb_y = target_page_idx * PAGE_HEIGHT + mt_next

    box.x = cb_x
    box.y = cb_y

    content_x = box.x + box.margin_left + box.border_left + box.padding_left
    current_border_box_bottom = (
        box.y + box.margin_top + box.border_top + box.padding_top
    )

    # Determine the containing block for absolute children
    padding_x = box.x + box.margin_left + box.border_left
    padding_y = box.y + box.margin_top + box.border_top
    padding_w = box.w + box.padding_left + box.padding_right
    # padding_h is yet to be determined if height is auto

    # BFC check: Does this box exit the Initial Containing Block (ICB) flow?
    # Floats, inline-blocks, flex items, table cells, and positioned elements
    # establish new contexts that should not snap to page margins.
    is_bfc = (
        box.position != "static"
        or box.float_mode != "none"
        or style.get("display", "block").strip().lower()
        in ("inline-block", "table-cell", "flex")
    )

    if is_bfc:
        # This box establishes a new containing block / formatting context
        child_pos_cb = PosCB(padding_x, padding_y, padding_w, 0.0, is_icb=False)
    else:
        child_pos_cb = pos_cb

    _wrap_inline_children(box)

    current_border_box_bottom, current_page_name = _layout_block_children(
        box,
        content_x,
        current_border_box_bottom,
        pos_cb=child_pos_cb,
        root_font_size=root_font_size,
        current_page_name=current_page_name,
        page_map=page_map,
        page_rules=page_rules,
        is_root=is_root,
        float_manager=float_manager,
    )

    if css_height is not None:
        if box_sizing == "border-box":
            box.h = max(
                0.0,
                css_height
                - box.padding_top
                - box.padding_bottom
                - box.border_top
                - box.border_bottom,
            )
        else:
            box.h = css_height
    elif (
        box.position == "absolute"
        and not math.isnan(box.top)
        and not math.isnan(box.bottom)
    ):
        # Height was already set in _resolve_box_geometry based on offsets
        pass
    else:
        content_bottom = current_border_box_bottom
        content_y = box.y + box.margin_top + box.border_top + box.padding_top
        box.h = max(0.0, content_bottom - content_y)

        if isinstance(box, TextBox) and box.h == 0:
            box.h = 20.0

    # Final padding height is now known
    padding_h = box.h + box.padding_top + box.padding_bottom

    # Update the child_pos_cb with the resolved height if this box is positioned
    if box.position != "static":
        final_pos_cb = PosCB(padding_x, padding_y, padding_w, padding_h)
    else:
        final_pos_cb = pos_cb

    # Phase 9: Relative Positioning Offset (Visual shift only)
    if box.position == "relative":
        from .inline import shift_box

        dx = 0.0
        dy = 0.0
        if not math.isnan(box.left):
            dx = box.left
        elif not math.isnan(box.right):
            dx = -box.right

        if not math.isnan(box.top):
            dy = box.top
        elif not math.isnan(box.bottom):
            dy = -box.bottom

        if dx != 0 or dy != 0:
            shift_box(box, dx, dy)

    # Phase 9: Absolute Positioning (Simplified: Relative to Container/Page)
    # W3C: Absolute containing block is the PADDING box of the nearest
    # positioned ancestor.
    _layout_positioned_children(
        box,
        final_pos_cb,
        root_font_size=root_font_size,
        current_page_name=current_page_name,
        page_rules=page_rules,
    )

    return current_border_box_bottom, current_page_name


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


def _layout_positioned_children(
    box: Box,
    pos_cb: PosCB,
    root_font_size: float = 12.0,
    current_page_name: str = "default",
    page_rules: list | None = None,
):
    """Lays out absolute/fixed boxes that belong to this containing block context."""
    for child_box in box.children:
        if child_box.position not in ("absolute", "fixed"):
            continue

        child_style = getattr(child_box.node, "style", {}) if child_box.node else {}
        _resolve_box_geometry(
            child_box,
            pos_cb.w,
            child_style,
            pos_cb=pos_cb,
            root_font_size=root_font_size,
        )

        import math

        # Simplified Absolute positioning:
        # If position is absolute, coordinates are relative to the
        # containing block (this box).
        # In this implementation, we apply it relative to the
        # container's top-left.

        if child_box.position == "fixed":
            from pypdfpatra.defaults import PAGE_WIDTH

            # Fixed is relative to page (standard viewport)
            ref_x = 0.0
            ref_y = int(box.y / PAGE_HEIGHT) * PAGE_HEIGHT
            ref_w = PAGE_WIDTH
            ref_h = PAGE_HEIGHT
        else:
            ref_x, ref_y, ref_w, ref_h = pos_cb.x, pos_cb.y, pos_cb.w, pos_cb.h

        # Update pos_cb for absolute/fixed layout context to prevent root width reset
        cb_for_child = PosCB(ref_x, ref_y, ref_w, ref_h)

        init_x = ref_x
        init_y = ref_y

        # Handle X (initial guessed X)
        if not math.isnan(child_box.left):
            init_x = ref_x + child_box.left
        elif not math.isnan(child_box.right):
            # Account for full margin-box width
            init_x = ref_x + ref_w - _get_outer_width(child_box) - child_box.right
        else:
            init_x = ref_x

        # Handle Y (initial guessed Y)
        if not math.isnan(child_box.top):
            init_y = ref_y + child_box.top
        elif not math.isnan(child_box.bottom):
            # Account for full margin-box height
            init_y = ref_y + ref_h - _get_outer_height(child_box) - child_box.bottom
        else:
            init_y = ref_y

        if child_box.__class__.__name__ == "TableBox":
            from .table import layout_table_context

            layout_table_context(
                child_box,
                init_x,
                init_y,
                child_box.w,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                pos_cb=cb_for_child,
            )
        elif child_box.__class__.__name__ == "ImageBox":
            child_box.x = init_x
            child_box.y = init_y
            child_box.h = child_box.image_h * (child_box.w / child_box.image_w)
        else:
            layout_block_context(
                child_box,
                init_x,
                init_y,
                child_box.w,
                pos_cb=cb_for_child,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                is_root=False,  # Fixed/absolute nested children are not document root
            )

        # Post-layout adjustment for right/bottom
        dx = 0.0
        dy = 0.0
        if not math.isnan(child_box.right) and math.isnan(child_box.left):
            # Re-calculate correct X now that width is definitely known
            target_x = ref_x + ref_w - _get_outer_width(child_box) - child_box.right
            dx = target_x - child_box.x

        if not math.isnan(child_box.bottom) and math.isnan(child_box.top):
            # Re-calculate correct Y now that height is definitely known
            target_y = ref_y + ref_h - _get_outer_height(child_box) - child_box.bottom
            dy = target_y - child_box.y

        if dx != 0 or dy != 0:
            shift_box(child_box, dx, dy)
