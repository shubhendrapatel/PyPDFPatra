from pypdfpatra.engine.tree import Box, LineBox, TextBox
from pypdfpatra.engine.font_metrics import measure_text, get_line_height


def layout_inline_context(
    parent_box: Box, cb_x: float, cb_y: float, cb_w: float
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
    """
    inline_children = parent_box.children
    if not inline_children:
        return

    # Clear original children to replace them with LineBoxes
    parent_box.children = []

    current_line_boxes = []
    current_line_width = 0.0
    current_line_ends_with_space = False

    current_y = cb_y
    line_x = cb_x

    def commit_line():
        nonlocal current_y, current_line_boxes, current_line_width, current_line_ends_with_space

        if not current_line_boxes:
            return

        # Create the LineBox container
        line_box = LineBox(node=None)
        line_box.x = line_x
        line_box.y = current_y
        line_box.w = cb_w

        # Determine line height (max height of outer box dimensions)
        max_h = 0.0
        for item in current_line_boxes:
            child, outer_w, outer_h = item
            if outer_h > max_h:
                max_h = outer_h

        if max_h == 0:
            max_h = 20.0

        line_box.h = max_h

        def shift_box(b, dx, dy):
            b.x += dx
            b.y += dy
            for c in b.children:
                shift_box(c, dx, dy)

        # Center horizontally if needed. Right now, W3C aligned left.
        for item in current_line_boxes:
            child, outer_w, outer_h = item
            # Align bottom of outer box to bottom of line box
            target_outer_y = current_y + (max_h - outer_h)
            
            # target_outer_y is where the margin-top starts.
            target_content_y = target_outer_y + child.margin_top + child.border_top + child.padding_top
            
            dy = target_content_y - child.y
            shift_box(child, 0, dy)
            
            line_box.children.append(child)

        parent_box.children.append(line_box)
        current_y += max_h
        current_line_boxes.clear()
        current_line_width = 0.0
        current_line_ends_with_space = False

    def flatten_inline(boxes):
        flat = []
        for b in boxes:
            if isinstance(b, TextBox):
                flat.append(b)
            elif hasattr(b, "children") and b.__class__.__name__ == "InlineBox":
                flat.extend(flatten_inline(b.children))
            else:
                flat.append(b)
        return flat

    # Flow the inline children
    flat_children = flatten_inline(inline_children)
    for child in flat_children:
        if isinstance(child, TextBox):
            content = child.text_content
            if not content:
                continue

            style = getattr(child.node, "style", {}) if child.node else {}
            white_space = style.get("white-space", "normal")
            
            from pypdfpatra.engine.font_metrics import parse_font
            family, fpdf_style, size = parse_font(style)
            space_width = measure_text(" ", family, size, fpdf_style)

            if white_space == "pre":
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if i > 0:
                        commit_line()

                    if not line:
                        continue

                    word_w = measure_text(line, family, size, fpdf_style)
                    if current_line_width + word_w > cb_w and current_line_width > 0:
                        commit_line()

                    word_box = TextBox(text_content=line, node=child.node)
                    word_box.w = word_w
                    word_box.h = get_line_height(family, size, fpdf_style)
                    word_box.x = line_x + current_line_width
                    word_box.y = 0.0 # Will be shifted
                    
                    current_line_width += word_w
                    current_line_boxes.append((word_box, word_w, word_box.h))
            else:
                import re
                tokens = [t for t in re.split(r'(\s+)', content) if t]

                for token in tokens:
                    if token.isspace():
                        if current_line_width > 0 and not current_line_ends_with_space:
                            current_line_width += space_width
                            current_line_ends_with_space = True
                        continue

                    word_w = measure_text(token, family, size, fpdf_style)
                    if current_line_width + word_w > cb_w and current_line_width > 0:
                        commit_line()
                        current_line_ends_with_space = False

                    word_box = TextBox(text_content=token, node=child.node)
                    word_box.w = word_w
                    word_box.h = get_line_height(family, size, fpdf_style)
                    word_box.x = line_x + current_line_width
                    word_box.y = 0.0 # Will be shifted
                    
                    current_line_width += word_w
                    current_line_boxes.append((word_box, word_w, word_box.h))
                    current_line_ends_with_space = False

        else:
            if child.__class__.__name__ == "InlineBlockBox":
                from pypdfpatra.engine.layout_block import layout_block_context
                child_style = getattr(child.node, "style", {})
                
                from pypdfpatra.engine.layout_block import _parse_length
                css_width = _parse_length(child_style.get("width", "auto"), cb_w)
                if css_width <= 0:
                    css_width = 150.0
                
                layout_block_context(child, 0.0, 0.0, css_width)

            child_total_w = child.margin_left + child.border_left + child.padding_left + child.w + child.padding_right + child.border_right + child.margin_right
            child_total_h = child.margin_top + child.border_top + child.padding_top + child.h + child.padding_bottom + child.border_bottom + child.margin_bottom

            if current_line_width + child_total_w > cb_w and current_line_width > 0:
                commit_line()

            target_content_x = line_x + current_line_width + child.margin_left + child.border_left + child.padding_left
            dx = target_content_x - child.x
            
            def shift_box_hz(b, dx_hz):
                b.x += dx_hz
                for c in b.children:
                    shift_box_hz(c, dx_hz)
                    
            shift_box_hz(child, dx)

            current_line_width += child_total_w
            current_line_boxes.append((child, child_total_w, child_total_h))

    commit_line()

    # The parent block box height expands to fit all the line boxes
    parent_box.h = max(0.0, current_y - cb_y)
