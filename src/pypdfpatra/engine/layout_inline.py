from pypdfpatra.engine.tree import Box, LineBox, TextBox
from pypdfpatra.engine.font_metrics import measure_text, get_line_height
from pypdfpatra.defaults import PAGE_HEIGHT, DEFAULT_MARGIN_TOP, DEFAULT_MARGIN_BOTTOM


def _flatten_inline(boxes: list[Box]) -> list[Box]:
    """Flattens nested InlineBox wrappers into a flat 1D sequence for the line wrapper."""
    flat = []
    for b in boxes:
        if isinstance(b, TextBox):
            flat.append(b)
        elif b.__class__.__name__ == "InlineBox":
            href = getattr(b.node, "props", {}).get("href")
            children = _flatten_inline(b.children)
            if href:
                for c in children:
                    # Inherit the anchor's href if the child node doesn't have one
                    if "href" not in c.node.props:
                        c.node.props["href"] = href
            flat.extend(children)
        else:
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
    cb_w: float,
    parent_box: Box,
    text_align: str = "left",
) -> float:
    """
    Constructs a LineBox from the accumulated inline boxes and appends it to the parent.
    Returns (consumed_max_h, new_y_bottom).
    """
    if not current_line_boxes:
        return 0.0, current_y

    # Create the LineBox container
    line_box = LineBox(node=None)
    line_box.x = line_x
    line_box.w = cb_w

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
    page_boundary = (current_page_idx + 1) * PAGE_HEIGHT - DEFAULT_MARGIN_BOTTOM

    if current_y + max_h > page_boundary:
        current_y = (current_page_idx + 1) * PAGE_HEIGHT + DEFAULT_MARGIN_TOP

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
        dx = max(0.0, (cb_w - total_line_width) / 2.0)
    elif text_align == "right":
        dx = max(0.0, cb_w - total_line_width)

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

    parent_box.children.append(line_box)
    return max_h, current_y + max_h


def _process_text_box(
    child: TextBox,
    cb_w: float,
    line_x: float,
    current_y: float,
    current_line_width: float,
    current_line_ends_with_space: bool,
    current_line_boxes: list[tuple[Box, float, float]],
    parent_box: Box,
    text_align: str = "left",
) -> tuple[float, float, bool]:
    content = child.text_content
    if not content:
        return current_y, current_line_width, current_line_ends_with_space

    style = getattr(child.node, "style", {}) if child.node else {}
    white_space = style.get("white-space", "normal")

    from pypdfpatra.engine.font_metrics import parse_font

    family, fpdf_style, size = parse_font(style)
    space_width = measure_text(" ", family, size, fpdf_style)

    if white_space == "pre":
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if i > 0:
                consumed_h, current_y = _commit_line(
                    current_line_boxes, line_x, current_y, cb_w, parent_box, text_align
                )
                current_line_boxes.clear()
                current_line_width = 0.0
                current_line_ends_with_space = False

            if not line:
                continue

            word_w = measure_text(line, family, size, fpdf_style)
            if current_line_width + word_w > cb_w and current_line_width > 0:
                consumed_h, current_y = _commit_line(
                    current_line_boxes, line_x, current_y, cb_w, parent_box, text_align
                )
                current_line_boxes.clear()
                current_line_width = 0.0
                current_line_ends_with_space = False

            word_box = TextBox(text_content=line, node=child.node)
            word_box.w = word_w
            word_box.h = get_line_height(family, size, fpdf_style)
            word_box.x = line_x + current_line_width
            word_box.y = 0.0  # Will be shifted

            current_line_width += word_w
            current_line_boxes.append((word_box, word_w, word_box.h))
    else:
        import re

        tokens = [t for t in re.split(r"(\s+)", content) if t]

        for token in tokens:
            if token.isspace():
                if current_line_width > 0 and not current_line_ends_with_space:
                    current_line_width += space_width
                    current_line_ends_with_space = True
                continue

            word_w = measure_text(token, family, size, fpdf_style)
            if current_line_width + word_w > cb_w and current_line_width > 0:
                consumed_h, current_y = _commit_line(
                    current_line_boxes, line_x, current_y, cb_w, parent_box, text_align
                )
                current_line_boxes.clear()
                current_line_width = 0.0
                current_line_ends_with_space = False

            word_box = TextBox(text_content=token, node=child.node)
            word_box.w = word_w
            word_box.h = get_line_height(family, size, fpdf_style)
            word_box.x = line_x + current_line_width
            word_box.y = 0.0  # Will be shifted

            current_line_width += word_w
            current_line_boxes.append((word_box, word_w, word_box.h))
            current_line_ends_with_space = False

    return current_y, current_line_width, current_line_ends_with_space


def _process_inline_box(
    child: Box,
    cb_w: float,
    line_x: float,
    current_y: float,
    current_line_width: float,
    current_line_boxes: list[tuple[Box, float, float]],
    parent_box: Box,
    text_align: str = "left",
) -> tuple[float, float, bool]:
    if child.__class__.__name__ == "InlineBlockBox":
        from pypdfpatra.engine.layout_block import layout_block_context

        child_style = getattr(child.node, "style", {})

        from pypdfpatra.engine.layout_block import _parse_length

        css_width = _parse_length(child_style.get("width", "auto"), cb_w, default_auto=None)
        if css_width is None:
            css_width = 150.0

        layout_block_context(child, 0.0, 0.0, css_width)

    elif child.__class__.__name__ == "ImageBox":
        child_style = getattr(child.node, "style", {})
        from pypdfpatra.engine.layout_block import _parse_length

        css_width = _parse_length(child_style.get("width", "auto"), cb_w, default_auto=None)
        css_height = _parse_length(child_style.get("height", "auto"), cb_w, default_auto=None)

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
        if child.w > cb_w and cb_w > 0:
            ratio = cb_w / child.w
            child.w = cb_w
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

    if current_line_width + child_total_w > cb_w and current_line_width > 0:
        consumed_h, current_y = _commit_line(
            current_line_boxes, line_x, current_y, cb_w, parent_box, text_align
        )
        current_line_boxes.clear()
        current_line_width = 0.0

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

    return current_y, current_line_width, False


def layout_inline_context(
    parent_box: Box, cb_x: float, cb_y: float, cb_w: float, text_align: str = "left"
) -> None:
    """
    Implements a basic W3C Inline Formatting Context (IFC).
    Takes a parent block box that contains inline-level children, and flows
    them horizontally into one or more Line Boxes.

    Args:
        parent_box: The BlockBox establishing the IFC. Its children will be wrapped in LineBoxes.
        cb_x: X coordinate of the content area.
        cb_y: Y coordinate of the content area starting point.
        cb_w: Available width for lines.
        text_align: Horizontal alignment for the generated line boxes.
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
    line_x = cb_x

    # Flow the inline children
    flat_children = _flatten_inline(inline_children)
    for child in flat_children:
        if isinstance(child, TextBox):
            current_y, current_line_width, current_line_ends_with_space = (
                _process_text_box(
                    child,
                    cb_w,
                    line_x,
                    current_y,
                    current_line_width,
                    current_line_ends_with_space,
                    current_line_boxes,
                    parent_box,
                    text_align,
                )
            )
        else:
            current_y, current_line_width, current_line_ends_with_space = (
                _process_inline_box(
                    child,
                    cb_w,
                    line_x,
                    current_y,
                    current_line_width,
                    current_line_boxes,
                    parent_box,
                    text_align,
                )
            )

    consumed_h, current_y = _commit_line(
        current_line_boxes, line_x, current_y, cb_w, parent_box, text_align
    )

    # The parent block box height expands to fit all the line boxes
    parent_box.h = max(0.0, current_y - cb_y)
