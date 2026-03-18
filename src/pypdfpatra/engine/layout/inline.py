"""
pypdfpatra.engine.layout.inline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Implements the W3C Inline Formatting Context (IFC).
"""

import re

import pyphen

from pypdfpatra.defaults import PAGE_HEIGHT
from pypdfpatra.engine.font_metrics import get_line_height, measure_text, parse_font
from pypdfpatra.engine.tree import Box, LineBox, TextBox

from .common import PosCB

_pyphen_cache = {}


def _get_pyphen(lang: str = "en"):
    if lang not in _pyphen_cache:
        try:
            _pyphen_cache[lang] = pyphen.Pyphen(lang=lang)
        except Exception:
            _pyphen_cache[lang] = pyphen.Pyphen(lang="en")
    return _pyphen_cache[lang]


def _get_lang(node):
    curr = node
    while curr:
        if hasattr(curr, "props"):
            lang = curr.props.get("lang")
            if lang:
                return lang
        curr = getattr(curr, "parent", None)
    return "en"


# Removed - functionality merged into _flatten_inline


def _calculate_inline_bg_regions(line_box: LineBox) -> None:
    """
    After a LineBox is populated, traverse its children to calculate
    background regions for InlineBox ancestors of TextBoxes.

    This stores the bounding rectangles on each InlineBox's _inline_bg_regions
    property without modifying the line_box.children structure.
    """
    if not hasattr(line_box, "children") or not line_box.children:
        return

    # Build a mapping of (InlineBox, y_position) -> list of TextBoxes
    inline_regions = {}

    for child in line_box.children:
        if isinstance(child, TextBox):
            # Get inline parent from node.props (stored during flattening)
            parent_inline = None
            if child.node and hasattr(child.node, "props"):
                parent_inline = child.node.props.get("_inline_parent_box")

            if parent_inline and parent_inline.__class__.__name__ == "InlineBox":
                # Round y to group TextBoxes on same baseline
                y_key = round(child.y, 2)
                key = (id(parent_inline), y_key)
                if key not in inline_regions:
                    inline_regions[key] = (parent_inline, [])
                inline_regions[key][1].append(child)

    # For each inline box, calculate its background regions
    for (_inline_id, _y_pos), (inline_box, text_boxes) in inline_regions.items():
        if not text_boxes:
            continue

        # Sort text boxes by x position
        text_boxes_sorted = sorted(text_boxes, key=lambda tb: tb.x)

        # Group consecutive text boxes that should be in one background region
        regions = []
        current_region_boxes = [text_boxes_sorted[0]]

        for tb in text_boxes_sorted[1:]:
            prev_box = current_region_boxes[-1]
            # Check if this box is adjacent or overlapping with previous
            # Allow small gap for spacing
            gap = tb.x - (prev_box.x + prev_box.w)
            if gap <= 0.5:  # Adjacent or overlapping
                current_region_boxes.append(tb)
            else:
                # Start a new region
                regions.append(current_region_boxes)
                current_region_boxes = [tb]

        if current_region_boxes:
            regions.append(current_region_boxes)

        # Calculate bounding box for each region
        bg_regions = []
        for region_boxes in regions:
            min_x = min(tb.x for tb in region_boxes)
            max_x = max(tb.x + tb.w for tb in region_boxes)
            min_y = min(tb.y for tb in region_boxes)
            max_y = max(tb.y + tb.h for tb in region_boxes)

            # Add padding from inline box's padding
            padding_left = getattr(inline_box, "padding_left", 0.0)
            padding_right = getattr(inline_box, "padding_right", 0.0)
            padding_top = getattr(inline_box, "padding_top", 0.0)
            padding_bottom = getattr(inline_box, "padding_bottom", 0.0)

            x = min_x - padding_left
            y = min_y - padding_top
            w = (max_x - min_x) + padding_left + padding_right
            h = (max_y - min_y) + padding_top + padding_bottom

            bg_regions.append((x, y, w, h))

        # Store regions on the inline box
        if hasattr(inline_box, "_inline_bg_regions"):
            inline_box._inline_bg_regions = bg_regions
        else:
            # Should be initialized in tree.pyx
            pass


def _flatten_inline(boxes: list[Box], parent_inline=None) -> list[Box]:
    """
    Flattens nested InlineBox wrappers into a 1D sequence for line wrapper.
    Also tracks inline parent on each TextBox for background-color support.
    Stores parent reference in node.props (Cython objects lack __dict__).
    """
    flat = []
    for b in boxes:
        if isinstance(b, TextBox):
            # Store the inline parent in node.props for later background calculation
            if b.node and hasattr(b.node, "props"):
                b.node.props["_inline_parent_box"] = parent_inline
            flat.append(b)
        elif b.__class__.__name__ == "InlineBox":
            href = getattr(b.node, "props", {}).get("href")
            children = _flatten_inline(b.children, parent_inline=b)
            if href:
                for c in children:
                    # Inherit the anchor's href if the child node doesn't have one
                    if c.node and "href" not in c.node.props:
                        c.node.props["href"] = href
            flat.extend(children)
        elif b.__class__.__name__ == "LineBox":
            flat.extend(_flatten_inline(b.children, parent_inline))
        else:
            # Store parent reference for non-TextBox children too
            if b.node and hasattr(b.node, "props"):
                b.node.props["_inline_parent_box"] = parent_inline
            flat.append(b)
    return flat


def shift_box(b: Box, dx: float, dy: float) -> None:
    """Recursively shifts a box and its children."""
    b.x += dx
    b.y += dy
    for c in getattr(b, "children", []):
        shift_box(c, dx, dy)


def _commit_line(
    current_line_boxes: list[tuple[Box, float, float]],
    line_x: float,
    current_y: float,
    line_w: float,
    parent_box: Box,
    text_align: str = "left",
    is_last_line: bool = False,
    current_page_name: str = "default",
    page_rules: list | None = None,
    float_manager: object = None,
) -> tuple[float, float]:
    """
    Constructs a LineBox from the accumulated inline boxes and appends it to the parent.
    Returns (consumed_max_h, new_y_bottom).
    """
    if not current_line_boxes:
        return 0.0, current_y

    # Create the LineBox container
    line_box = LineBox(node=None)
    line_box.x = line_x
    line_box.w = line_w

    # Determine line height (max height of outer box dimensions)
    max_h = 0.0
    for item in current_line_boxes:
        _, _, outer_h = item
        if outer_h > max_h:
            max_h = outer_h

    if max_h == 0:
        max_h = 20.0

    # Pagination: move lines to next page if they overflow current boundary.
    current_page_idx = int(current_y / PAGE_HEIGHT)
    from pypdfpatra.engine.page import get_resolved_margins

    _, mb, _, _ = get_resolved_margins(page_rules, current_page_idx, current_page_name)
    page_boundary = (current_page_idx + 1) * PAGE_HEIGHT - mb

    if current_y + max_h > page_boundary:
        next_page_idx = current_page_idx + 1
        nmt, _, _, _ = get_resolved_margins(
            page_rules, next_page_idx, current_page_name
        )
        current_y = (next_page_idx * PAGE_HEIGHT) + nmt

    line_box.y = current_y
    line_box.h = max_h

    # Center horizontally if needed. Right now, W3C aligned left.
    text_align = text_align.strip().lower()

    # Calculate total line width
    total_line_width = 0.0
    if current_line_boxes:
        last_box, last_w, _ = current_line_boxes[-1]
        total_line_width = (last_box.x + last_w) - line_x

    # Calculate horizontal shift
    dx = 0.0
    if text_align == "center":
        dx = max(0.0, (line_w - total_line_width) / 2.0)
    elif text_align == "right":
        dx = max(0.0, line_w - total_line_width)
    elif text_align == "justify":
        # W3C: last line of a paragraph is NOT justified by default (text-align-last).
        if not is_last_line and len(current_line_boxes) > 1:
            extra_total = line_w - total_line_width
            # Only justify if there's a reasonable amount of text (avoid weird gaps)
            if extra_total > 0 and extra_total < (line_w * 0.4):
                gap_per_word = extra_total / (len(current_line_boxes) - 1)
                for i, (child, _, _) in enumerate(current_line_boxes):
                    shift_box(child, i * gap_per_word, 0)
                total_line_width = line_w

    for item in current_line_boxes:
        child, _, outer_h = item
        # Align bottom of outer box to bottom of line box
        target_outer_y = current_y + (max_h - outer_h)

        # target_outer_y is where the margin-top starts.
        target_content_y = (
            target_outer_y
            + getattr(child, "margin_top", 0)
            + getattr(child, "border_top", 0)
            + getattr(child, "padding_top", 0)
        )

        dy = target_content_y - child.y
        shift_box(child, dx, dy)

        line_box.children.append(child)

    # Calculate background regions for inline elements (after positioning)
    _calculate_inline_bg_regions(line_box)

    parent_box.children.append(line_box)
    return max_h, current_y + max_h


def _process_text_box(
    child: TextBox,
    line_w: float,
    line_x: float,
    current_y: float,
    current_line_width: float,
    current_line_ends_with_space: bool,
    current_line_boxes: list[tuple[Box, float, float]],
    parent_box: Box,
    text_align: str = "left",
    root_font_size: float = 12.0,
    current_page_name: str = "default",
    page_rules: list | None = None,
    float_manager: object = None,
) -> tuple[float, float, bool, float, float]:
    content = child.text_content
    if not content:
        return (
            current_y,
            current_line_width,
            current_line_ends_with_space,
            line_x,
            line_w,
        )

    style = getattr(child.node, "style", {}) if child.node else {}
    white_space = style.get("white-space", "normal")
    css_lh = style.get("line-height", "normal")

    family, fpdf_style, size = parse_font(style)

    # Phase 12: Support letter-spacing
    ls_str = style.get("letter-spacing", "normal").strip().lower()
    letter_spacing = 0.0
    if ls_str != "normal":
        if ls_str.endswith("px") or ls_str.endswith("pt"):
            letter_spacing = float(ls_str[:-2])
        elif ls_str.endswith("em"):
            letter_spacing = float(ls_str[:-2]) * size
        else:
            try:
                letter_spacing = float(ls_str)
            except ValueError:
                pass
    transform = style.get("text-transform", "none").lower()
    if transform == "uppercase":
        content = content.upper()
    elif transform == "lowercase":
        content = content.lower()
    elif transform == "capitalize":
        content = content.title()

    space_width = measure_text(" ", family, size, fpdf_style)

    if white_space == "pre":
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if i > 0:
                consumed_h, current_y = _commit_line(
                    current_line_boxes,
                    line_x,
                    current_y,
                    line_w,
                    parent_box,
                    text_align,
                    is_last_line=True,
                    current_page_name=current_page_name,
                    page_rules=page_rules,
                    float_manager=float_manager,
                )
                current_line_boxes.clear()
                current_line_width = 0.0
                current_line_ends_with_space = False
                if float_manager:
                    line_x, line_w = float_manager.get_line_geometry(
                        current_y, size, parent_box.x, parent_box.w
                    )

            if not line:
                continue

            word_w = measure_text(line, family, size, fpdf_style)
            while current_line_width + word_w > line_w:
                if current_line_width > 0:
                    consumed_h, current_y = _commit_line(
                        current_line_boxes,
                        line_x,
                        current_y,
                        line_w,
                        parent_box,
                        text_align,
                        is_last_line=False,
                        current_page_name=current_page_name,
                        page_rules=page_rules,
                        float_manager=float_manager,
                    )
                    current_line_boxes.clear()
                    current_line_width = 0.0
                    current_line_ends_with_space = False
                    if float_manager:
                        line_x, line_w = float_manager.get_line_geometry(
                            current_y, size, parent_box.x, parent_box.w
                        )
                else:
                    break

            word_box = TextBox(text_content=line, node=child.node)
            word_box.w = word_w
            word_box.h = get_line_height(
                family, size, fpdf_style, css_line_height=css_lh
            )
            word_box.x = line_x + current_line_width
            word_box.y = 0.0  # Will be shifted

            current_line_width += word_w
            current_line_boxes.append((word_box, word_w, word_box.h))
    else:
        # Preserve newlines and spaces, then handle them according to
        # white-space property.
        # Phase 14: Improve tokenization to support breaking after hyphens
        # Split by whitespace, and then further split non-whitespace tokens by hyphens
        raw_tokens = re.split(
            r"(target-counter\s*\(.*?\)|[ \t\n\r]+)", content, flags=re.IGNORECASE
        )
        tokens = []
        for t in raw_tokens:
            if not t:
                continue
            if t.isspace() or t.lower().startswith("target-counter"):
                tokens.append(t)
                continue
            # Split after hyphen but NOT if it's the only character
            if "-" in t and len(t) > 1:
                # e.g. "multi-stage" -> ["multi-", "stage"]
                sub_tokens = re.split(r"(?<=-)", t)
                tokens.extend([st for st in sub_tokens if st])
            else:
                tokens.append(t)

        for token in tokens:
            if "\n" in token or "\r" in token:
                if white_space == "pre-line":
                    consumed_h, current_y = _commit_line(
                        current_line_boxes,
                        line_x,
                        current_y,
                        line_w,
                        parent_box,
                        text_align,
                        is_last_line=True,
                        current_page_name=current_page_name,
                        page_rules=page_rules,
                        float_manager=float_manager,
                    )
                    current_line_boxes.clear()
                    current_line_width = 0.0
                    current_line_ends_with_space = False
                    if float_manager:
                        line_x, line_w = float_manager.get_line_geometry(
                            current_y, size, parent_box.x, parent_box.w
                        )
                    continue
                else:
                    # Treat newline as space for 'normal'
                    token = " "

            if token.isspace():
                if current_line_width > 0 and not current_line_ends_with_space:
                    current_line_width += space_width
                    current_line_ends_with_space = True
                continue

            variant = style.get("font-variant", "normal").lower()
            if token.lower().startswith("target-counter"):
                # Estimate width as a 2-digit page number for layout purposes
                word_w = measure_text("00", family, size, fpdf_style)
            elif variant == "small-caps":
                word_w = 0.0
                from pypdfpatra.defaults import SMALL_CAPS_RATIO

                small_size = size * SMALL_CAPS_RATIO
                for char in token:
                    if char.islower():
                        word_w += (
                            measure_text(char.upper(), family, small_size, fpdf_style)
                            + letter_spacing
                        )
                    else:
                        word_w += (
                            measure_text(char, family, size, fpdf_style)
                            + letter_spacing
                        )
                # Subtract trailing letter spacing as it's added inside the loop
                if token:
                    word_w -= letter_spacing
            else:
                word_w = measure_text(token, family, size, fpdf_style)
                # Phase 12: Apply letter-spacing to width
                if letter_spacing != 0 and len(token) > 1:
                    word_w += (len(token) - 1) * letter_spacing

            if current_line_width + word_w > line_w:
                hyphens_mode = style.get("hyphens", "manual").lower()
                if hyphens_mode == "auto":
                    lang = _get_lang(child.node).split("-")[0]
                    dic = _get_pyphen(lang)

                    # Try to hyphenate the word
                    hyphenated = dic.iterate(token)
                    remaining_space = line_w - current_line_width
                    hyphen_w = measure_text("-", family, size, fpdf_style)

                    best_prefix = None
                    best_prefix_w = 0.0
                    leftover = token

                    for prefix, suffix in hyphenated:
                        # Prefix width + hyphen must fit
                        p_w = measure_text(prefix, family, size, fpdf_style)
                        if variant == "small-caps":
                            # Accurate small-caps measurement for prefix
                            p_w = 0.0
                            for char in prefix:
                                if char.islower():
                                    from pypdfpatra.defaults import SMALL_CAPS_RATIO

                                    p_w += (
                                        measure_text(
                                            char.upper(),
                                            family,
                                            size * SMALL_CAPS_RATIO,
                                            fpdf_style,
                                        )
                                        + letter_spacing
                                    )
                                else:
                                    p_w += (
                                        measure_text(char, family, size, fpdf_style)
                                        + letter_spacing
                                    )
                            if prefix:
                                p_w -= letter_spacing
                        elif letter_spacing != 0 and len(prefix) > 1:
                            p_w += (len(prefix) - 1) * letter_spacing

                        if p_w + hyphen_w <= remaining_space:
                            best_prefix = prefix + "-"
                            best_prefix_w = p_w + hyphen_w
                            leftover = suffix
                            break  # Found the longest prefix that fits

                    if best_prefix:
                        # Commit the prefix and hyphen
                        p_box = TextBox(text_content=best_prefix, node=child.node)
                        p_box.w = best_prefix_w
                        p_box.h = get_line_height(
                            family, size, fpdf_style, css_line_height=css_lh
                        )
                        p_box.x = line_x + current_line_width
                        p_box.y = 0.0
                        current_line_boxes.append((p_box, best_prefix_w, p_box.h))

                        consumed_h, current_y = _commit_line(
                            current_line_boxes,
                            line_x,
                            current_y,
                            line_w,
                            parent_box,
                            text_align,
                            current_page_name=current_page_name,
                            page_rules=page_rules,
                            float_manager=float_manager,
                        )
                        current_line_boxes.clear()
                        current_line_width = 0.0
                        current_line_ends_with_space = False
                        if float_manager:
                            line_x, line_w = float_manager.get_line_geometry(
                                current_y, size, parent_box.x, parent_box.w
                            )

                        # Process the remaining part of the word as the new token
                        token = leftover
                        # Re-calculate word_w for the leftover
                        if variant == "small-caps":
                            word_w = 0.0
                            for char in token:
                                if char.islower():
                                    word_w += (
                                        measure_text(
                                            char.upper(), family, size * 0.8, fpdf_style
                                        )
                                        + letter_spacing
                                    )
                                else:
                                    word_w += (
                                        measure_text(char, family, size, fpdf_style)
                                        + letter_spacing
                                    )
                            if token:
                                word_w -= letter_spacing
                        else:
                            word_w = measure_text(token, family, size, fpdf_style)
                            if letter_spacing != 0 and len(token) > 1:
                                word_w += (len(token) - 1) * letter_spacing
                    elif current_line_width > 0:
                        consumed_h, current_y = _commit_line(
                            current_line_boxes,
                            line_x,
                            current_y,
                            line_w,
                            parent_box,
                            text_align,
                            is_last_line=False,
                            current_page_name=current_page_name,
                            page_rules=page_rules,
                            float_manager=float_manager,
                        )
                        current_line_boxes.clear()
                        current_line_width = 0.0
                        current_line_ends_with_space = False
                        if float_manager:
                            line_x, line_w = float_manager.get_line_geometry(
                                current_y, size, parent_box.x, parent_box.w
                            )
                elif current_line_width > 0:
                    consumed_h, current_y = _commit_line(
                        current_line_boxes,
                        line_x,
                        current_y,
                        line_w,
                        parent_box,
                        text_align,
                        is_last_line=False,
                        current_page_name=current_page_name,
                        page_rules=page_rules,
                        float_manager=float_manager,
                    )
                    current_line_boxes.clear()
                    current_line_width = 0.0
                    current_line_ends_with_space = False
                    if float_manager:
                        line_x, line_w = float_manager.get_line_geometry(
                            current_y, size, parent_box.x, parent_box.w
                        )

            word_box = TextBox(text_content=token, node=child.node)
            word_box.w = word_w
            word_box.h = get_line_height(
                family, size, fpdf_style, css_line_height=css_lh
            )
            word_box.x = line_x + current_line_width
            word_box.y = 0.0  # Will be shifted

            current_line_width += word_w
            current_line_boxes.append((word_box, word_w, word_box.h))
            current_line_ends_with_space = False

    return current_y, current_line_width, current_line_ends_with_space, line_x, line_w


def _process_inline_box(
    child: Box,
    line_w: float,
    line_x: float,
    current_y: float,
    current_line_width: float,
    current_line_boxes: list[tuple[Box, float, float]],
    parent_box: Box,
    text_align: str = "left",
    root_font_size: float = 12.0,
    current_page_name: str = "default",
    page_rules: list | None = None,
    float_manager: object = None,
) -> tuple[float, float, bool, float, float]:
    child_style = getattr(child.node, "style", {})

    if child.__class__.__name__ == "InlineBlockBox":
        from .block import _parse_length, layout_block_context

        css_width = _parse_length(
            child_style.get("width", "auto"),
            line_w,
            default_auto=None,
            root_font_size=root_font_size,
        )
        if css_width is None:
            css_width = 150.0

        layout_block_context(
            child,
            0.0,
            0.0,
            css_width,
            root_font_size=root_font_size,
            current_page_name=current_page_name,
            page_rules=page_rules,
            pos_cb=PosCB(0, 0, css_width, 0),
        )

    elif child.__class__.__name__ == "ImageBox":
        from .block import _parse_length

        css_width = _parse_length(
            child_style.get("width", "auto"),
            line_w,
            default_auto=None,
            root_font_size=root_font_size,
        )
        css_height = _parse_length(
            child_style.get("height", "auto"),
            line_w,
            default_auto=None,
            root_font_size=root_font_size,
        )

        # Fallback to HTML attributes if no CSS width/height is present
        if css_width is None:
            attr_w = getattr(child.node, "props", {}).get("width")
            if attr_w:
                css_width = float(str(attr_w).replace("px", ""))
        if css_height is None:
            attr_h = getattr(child.node, "props", {}).get("height")
            if attr_h:
                css_height = float(str(attr_h).replace("px", ""))

        if css_width is not None and css_height is None:
            child.w = css_width
            child.h = (
                (child.image_h / child.image_w * css_width)
                if child.image_w > 0
                else css_width
            )
        elif css_height is not None and css_width is None:
            child.h = css_height
            child.w = (
                (child.image_w / child.image_h * css_height)
                if child.image_h > 0
                else css_height
            )
        elif css_width is not None and css_height is not None:
            child.w = css_width
            child.h = css_height
        else:
            child.w = child.image_w
            child.h = child.image_h

        # Responsive layout: don't bleed outside container
        if child.w > line_w and line_w > 0:
            ratio = line_w / child.w
            child.w = line_w
            child.h *= ratio

    child_total_w = (
        child.margin_left
        + child.border_left
        + child.padding_left
        + child.w
        + child.padding_right
        + child.border_right
        + child.margin_right
    )
    child_total_h = (
        child.margin_top
        + child.border_top
        + child.padding_top
        + child.h
        + child.padding_bottom
        + child.border_bottom
        + child.margin_bottom
    )

    if current_line_width + child_total_w > line_w and current_line_width > 0:
        consumed_h, current_y = _commit_line(
            current_line_boxes,
            line_x,
            current_y,
            line_w,
            parent_box,
            text_align,
            current_page_name=current_page_name,
            page_rules=page_rules,
            float_manager=float_manager,
        )
        current_line_boxes.clear()
        current_line_width = 0.0
        if float_manager:
            line_x, line_w = float_manager.get_line_geometry(
                current_y, root_font_size, parent_box.x, parent_box.w
            )

    target_content_x = (
        line_x
        + current_line_width
        + child.margin_left
        + child.border_left
        + child.padding_left
    )
    dx = target_content_x - child.x

    shift_box(child, dx, 0)

    current_line_width += child_total_w
    current_line_boxes.append((child, child_total_w, child_total_h))

    return current_y, current_line_width, False, line_x, line_w


def layout_inline_context(
    parent_box: Box,
    cb_x: float,
    cb_y: float,
    cb_w: float,
    text_align: str = "left",
    root_font_size: float = 12.0,
    current_page_name: str = "default",
    page_rules: list | None = None,
    float_manager: object = None,
) -> None:
    """
    Implements a basic W3C Inline Formatting Context (IFC).
    """
    inline_children = parent_box.children
    if not inline_children:
        return

    # Clear original children to replace them with LineBoxes
    parent_box.children = []

    current_line_boxes: list[tuple[Box, float, float]] = []
    current_line_width = 0.0
    current_line_ends_with_space = False

    current_y = cb_y
    if float_manager:
        line_x, line_w = float_manager.get_line_geometry(
            current_y, root_font_size, cb_x, cb_w
        )
    else:
        line_x, line_w = cb_x, cb_w

    # Flow the inline children
    flat_children = _flatten_inline(inline_children)
    for child in flat_children:
        if isinstance(child, TextBox):
            (
                current_y,
                current_line_width,
                current_line_ends_with_space,
                line_x,
                line_w,
            ) = _process_text_box(
                child,
                line_w,
                line_x,
                current_y,
                current_line_width,
                current_line_ends_with_space,
                current_line_boxes,
                parent_box,
                text_align,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                float_manager=float_manager,
            )
        else:
            (
                current_y,
                current_line_width,
                current_line_ends_with_space,
                line_x,
                line_w,
            ) = _process_inline_box(
                child,
                line_w,
                line_x,
                current_y,
                current_line_width,
                current_line_boxes,
                parent_box,
                text_align,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                float_manager=float_manager,
            )

    # Final commit for the last remaining line of the paragraph
    consumed_h, current_y = _commit_line(
        current_line_boxes,
        line_x,
        current_y,
        line_w,
        parent_box,
        text_align,
        is_last_line=True,
        current_page_name=current_page_name,
        page_rules=page_rules,
        float_manager=float_manager,
    )

    # The parent block box height expands to fit all the line boxes
    parent_box.h = max(0.0, current_y - cb_y)
