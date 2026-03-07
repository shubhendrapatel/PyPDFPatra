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

        # Determine line height (max height of contents)
        max_h = 0.0
        for child in current_line_boxes:
            if child.h > max_h:
                max_h = child.h

        if max_h == 0:
            # Fallback for empty lines
            max_h = 20.0

        line_box.h = max_h

        # Center horizontally if needed, or just left-align (default W3C is left-aligned)
        # For each child, their 'y' is currently relative to the line box top.
        for child in current_line_boxes:
            # Simple baseline alignment: align to bottom of line box
            child.y = current_y + (max_h - child.h)
            line_box.children.append(child)

        parent_box.children.append(line_box)

        # Advance Y for next line
        current_y += max_h

        # Reset for next line
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
            
            # Evaluate font properties specifically for this child text node
            from pypdfpatra.engine.font_metrics import parse_font
            family, fpdf_style, size = parse_font(style)
            space_width = measure_text(" ", family, size, fpdf_style)

            if white_space == "pre":
                # Preserve exact formatting (newlines break lines, spaces are measured exactly)
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if i > 0:
                        commit_line()  # Hard break for newline

                    if not line:
                        continue

                    word_w = measure_text(line, family, size, fpdf_style)
                    
                    if current_line_width + word_w > cb_w and current_line_width > 0:
                        commit_line()

                    word_box = TextBox(text_content=line, node=child.node)
                    word_box.w = word_w
                    word_box.h = get_line_height(family, size, fpdf_style)
                    word_box.x = line_x + current_line_width
                    
                    current_line_width += word_w
                    current_line_boxes.append(word_box)
            else:
                # Normal word wrapping
                import re
                tokens = [t for t in re.split(r'(\s+)', content) if t]

                for token in tokens:
                    if token.isspace():
                        # Only inject a space width if we aren't at the start of a line
                        # and haven't already added a space just before this.
                        if current_line_width > 0 and not current_line_ends_with_space:
                            current_line_width += space_width
                            current_line_ends_with_space = True
                        continue

                    word_w = measure_text(token, family, size, fpdf_style)

                    # If word exceeds available width on current line, wrap it
                    if current_line_width + word_w > cb_w and current_line_width > 0:
                        commit_line()
                        current_line_ends_with_space = False

                    # Create a fragment box for this specific word
                    word_box = TextBox(text_content=token, node=child.node)
                    word_box.w = word_w
                    word_box.h = get_line_height(family, size, fpdf_style)

                    # Position horizontally within the line
                    word_box.x = line_x + current_line_width

                    current_line_width += word_w
                    current_line_boxes.append(word_box)
                    current_line_ends_with_space = False

        else:
            # For non-text inline blocks (like empty spans or images later)
            # We treat them as indivisible inline blocks
            if current_line_width + child.w > cb_w and current_line_width > 0:
                commit_line()

            child.x = line_x + current_line_width
            current_line_width += child.w
            current_line_boxes.append(child)

    # Commit any remaining boxes
    commit_line()

    # The parent block box height expands to fit all the line boxes
    parent_box.h = max(0.0, current_y - cb_y)
