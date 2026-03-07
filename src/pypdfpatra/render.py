"""
pypdfpatra.render
~~~~~~~~~~~~~~~~~
The rendering orchestrator that traverses the Cython layout tree and issues
drawing commands to a lightweight PDF backend (fpdf2).
"""

import fpdf
from pypdfpatra.engine.tree import Box, TextBox
from pypdfpatra.engine.font_metrics import parse_font


def _parse_color(color_str: str) -> tuple:
    """Parses a hex color string (e.g. '#ff0000') to an RGB tuple."""
    if not color_str:
        return (0, 0, 0)
    color_str = color_str.strip()
    if color_str.startswith("#"):
        try:
            if len(color_str) == 7:
                return (
                    int(color_str[1:3], 16),
                    int(color_str[3:5], 16),
                    int(color_str[5:7], 16),
                )
            elif len(color_str) == 4:
                return (
                    int(color_str[1] * 2, 16),
                    int(color_str[2] * 2, 16),
                    int(color_str[3] * 2, 16),
                )
        except ValueError:
            pass
    return (0, 0, 0)


PAGE_HEIGHT = 842.0


def _ensure_page(pdf: fpdf.FPDF, page_idx: int):
    """Ensures the PDF has enough pages to draw at the given 0-indexed page."""
    target_page = page_idx + 1
    while len(pdf.pages) < target_page:
        pdf.add_page()
    pdf.page = target_page


def draw_boxes(pdf: fpdf.FPDF, boxes: list[Box]):
    """
    Recursively iterates through the W3C Box Tree (Render Tree)
    and paints the boxes onto the PDF, slicing background shapes across
    multi-page boundaries mathematically.

    Args:
        pdf: The fpdf.FPDF context.
        boxes: List of Cython Box geometry models.
    """
    for box in boxes:
        if box is None:
            continue

        style = getattr(box.node, "style", {})

        # Using W3C model: box.x/y is margin origin, box.w/h is content box dimensions
        border_left = getattr(box, "border_left", 0)
        border_right = getattr(box, "border_right", 0)
        border_top = getattr(box, "border_top", 0)
        border_bottom = getattr(box, "border_bottom", 0)

        border_box_x = box.x + box.margin_left
        border_box_y = box.y + box.margin_top
        border_box_w = border_left + box.padding_left + box.w + box.padding_right + border_right
        border_box_h = border_top + box.padding_top + box.h + box.padding_bottom + border_bottom

        # Paint Backgrounds spanning multiple pages
        bg_color_str = style.get("background-color")
        if bg_color_str:
            r, g, b = _parse_color(bg_color_str)
            pdf.set_fill_color(r, g, b)
            
            start_page = int(border_box_y / PAGE_HEIGHT)
            end_page = int((border_box_y + border_box_h) / PAGE_HEIGHT)
            
            for p in range(start_page, end_page + 1):
                _ensure_page(pdf, p)
                
                local_y = border_box_y - (p * PAGE_HEIGHT)
                local_h = border_box_h
                
                if local_y < 0:
                    local_h += local_y
                    local_y = 0
                
                if local_y + local_h > PAGE_HEIGHT:
                    local_h = PAGE_HEIGHT - local_y
                    
                if local_h > 0:
                    pdf.rect(x=border_box_x, y=local_y, w=border_box_w, h=local_h, style="F")
            
            pdf.set_fill_color(0, 0, 0)
            
        # Draw Borders (MVP: Solid rectangles on the first page of the box)
        for edge, b_w, offset_x, offset_y, w, h in [
            ("top", border_top, border_box_x, border_box_y, border_box_w, border_top),
            ("bottom", border_bottom, border_box_x, border_box_y + border_box_h - border_bottom, border_box_w, border_bottom),
            ("left", border_left, border_box_x, border_box_y + border_top, border_left, border_box_h - border_top - border_bottom),
            ("right", border_right, border_box_x + border_box_w - border_right, border_box_y + border_top, border_right, border_box_h - border_top - border_bottom),
        ]:
            if b_w > 0 and style.get(f"border-{edge}-style", "solid") not in ("none", "hidden"):
                color_str = style.get(f"border-{edge}-color", style.get("border-color", "#000000"))
                r, g, b = _parse_color(color_str)
                pdf.set_fill_color(r, g, b)
                
                page_idx = int(offset_y / PAGE_HEIGHT)
                _ensure_page(pdf, page_idx)
                local_y = offset_y - (page_idx * PAGE_HEIGHT)
                if h > 0 and w > 0:
                    pdf.rect(x=offset_x, y=local_y, w=w, h=h, style="F")
                pdf.set_fill_color(0, 0, 0)

        # Paint Text Content on a specific page
        if isinstance(box, TextBox):
            text_content = box.text_content

            if text_content:
                content_x = border_box_x + border_left + box.padding_left
                content_y = border_box_y + border_top + box.padding_top
                
                page_idx = int(content_y / PAGE_HEIGHT)
                _ensure_page(pdf, page_idx)
                
                local_y = content_y - (page_idx * PAGE_HEIGHT)
                pdf.set_xy(content_x, local_y)
                
                family, fpdf_style, size = parse_font(style)
                pdf.set_font(family, style=fpdf_style, size=size)
                
                color_str = style.get("color", "#000000")
                r, g, b = _parse_color(color_str)
                # Force FPDF to emit the non-stroking color by invalidating its cache
                # because fill_color and text_color both use the same `rg` PDF operator.
                dummy_r = 1 if r == 0 else r - 1
                pdf.set_text_color(dummy_r, g, b)
                pdf.set_text_color(r, g, b)
                # Words are precisely positioned top-left by the IFC
                pdf.cell(w=box.w, h=box.h, text=text_content, align="L")

        # Paint children (Z-order: backgrounds, borders, then children)
        if box.children:
            draw_boxes(pdf, box.children)
