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
        # Backgrounds paint over the padding and border box.
        padding_x = box.x + box.margin_left
        padding_y = box.y + box.margin_top
        padding_w = box.padding_left + box.w + box.padding_right
        padding_h = box.padding_top + box.h + box.padding_bottom

        # Paint Backgrounds spanning multiple pages
        bg_color_str = style.get("background-color")
        if bg_color_str:
            r, g, b = _parse_color(bg_color_str)
            pdf.set_fill_color(r, g, b)
            
            start_page = int(padding_y / PAGE_HEIGHT)
            end_page = int((padding_y + padding_h) / PAGE_HEIGHT)
            
            for p in range(start_page, end_page + 1):
                _ensure_page(pdf, p)
                
                local_y = padding_y - (p * PAGE_HEIGHT)
                local_h = padding_h
                
                # Clip top if it bleeds from a previous page
                if local_y < 0:
                    local_h += local_y
                    local_y = 0
                
                # Clip bottom if it bleeds into the next page
                if local_y + local_h > PAGE_HEIGHT:
                    local_h = PAGE_HEIGHT - local_y
                    
                if local_h > 0:
                    pdf.rect(x=padding_x, y=local_y, w=padding_w, h=local_h, style="F")
            
            # CRITICAL FIX: Reset fill color to prevent black bleeding
            pdf.set_fill_color(0, 0, 0)

        # Paint Text Content on a specific page
        if isinstance(box, TextBox):
            text_content = box.text_content

            if text_content:
                content_x = padding_x + box.padding_left
                content_y = padding_y + box.padding_top
                
                page_idx = int(content_y / PAGE_HEIGHT)
                _ensure_page(pdf, page_idx)
                
                local_y = content_y - (page_idx * PAGE_HEIGHT)
                pdf.set_xy(content_x, local_y)
                
                family, fpdf_style, size = parse_font(style)
                pdf.set_font(family, style=fpdf_style, size=size)
                
                color_str = style.get("color", "#000000")
                r, g, b = _parse_color(color_str)
                pdf.set_text_color(r, g, b)
                # Words are precisely positioned top-left by the IFC
                pdf.cell(w=box.w, h=box.h, text=text_content, align="L")

        # Paint children (Z-order: backgrounds, borders, then children)
        if box.children:
            draw_boxes(pdf, box.children)
