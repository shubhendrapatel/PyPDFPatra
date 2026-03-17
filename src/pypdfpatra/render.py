"""
pypdfpatra.render
~~~~~~~~~~~~~~~~
The rendering orchestrator that traverses the Cython layout tree and issues
drawing commands to a lightweight PDF backend (fpdf2).
"""

import fpdf

from pypdfpatra.colors import parse_color
from pypdfpatra.defaults import DEFAULT_COLOR, DEFAULT_FONT_FAMILY, PAGE_HEIGHT
from pypdfpatra.engine.font_metrics import parse_font
from pypdfpatra.engine.page import PageRule, resolve_page_style
from pypdfpatra.engine.tree import Box, TextBox


def _apply_transform(transform_matrix: list | None) -> tuple[float, float]:
    """
    Extracts translation components from a transformation matrix.
    Other effects (scale, rotate, skew) are currently ignored by the renderer.

    Args:
        transform_matrix: [a, b, c, d, e, f] or None

    Returns:
        A tuple of (tx, ty) representing the points to shift in X and Y.
    """
    if not transform_matrix:
        return 0.0, 0.0

    # In PDF matrix [a, b, c, d, e, f], e and f are the translation components.
    # While we don't fully support rotation/scale yet, extracting e/f allows
    # simple translate() to work perfectly.
    tx = transform_matrix[4]
    ty = transform_matrix[5]

    return tx, ty


def collect_fixed_boxes(boxes: list[Box]) -> list[Box]:
    """Recursively collects all boxes with position='fixed'."""
    fixed = []
    for box in boxes:
        if box is None:
            continue
        if getattr(box, "position", "static") == "fixed":
            fixed.append(box)
        if hasattr(box, "children") and box.children:
            fixed.extend(collect_fixed_boxes(box.children))
    return fixed


def register_anchors(
    pdf: fpdf.FPDF,
    boxes: list[Box],
    dy: float = 0.0,
    page_rules: list = None,
    page_names: dict = None,
) -> dict:
    """
    Traverses the box tree to find elements with 'id' attributes and
    registers them as PDF destinations (internal links).
    """
    anchor_map = {}

    def _collect(box_list, curr_dy):
        for box in box_list:
            if box is None:
                continue

            node_id = getattr(box.node, "props", {}).get("id")
            if node_id and node_id not in anchor_map:
                # Calculate the exact Y position on the page
                border_box_y = (box.y + curr_dy) + box.margin_top
                page_idx = int(border_box_y / PAGE_HEIGHT)
                local_y = border_box_y - (page_idx * PAGE_HEIGHT)

                # Ensure the target page exists
                _ensure_page(
                    pdf, page_idx, page_rules=page_rules, page_names=page_names
                )

                # Create link destination
                link_id = pdf.add_link()
                pdf.set_link(link_id, y=local_y, page=page_idx + 1)
                anchor_map[node_id] = (link_id, page_idx)

            if hasattr(box, "children") and box.children:
                _collect(box.children, curr_dy)

    _collect(boxes, dy)
    return anchor_map


def _ensure_page(
    pdf: fpdf.FPDF,
    page_idx: int,
    page_rules: list = None,
    page_names: dict = None,
):
    """Ensures the PDF has enough pages and resets state cache for new pages."""
    target_page = page_idx + 1
    if len(pdf.pages) < target_page:
        while len(pdf.pages) < target_page:
            pdf.add_page()
            # Draw page decorations (background/border) for the newly created page
            new_page_idx = len(pdf.pages) - 1
            _draw_page_decorations(pdf, new_page_idx, page_rules, page_names)

    if pdf.page != target_page:
        pdf.page = target_page
        # FPDF 2 caches font/color per page-insertion but often misses manual
        # page switching. Invalidate internal trackers to force re-emission.
        pdf.font_family = None
        pdf.draw_color = None
        pdf.fill_color = None
        pdf.text_color = None
        pdf.line_width = -1.0


def _draw_page_decorations(
    pdf: fpdf.FPDF,
    page_idx: int,
    page_rules: list = None,
    page_names: dict = None,
) -> None:
    """Draws background and borders for the page box/area."""
    if not page_rules:
        return

    from pypdfpatra.defaults import PAGE_HEIGHT, PAGE_WIDTH
    from pypdfpatra.engine.page import get_resolved_margins, resolve_page_style
    from pypdfpatra.engine.styling.utils import parse_length

    page_name = "default"
    if page_names and page_idx in page_names:
        page_name = page_names[page_idx]

    page_style = resolve_page_style(page_rules, page_idx, page_name)
    style = page_style.style

    # 1. Page Background (covers whole sheet)
    bg_color = style.get("background-color")
    if bg_color and bg_color != "transparent":
        rgb = parse_color(bg_color)
        if rgb:
            pdf.set_fill_color(*rgb)
            pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, style="F")

    # 2. Page Area Border (inside margins)
    mt, mb, ml, mr = get_resolved_margins(page_rules, page_idx, page_name)

    border_top_w = parse_length(
        style.get("border-top-width", style.get("border-width", "0"))
    )
    border_bottom_w = parse_length(
        style.get("border-bottom-width", style.get("border-width", "0"))
    )
    border_left_w = parse_length(
        style.get("border-left-width", style.get("border-width", "0"))
    )
    border_right_w = parse_length(
        style.get("border-right-width", style.get("border-width", "0"))
    )

    if any(
        w > 0 for w in (border_top_w, border_bottom_w, border_left_w, border_right_w)
    ):
        border_box_x = ml
        border_box_y = mt
        border_box_w = PAGE_WIDTH - ml - mr
        border_box_h = PAGE_HEIGHT - mt - mb

        # Temporarily suppress page jump to avoid recursion and allow drawing on
        # the page we are currently decorating.
        orig_suppress = getattr(pdf, "_suppress_page_jump", False)
        pdf._suppress_page_jump = True

        _draw_borders(
            pdf,
            style,
            border_top_w,
            border_bottom_w,
            border_left_w,
            border_right_w,
            border_box_x,
            page_idx * PAGE_HEIGHT + border_box_y,
            border_box_w,
            border_box_h,
            page_rules=None,
            page_names=None,
            skip_clipping=True,
        )
        pdf._suppress_page_jump = orig_suppress


def _get_page_margins(pdf, page_idx, page_rules, page_names):
    from pypdfpatra.engine.page import get_resolved_margins

    page_name = "default"
    if page_names and page_idx in page_names:
        page_name = page_names[page_idx]

    return get_resolved_margins(page_rules, page_idx, page_name)


def _draw_background(
    pdf: fpdf.FPDF,
    style: dict,
    border_box_x: float,
    border_box_y: float,
    border_box_w: float,
    border_box_h: float,
    page_rules: list = None,
    page_names: dict = None,
    skip_clipping: bool = False,
) -> None:
    """Paints background colors across potentially multiple pages."""
    if style.get("visibility") == "hidden":
        return
    bg_color_str = style.get("background-color")
    if bg_color_str and bg_color_str != "transparent":
        rgb = parse_color(bg_color_str)
        if rgb is None:
            return
        r, g, b = rgb
        if r is None:
            return

        start_page = int(border_box_y / PAGE_HEIGHT)
        end_page = int((border_box_y + border_box_h) / PAGE_HEIGHT)

        for p in range(start_page, end_page + 1):
            if not getattr(pdf, "_suppress_page_jump", False):
                _ensure_page(pdf, p)
            pdf.set_fill_color(r, g, b)

            mt, mb, ml, mr = _get_page_margins(pdf, p, page_rules, page_names)

            # Local coordinates for this specific page fragment
            local_y = border_box_y - (p * PAGE_HEIGHT)
            local_h = border_box_h

            # Clip against page boundaries (top/bottom margins)
            if not skip_clipping:
                if local_y < mt:
                    local_h -= mt - local_y
                    local_y = mt

                if local_y + local_h > PAGE_HEIGHT - mb:
                    local_h = (PAGE_HEIGHT - mb) - local_y

            if local_h > 0:
                pdf.rect(
                    x=border_box_x, y=local_y, w=border_box_w, h=local_h, style="F"
                )

        pdf.set_fill_color(0, 0, 0)


def _draw_borders(
    pdf: fpdf.FPDF,
    style: dict,
    border_top: float,
    border_bottom: float,
    border_left: float,
    border_right: float,
    border_box_x: float,
    border_box_y: float,
    border_box_w: float,
    border_box_h: float,
    page_rules: list = None,
    page_names: dict = None,
    skip_clipping: bool = False,
) -> None:
    """Paints element borders with correct styles: solid, dashed, dotted, double."""
    if style.get("visibility") == "hidden":
        return
    # Use butt caps (0 J) to ensure borders meet precisely at corners.
    pdf._out("0 J")

    def half(w):
        return w / 2.0

    # Draw order: Top, Bottom, Left, Right
    edges = [
        (
            "top",
            border_top,
            border_box_x,
            border_box_y + half(border_top),
            border_box_x + border_box_w,
            border_box_y + half(border_top),
        ),
        (
            "bottom",
            border_bottom,
            border_box_x,
            border_box_y + border_box_h - half(border_bottom),
            border_box_x + border_box_w,
            border_box_y + border_box_h - half(border_bottom),
        ),
        (
            "left",
            border_left,
            border_box_x + half(border_left),
            border_box_y + border_top,
            border_box_x + half(border_left),
            border_box_y + border_box_h - border_bottom,
        ),
        (
            "right",
            border_right,
            border_box_x + border_box_w - half(border_right),
            border_box_y + border_top,
            border_box_x + border_box_w - half(border_right),
            border_box_y + border_box_h - border_bottom,
        ),
    ]

    for edge, b_w, line_x1, line_y1, line_x2, line_y2 in edges:
        border_style = style.get(
            f"border-{edge}-style", style.get("border-style", "solid")
        )
        if b_w <= 0 or border_style in ("none", "hidden"):
            continue

        color_str = style.get(
            f"border-{edge}-color", style.get("border-color", DEFAULT_COLOR)
        )
        rgb = parse_color(color_str)
        if rgb is None:
            continue
        r, g, b = rgb

        start_page = int(line_y1 / PAGE_HEIGHT)
        end_page = int(line_y2 / PAGE_HEIGHT)

        for p in range(start_page, end_page + 1):
            if not getattr(pdf, "_suppress_page_jump", False):
                _ensure_page(pdf, p, page_rules=page_rules, page_names=page_names)
            pdf.set_draw_color(r, g, b)
            pdf.set_line_width(b_w)

            # Line coordinates relative to this page
            p_y1 = line_y1 - (p * PAGE_HEIGHT)
            p_y2 = line_y2 - (p * PAGE_HEIGHT)

            # Clipping vertical fragments
            if not skip_clipping:
                mt, mb, ml, mr = _get_page_margins(pdf, p, page_rules, page_names)

                if p_y1 < mt:
                    p_y1 = mt
                if p_y2 < mt:
                    p_y2 = mt
                if p_y1 > PAGE_HEIGHT - mb:
                    p_y1 = PAGE_HEIGHT - mb
                if p_y2 > PAGE_HEIGHT - mb:
                    p_y2 = PAGE_HEIGHT - mb
            else:
                # Still need mt/mb if we want to call it, but let's just skip
                pass

            if p_y1 == p_y2 and edge in ("left", "right"):
                continue  # Whole fragment clipped out

            # Only draw horizontal borders on their respective first/last pages
            if edge == "top" and p != start_page:
                continue
            if edge == "bottom" and p != end_page:
                continue

            def _draw_line(x1, y1, x2, y2, color_rgb=None, width=None):
                if color_rgb:
                    pdf.set_draw_color(*color_rgb)
                if width is not None:
                    pdf.set_line_width(width)
                pdf.line(x1, y1, x2, y2)

            def _get_shades(base_rgb):
                def clamp(c):
                    return max(0, min(255, int(c)))

                r, g, b = base_rgb
                light = (clamp(r + 50), clamp(g + 50), clamp(b + 50))
                dark = (clamp(r - 50), clamp(g - 50), clamp(b - 50))
                return light, dark

            light, dark = _get_shades((r, g, b))

            if border_style == "dashed":
                pdf.set_dash_pattern(dash=b_w * 3, gap=b_w * 2)
                _draw_line(line_x1, p_y1, line_x2, p_y2)
                pdf.set_dash_pattern()
            elif border_style == "dotted":
                pdf.set_dash_pattern(dash=b_w, gap=b_w)
                _draw_line(line_x1, p_y1, line_x2, p_y2)
                pdf.set_dash_pattern()
            elif border_style == "double":
                third = b_w / 3.0
                offset = third
                if edge == "top":
                    _draw_line(
                        line_x1, p_y1 - offset, line_x2, p_y2 - offset, width=third
                    )
                    _draw_line(
                        line_x1, p_y1 + offset, line_x2, p_y2 + offset, width=third
                    )
                elif edge == "bottom":
                    _draw_line(
                        line_x1, p_y1 - offset, line_x2, p_y2 - offset, width=third
                    )
                    _draw_line(
                        line_x1, p_y1 + offset, line_x2, p_y1 + offset, width=third
                    )
                elif edge == "left":
                    _draw_line(
                        line_x1 - offset, p_y1, line_x2 - offset, p_y2, width=third
                    )
                    _draw_line(
                        line_x1 + offset, p_y1, line_x2 + offset, p_y2, width=third
                    )
                elif edge == "right":
                    _draw_line(
                        line_x1 - offset, p_y1, line_x2 - offset, p_y2, width=third
                    )
                    _draw_line(
                        line_x1 + offset, p_y1, line_x2 + offset, p_y2, width=third
                    )
            elif border_style in ("ridge", "groove"):
                half_w = b_w / 2.0
                off = half_w / 2.0
                is_ridge = border_style == "ridge"
                c1 = light if is_ridge else dark
                c2 = dark if is_ridge else light
                if edge in ("top", "left"):
                    pass
                else:
                    c1, c2 = c2, c1

                if edge in ("top", "bottom"):
                    _draw_line(
                        line_x1,
                        p_y1 - off,
                        line_x2,
                        p_y2 - off,
                        color_rgb=c1,
                        width=half_w,
                    )
                    _draw_line(
                        line_x1,
                        p_y1 + off,
                        line_x2,
                        p_y2 + off,
                        color_rgb=c2,
                        width=half_w,
                    )
                else:
                    _draw_line(
                        line_x1 - off,
                        p_y1,
                        line_x2 - off,
                        p_y2,
                        color_rgb=c1,
                        width=half_w,
                    )
                    _draw_line(
                        line_x1 + off,
                        p_y1,
                        line_x2 + off,
                        p_y2,
                        color_rgb=c2,
                        width=half_w,
                    )
            elif border_style in ("inset", "outset"):
                is_inset = border_style == "inset"
                shade = (
                    dark
                    if (is_inset and edge in ("top", "left"))
                    or (not is_inset and edge in ("bottom", "right"))
                    else light
                )
                _draw_line(line_x1, p_y1, line_x2, p_y2, color_rgb=shade)
            else:
                _draw_line(line_x1, p_y1, line_x2, p_y2)

    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)
    pdf._out("2 J")


def _draw_inline_backgrounds(
    pdf: fpdf.FPDF,
    box: Box,
    style: dict,
    dy: float = 0.0,
    page_rules: list = None,
    page_names: dict = None,
) -> None:
    """
    Draws background colors for inline elements.

    During layout, InlineBox objects have their background regions pre-calculated
    and stored in _inline_bg_regions. However, in the render tree, these boxes
    are flattened to TextBox objects. We use node.props["_inline_parent_box"]
    to find the original InlineBox and draw its backgrounds.
    """
    # Only process TextBox objects to find their inline parents
    if box.__class__.__name__ != "TextBox":
        return

    # Look for an inline parent box reference
    parent_inline = None
    if hasattr(box, "node") and hasattr(box.node, "props"):
        parent_inline = box.node.props.get("_inline_parent_box")

    if not parent_inline:
        return

    if parent_inline.__class__.__name__ != "InlineBox":
        return

    node_style = (
        getattr(parent_inline.node, "style", {})
        if hasattr(parent_inline, "node")
        else {}
    )

    if node_style.get("visibility") == "hidden":
        return

    bg_color_str = node_style.get("background-color")
    if not bg_color_str or bg_color_str == "transparent":
        return

    rgb = parse_color(bg_color_str)
    if rgb is None:
        return
    r, g, b = rgb
    if r is None:
        return

    # Get the inline background regions
    bg_regions = getattr(parent_inline, "_inline_bg_regions", [])
    if not bg_regions:
        return

    # Prevent drawing the same inline background multiple times
    # (once per TextBox child). Use a set on the PDF object to track drawn boxes.
    if not hasattr(pdf, "_drawn_inline_boxes"):
        pdf._drawn_inline_boxes = set()

    parent_id = id(parent_inline)
    if parent_id in pdf._drawn_inline_boxes:
        return

    pdf._drawn_inline_boxes.add(parent_id)

    pdf.set_fill_color(r, g, b)

    for x, y, w, h in bg_regions:
        # Convert absolute coordinates to page-relative
        absolute_y = y + dy
        start_page = int(absolute_y / PAGE_HEIGHT)
        end_page = int((absolute_y + h) / PAGE_HEIGHT)

        for p in range(start_page, end_page + 1):
            if not getattr(pdf, "_suppress_page_jump", False):
                _ensure_page(pdf, p)
            pdf.set_fill_color(r, g, b)

            # Get page margins for clipping
            mt, mb, ml, mr = _get_page_margins(pdf, p, page_rules, page_names)

            # Local y position on this page
            local_y = absolute_y - (p * PAGE_HEIGHT)
            local_h = h

            # Clip against page boundaries
            if local_y < mt:
                local_h -= mt - local_y
                local_y = mt

            if local_y + local_h > PAGE_HEIGHT - mb:
                local_h = (PAGE_HEIGHT - mb) - local_y

            if local_h > 0:
                pdf.rect(x=x, y=local_y, w=w, h=local_h, style="F")

    pdf.set_fill_color(0, 0, 0)


def _draw_text(
    pdf: fpdf.FPDF,
    box: TextBox,
    style: dict,
    border_box_x: float,
    border_box_y: float,
    border_top: float,
    border_left: float,
    anchor_map: dict = None,
    page_rules: list = None,
    page_names: dict = None,
) -> None:
    """
    Paints correctly formatted and styled inline text primitives or
    vector list markers.
    """
    if style.get("visibility") == "hidden":
        return

    text_content = box.text_content
    if not text_content:
        return

    transform = style.get("text-transform", "none").lower()
    if transform == "uppercase":
        text_content = text_content.upper()
    elif transform == "lowercase":
        text_content = text_content.lower()
    elif transform == "capitalize":
        text_content = text_content.title()

    # Phase 11: Resolve cross-references in text: target-counter(#id, page)
    if "target-counter" in text_content and anchor_map:
        import re

        tc_regex = r"target-counter\(([^,]+),\s*page\)"
        matches = re.findall(tc_regex, text_content)
        for target_id_raw in matches:
            target_id = target_id_raw.strip("#'\" ")
            if target_id in anchor_map:
                val = anchor_map[target_id]
                if isinstance(val, tuple):
                    replacement = str(val[1] + 1)
                    text_content = text_content.replace(
                        f"target-counter({target_id_raw}, page)", replacement
                    )
                else:
                    text_content = text_content.replace(
                        f"target-counter({target_id_raw}, page)", "??"
                    )
            else:
                text_content = text_content.replace(
                    f"target-counter({target_id_raw}, page)", "??"
                )

    content_x = border_box_x + border_left + box.padding_left
    content_y = border_box_y + border_top + box.padding_top

    page_idx = int(content_y / PAGE_HEIGHT)
    if not getattr(pdf, "_suppress_page_jump", False):
        _ensure_page(pdf, page_idx, page_rules=page_rules, page_names=page_names)

    local_y = content_y - (page_idx * PAGE_HEIGHT)

    color_str = style.get("color", DEFAULT_COLOR)
    rgb = parse_color(color_str)
    r, g, b = rgb if rgb else (0, 0, 0)

    if box.__class__.__name__ == "MarkerBox" and text_content in (
        "__disc__",
        "__circle__",
        "__square__",
    ):
        # Draw vector shapes for list markers
        pdf.set_fill_color(r, g, b)
        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(0.5)

        if text_content == "__disc__":
            pdf.ellipse(x=content_x, y=local_y, w=box.w, h=box.h, style="F")
        elif text_content == "__circle__":
            pdf.ellipse(x=content_x, y=local_y, w=box.w, h=box.h, style="D")
        elif text_content == "__square__":
            pdf.rect(x=content_x, y=local_y, w=box.w, h=box.h, style="F")

        pdf.set_fill_color(0, 0, 0)
        pdf.set_draw_color(0, 0, 0)
        return

    pdf.set_xy(content_x, local_y)
    family, fpdf_style, size = parse_font(style)

    # Map CSS text-align to FPDF align code
    # NOTE: We map all to "L" because the layout engine (IFC) pre-calculates
    # absolute x/y coordinates for every TextBox after alignment shifts.
    fpdf_align = "L"

    # Font and color settings
    pdf.set_text_color(r, g, b)
    from pypdfpatra.engine.font_metrics import FontMetrics

    metrics = FontMetrics.get_instance()
    metrics.set_font_safe(pdf, family, size, fpdf_style)

    # Phase 12: Handle letter-spacing and small-caps
    ls_str = style.get("letter-spacing", "normal").strip().lower()
    letter_spacing = 0.0
    if ls_str != "normal":
        if ls_str.endswith("px") or ls_str.endswith("pt"):
            letter_spacing = float(ls_str[:-2])
        elif ls_str.endswith("em"):
            letter_spacing = float(ls_str[:-2]) * size

    variant = style.get("font-variant", "normal").lower()

    # Phase 12: Manual character drawing for letter-spacing/small-caps
    if letter_spacing != 0 or variant == "small-caps":
        current_x = content_x
        from pypdfpatra.defaults import SMALL_CAPS_RATIO

        small_size = size * SMALL_CAPS_RATIO

        for char in text_content:
            is_small = variant == "small-caps" and char.islower()
            draw_size = small_size if is_small else size
            char_to_draw = char.upper() if is_small else char

            metrics.set_font_safe(pdf, family, draw_size, fpdf_style)
            c_w = pdf.get_string_width(char_to_draw) + letter_spacing

            pdf.set_xy(current_x, local_y)
            pdf.cell(w=c_w, h=box.h, text=char_to_draw)
            current_x += c_w
    else:
        pdf.cell(w=box.w, h=box.h, text=text_content, align=fpdf_align)

    # Draw text decoration lines (underline and line-through)
    decoration = style.get("text-decoration", "none").strip().lower()
    if decoration not in ("none", ""):
        line_w = box.w
        line_weight = max(0.4, size * 0.05)

        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(line_weight)

        if "underline" in decoration:
            underline_y = local_y + box.h - line_weight
            pdf.line(content_x, underline_y, content_x + line_w, underline_y)

        if "line-through" in decoration:
            strikethrough_y = local_y + box.h * 0.55
            pdf.line(content_x, strikethrough_y, content_x + line_w, strikethrough_y)

        pdf.set_line_width(0.2)
        pdf.set_draw_color(0, 0, 0)


def _draw_image(
    pdf: fpdf.FPDF,
    box: Box,
    style: dict,
    border_box_x: float,
    border_box_y: float,
    border_top: float,
    border_left: float,
    page_rules: list = None,
    page_names: dict = None,
) -> None:
    """Paints external image assets onto the PDF respecting absolute geometry."""
    if style.get("visibility") == "hidden":
        return
    img_src = getattr(box, "img_src", "")
    if not img_src:
        return

    content_x = border_box_x + border_left + box.padding_left
    content_y = border_box_y + border_top + box.padding_top

    page_idx = int(content_y / PAGE_HEIGHT)
    _ensure_page(pdf, page_idx, page_rules=page_rules, page_names=page_names)

    local_y = content_y - (page_idx * PAGE_HEIGHT)

    try:
        pdf.image(name=img_src, x=content_x, y=local_y, w=box.w, h=box.h)
    except Exception as e:
        print(f"pypdfpatra - WARNING - Failed to render image {img_src}: {e}")
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x=content_x, y=local_y, w=box.w, h=box.h, style="D")

        alt_text = getattr(box, "alt_text", "")
        if not alt_text:
            alt_text = img_src.split("/")[-1].split("\\")[-1]

        pdf.set_xy(content_x + 2, local_y + 2)
        pdf.set_text_color(150, 150, 150)
        pdf.set_font(DEFAULT_FONT_FAMILY, size=8)
        pdf.cell(w=max(0, box.w - 4), h=10, text=alt_text, align="L")
        pdf.set_draw_color(0, 0, 0)
        pdf.set_text_color(0, 0, 0)


def draw_boxes(
    pdf: fpdf.FPDF,
    boxes: list[Box],
    dx: float = 0.0,
    dy: float = 0.0,
    anchor_map: dict = None,
    skip_fixed: bool = False,
    string_map: dict = None,
    page_rules: list = None,
    page_names: dict = None,
):
    """
    Recursively iterates through the W3C Box Tree (Render Tree)
    and paints the boxes onto the PDF.
    """
    if string_map is None:
        string_map = {}

    # Phase 9: Stacking Order (z-index)
    # W3C Appendix E: Positioned elements paint after non-positioned ones.
    def stacking_key(b):
        zi = getattr(b, "z_index", 0)
        pos = getattr(b, "position", "static")
        is_pos = pos != "static"

        # Level 1: Negative Z-index positioned
        # Level 2: Normal flow (is_pos=False)
        # Level 3: Z-index >= 0 positioned
        if is_pos:
            if zi < 0:
                return (0, zi)  # Level 0, then sort by zi
            else:
                return (2, zi)  # Level 2, then sort by zi
        else:
            return (1, 0)  # Level 1 (normal flow)

    sorted_boxes = sorted(boxes, key=stacking_key)

    for box in sorted_boxes:
        if box is None:
            continue
        if skip_fixed and getattr(box, "position", "static") == "fixed":
            continue

        style = getattr(box.node, "style", {})

        border_left = getattr(box, "border_left", 0)
        border_right = getattr(box, "border_right", 0)
        border_top = getattr(box, "border_top", 0)
        border_bottom = getattr(box, "border_bottom", 0)

        # Phase 9b: Apply CSS Transforms (currently Translation only)
        tx, ty = _apply_transform(getattr(box, "transform_matrix", None))

        border_box_x = (box.x + dx) + box.margin_left + tx
        border_box_y = (box.y + dy) + box.margin_top + ty
        border_box_w = (
            border_left + box.padding_left + box.w + box.padding_right + border_right
        )
        border_box_h = (
            border_top + box.padding_top + box.h + box.padding_bottom + border_bottom
        )

        if box.__class__.__name__ == "TableBox":
            caption_h = 0.0
            for child in box.children:
                if getattr(child.node, "tag", "") == "caption":
                    caption_h += (
                        child.h
                        + child.margin_top
                        + child.margin_bottom
                        + child.border_top
                        + child.border_bottom
                        + child.padding_top
                        + child.padding_bottom
                    )

            border_box_y += caption_h
            border_box_h -= caption_h

        is_fixed = getattr(box, "position", "static") == "fixed"

        _draw_background(
            pdf,
            style,
            border_box_x,
            border_box_y,
            border_box_w,
            border_box_h,
            page_rules=page_rules,
            page_names=page_names,
            skip_clipping=is_fixed,
        )

        _draw_borders(
            pdf,
            style,
            border_top,
            border_bottom,
            border_left,
            border_right,
            border_box_x,
            border_box_y,
            border_box_w,
            border_box_h,
            page_rules=page_rules,
            page_names=page_names,
            skip_clipping=is_fixed,
        )

        # Draw inline element backgrounds (Phase 15)
        _draw_inline_backgrounds(
            pdf,
            box,
            style,
            dy=dy,
            page_rules=page_rules,
            page_names=page_names,
        )

        # Handle string-set (Phase 11 Named Strings)
        string_set = style.get("string-set")
        if string_set:
            # Format: name content()
            # Simplified: name content()
            import re

            match = re.search(r"(\w+)\s+content\(", string_set)
            if match:
                sname = match.group(1)
                # Extract text content from this box
                text_content = ""
                box_stack = [box]
                while box_stack:
                    curr = box_stack.pop()
                    if isinstance(curr, TextBox):
                        text_content += curr.text_content
                    if hasattr(curr, "children"):
                        box_stack.extend(reversed(curr.children))

                page_idx = int(border_box_y / PAGE_HEIGHT)
                if page_idx not in string_map:
                    string_map[page_idx] = {}
                string_map[page_idx][sname] = text_content

        href = getattr(box.node, "props", {}).get("href")
        if href:
            page_idx = int(border_box_y / PAGE_HEIGHT)
            local_y = border_box_y - (page_idx * PAGE_HEIGHT)

            target = href
            if href.startswith("#") and anchor_map:
                target_id = href[1:]
                if target_id in anchor_map:
                    target = anchor_map[target_id]
                    if isinstance(target, tuple):
                        target = target[0]

            pdf.link(
                x=border_box_x, y=local_y, w=border_box_w, h=border_box_h, link=target
            )

        if isinstance(box, TextBox) or box.__class__.__name__ == "MarkerBox":
            _draw_text(
                pdf,
                box,
                style,
                border_box_x,
                border_box_y,
                border_top,
                border_left,
                anchor_map=anchor_map,
                page_rules=page_rules,
                page_names=page_names,
            )

        # PDF Bookmarks (Outlines) for Headings (Phase 7)
        tag = getattr(box.node, "tag", "").lower()
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1]) - 1
            # We get the text content from the box children if they are text boxes
            heading_text = ""
            for child in box.children:
                if isinstance(child, TextBox):
                    heading_text += child.text_content

            if heading_text:
                page_idx = int(border_box_y / PAGE_HEIGHT)
                local_y = border_box_y - (page_idx * PAGE_HEIGHT)
                _ensure_page(
                    pdf, page_idx, page_rules=page_rules, page_names=page_names
                )
                # Save position, jump to heading Y, start section, restore position
                old_y = pdf.y
                pdf.y = local_y
                pdf.start_section(heading_text, level=level - 1)
                pdf.y = old_y

        if box.__class__.__name__ == "ImageBox":
            _draw_image(
                pdf,
                box,
                style,
                border_box_x,
                border_box_y,
                border_top,
                border_left,
                page_rules=page_rules,
                page_names=page_names,
            )

        if box.children:
            draw_boxes(
                pdf,
                box.children,
                dx=dx + tx,
                dy=dy + ty,
                anchor_map=anchor_map,
                skip_fixed=skip_fixed,
                string_map=string_map,
                page_rules=page_rules,
                page_names=page_names,
            )

        if dy == 0.0 and box.__class__.__name__ == "TableBox":
            thead_rows = getattr(box, "thead_rows", [])
            if thead_rows:
                start_page = int(border_box_y / PAGE_HEIGHT)
                end_page = int((border_box_y + border_box_h) / PAGE_HEIGHT)

                if end_page > start_page:
                    header_original_y = thead_rows[0].y
                    for p in range(start_page + 1, end_page + 1):
                        mt, _, _, _ = _get_page_margins(pdf, p, page_rules, page_names)
                        header_target_y = (p * PAGE_HEIGHT) + mt
                        repeat_dy = header_target_y - header_original_y
                        draw_boxes(
                            pdf,
                            thead_rows,
                            dx=dx,
                            dy=repeat_dy,
                            anchor_map=anchor_map,
                            page_rules=page_rules,
                            page_names=page_names,
                        )

        pass


def draw_page_margin_boxes(
    pdf: fpdf.FPDF,
    page_rules: list[PageRule],
    total_pages: int,
    anchor_map: dict = None,
    string_map: dict = None,
    page_names: dict[int, str] = None,
):
    """Draws margin boxes (@top-left, etc) on every page."""
    from pypdfpatra.defaults import PAGE_HEIGHT, PAGE_WIDTH

    if string_map is None:
        string_map = {}  # Maps page_idx -> {string_name: value}

    pdf._suppress_page_jump = True
    for page_idx in range(total_pages):
        pdf.page = page_idx + 1
        page_name = "default"
        if page_names and page_idx in page_names:
            page_name = page_names[page_idx]

        page_style = resolve_page_style(page_rules, page_idx, page_name=page_name)

        from pypdfpatra.engine.page import get_resolved_margins

        mt, mb, ml, mr = get_resolved_margins(page_rules, page_idx, page_name)

        content_w = PAGE_WIDTH - ml - mr

        # Get resolved strings for this page (last value set on or before this page)
        curr_strings = {}
        for p in range(page_idx + 1):
            if p in string_map:
                curr_strings.update(string_map[p])

        for mb_name, mb_style in page_style.margin_boxes.items():
            content = mb_style.get("content", "").strip()
            if not content or content == "none":
                continue

            # Resolve counters
            if "counter(page)" in content:
                content = content.replace("counter(page)", str(page_idx + 1))
            if "counter(pages)" in content:
                content = content.replace("counter(pages)", str(total_pages))

            # Resolve named strings: string(name)
            import re

            string_matches = re.findall(r"string\(([^)]+)\)", content)
            for sname in string_matches:
                val = curr_strings.get(sname, "")
                content = content.replace(f"string({sname})", val)

            # Resolve cross-references: target-counter(#id, page)
            tc_regex = r"target-counter\(([^,]+),\s*page\)"
            target_counter_matches = re.findall(tc_regex, content)
            for target_id_raw in target_counter_matches:
                target_id = target_id_raw.strip("#'\" ")
                if anchor_map and target_id in anchor_map:
                    # In fpdf2, link destination doesn't easily expose page number
                    # But we stored it in register_anchors!
                    # Let's fix register_anchors to store (link_id, page_idx)
                    val = anchor_map[target_id]
                    if isinstance(val, tuple):
                        replacement = str(val[1] + 1)
                        content = content.replace(
                            f"target-counter({target_id_raw}, page)", replacement
                        )
                    else:
                        content = content.replace(
                            f"target-counter({target_id_raw}, page)", "??"
                        )
                else:
                    content = content.replace(
                        f"target-counter({target_id_raw}, page)", "??"
                    )

            content = content.strip("\"'")

            # Simplified positioning for common margin boxes
            x, y, w, h = 0, 0, 0, 0
            align = mb_style.get("text-align", "center")

            if mb_name == "top-left":
                x, y, w, h = ml, 0, content_w / 3, mt
                align = mb_style.get("text-align", "left")
            elif mb_name == "top-center":
                x, y, w, h = ml + content_w / 3, 0, content_w / 3, mt
                align = mb_style.get("text-align", "center")
            elif mb_name == "top-right":
                x, y, w, h = ml + 2 * content_w / 3, 0, content_w / 3, mt
                align = mb_style.get("text-align", "right")
            elif mb_name == "bottom-left":
                x, y, w, h = ml, PAGE_HEIGHT - mb, content_w / 3, mb
                align = mb_style.get("text-align", "left")
            elif mb_name == "bottom-center":
                x, y, w, h = ml + content_w / 3, PAGE_HEIGHT - mb, content_w / 3, mb
                align = mb_style.get("text-align", "center")
            elif mb_name == "bottom-right":
                x, y, w, h = ml + 2 * content_w / 3, PAGE_HEIGHT - mb, content_w / 3, mb
                align = mb_style.get("text-align", "right")
            else:
                continue

            _draw_background(pdf, mb_style, x, y, w, h, skip_clipping=True)

            family, fpdf_style, size = parse_font(mb_style)
            color_str = mb_style.get("color", DEFAULT_COLOR)
            rgb = parse_color(color_str)
            r, g, b = rgb if rgb else (0, 0, 0)

            pdf.set_text_color(r, g, b)
            from pypdfpatra.engine.font_metrics import FontMetrics, get_line_height

            FontMetrics.get_instance().set_font_safe(pdf, family, size, fpdf_style)
            line_h = get_line_height(family, size, fpdf_style)

            v_align = mb_style.get("vertical-align", "middle").strip().lower()

            # Adjust Y and H based on vertical-align
            cell_y = y
            cell_h = h

            if v_align == "top":
                cell_h = line_h
            elif v_align == "bottom":
                cell_y = y + h - line_h
                cell_h = line_h
            # "middle" (default) uses the full height of the margin area to center

            pdf.set_xy(x, cell_y)
            fpdf_align = {"left": "L", "center": "C", "right": "R"}.get(align, "C")
            pdf.cell(w=w, h=cell_h, text=content, align=fpdf_align)

    pdf._suppress_page_jump = False
    pdf.set_text_color(0, 0, 0)
