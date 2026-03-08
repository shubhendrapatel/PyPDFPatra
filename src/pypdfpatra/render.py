"""
pypdfpatra.render
~~~~~~~~~~~~~~~~~
The rendering orchestrator that traverses the Cython layout tree and issues
drawing commands to a lightweight PDF backend (fpdf2).
"""

import fpdf
from pypdfpatra.engine.tree import Box, TextBox
from pypdfpatra.engine.font_metrics import parse_font


NAMED_COLORS = {
    "aliceblue": (240, 248, 255),
    "antiquewhite": (250, 235, 215),
    "aqua": (0, 255, 255),
    "aquamarine": (127, 255, 212),
    "azure": (240, 255, 255),
    "beige": (245, 245, 220),
    "bisque": (255, 228, 196),
    "black": (0, 0, 0),
    "blanchedalmond": (255, 235, 205),
    "blue": (0, 0, 255),
    "blueviolet": (138, 43, 226),
    "brown": (165, 42, 42),
    "burlywood": (222, 184, 135),
    "cadetblue": (95, 158, 160),
    "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30),
    "coral": (255, 127, 80),
    "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220),
    "crimson": (220, 20, 60),
    "cyan": (0, 255, 255),
    "darkblue": (0, 0, 139),
    "darkcyan": (0, 139, 139),
    "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169),
    "darkgreen": (0, 100, 0),
    "darkgrey": (169, 169, 169),
    "darkkhaki": (189, 183, 107),
    "darkmagenta": (139, 0, 139),
    "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0),
    "darkorchid": (153, 50, 204),
    "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122),
    "darkseagreen": (143, 188, 143),
    "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79),
    "darkslategrey": (47, 79, 79),
    "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211),
    "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105),
    "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34),
    "floralwhite": (255, 250, 240),
    "forestgreen": (34, 139, 34),
    "fuchsia": (255, 0, 255),
    "gainsboro": (220, 220, 220),
    "ghostwhite": (248, 248, 255),
    "goldenrod": (218, 165, 32),
    "gold": (255, 215, 0),
    "gray": (128, 128, 128),
    "green": (0, 128, 0),
    "greenyellow": (173, 255, 47),
    "grey": (128, 128, 128),
    "honeydew": (240, 255, 240),
    "hotpink": (255, 105, 180),
    "indianred": (205, 92, 92),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavenderblush": (255, 240, 245),
    "lavender": (230, 230, 250),
    "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205),
    "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightgrey": (211, 211, 211),
    "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122),
    "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224),
    "lime": (0, 255, 0),
    "limegreen": (50, 205, 50),
    "linen": (250, 240, 230),
    "magenta": (255, 0, 255),
    "maroon": (128, 0, 0),
    "mediumaquamarine": (102, 205, 170),
    "mediumblue": (0, 0, 205),
    "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219),
    "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204),
    "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112),
    "mintcream": (245, 255, 250),
    "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181),
    "navajowhite": (255, 222, 173),
    "navy": (0, 0, 128),
    "oldlace": (253, 245, 230),
    "olive": (128, 128, 0),
    "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0),
    "orangered": (255, 69, 0),
    "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170),
    "palegreen": (152, 251, 152),
    "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147),
    "papayawhip": (255, 239, 213),
    "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63),
    "pink": (255, 192, 203),
    "plum": (221, 160, 221),
    "powderblue": (176, 224, 230),
    "purple": (128, 0, 128),
    "rebeccapurple": (102, 51, 153),
    "red": (255, 0, 0),
    "rosybrown": (188, 143, 143),
    "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19),
    "salmon": (250, 128, 114),
    "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87),
    "seashell": (255, 245, 238),
    "sienna": (160, 82, 45),
    "silver": (192, 192, 192),
    "skyblue": (135, 206, 235),
    "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144),
    "slategrey": (112, 128, 144),
    "snow": (255, 250, 250),
    "springgreen": (0, 255, 127),
    "steelblue": (70, 130, 180),
    "tan": (210, 180, 140),
    "teal": (0, 128, 128),
    "thistle": (216, 191, 216),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
    "white": (255, 255, 255),
    "whitesmoke": (245, 245, 245),
    "yellow": (255, 255, 0),
    "yellowgreen": (154, 205, 50),
}


def _parse_color(color_str: str) -> tuple:
    """Parses a hex color string or common named color to an RGB tuple."""
    if not color_str:
        return (0, 0, 0)
    color_str = color_str.strip().lower()

    if color_str in NAMED_COLORS:
        return NAMED_COLORS[color_str]

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


def _draw_background(
    pdf: fpdf.FPDF,
    style: dict,
    border_box_x: float,
    border_box_y: float,
    border_box_w: float,
    border_box_h: float,
) -> None:
    """Paints background colors across potentially multiple pages."""
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
) -> None:
    """Paints element borders, adding basic 3D shadow effects for inset/outset rules."""
    for edge, b_w, offset_x, offset_y, w, h in [
        ("top", border_top, border_box_x, border_box_y, border_box_w, border_top),
        (
            "bottom",
            border_bottom,
            border_box_x,
            border_box_y + border_box_h - border_bottom,
            border_box_w,
            border_bottom,
        ),
        (
            "left",
            border_left,
            border_box_x,
            border_box_y + border_top,
            border_left,
            border_box_h - border_top - border_bottom,
        ),
        (
            "right",
            border_right,
            border_box_x + border_box_w - border_right,
            border_box_y + border_top,
            border_right,
            border_box_h - border_top - border_bottom,
        ),
    ]:
        border_style = style.get(
            f"border-{edge}-style", style.get("border-style", "solid")
        )
        if b_w > 0 and border_style not in ("none", "hidden"):
            color_str = style.get(
                f"border-{edge}-color", style.get("border-color", "#000000")
            )
            r, g, b = _parse_color(color_str)

            # Basic 3D effect for inset/outset
            if border_style == "outset":
                if edge in ("top", "left"):
                    r, g, b = min(255, r + 40), min(255, g + 40), min(255, b + 40)
                else:
                    r, g, b = max(0, r - 40), max(0, g - 40), max(0, b - 40)
            elif border_style == "inset":
                if edge in ("top", "left"):
                    r, g, b = max(0, r - 40), max(0, g - 40), max(0, b - 40)
                else:
                    r, g, b = min(255, r + 40), min(255, g + 40), min(255, b + 40)

            pdf.set_fill_color(r, g, b)

            page_idx = int(offset_y / PAGE_HEIGHT)
            _ensure_page(pdf, page_idx)
            local_y = offset_y - (page_idx * PAGE_HEIGHT)
            if h > 0 and w > 0:
                pdf.rect(x=offset_x, y=local_y, w=w, h=h, style="F")
            pdf.set_fill_color(0, 0, 0)


def _draw_text(
    pdf: fpdf.FPDF,
    box: TextBox,
    style: dict,
    border_box_x: float,
    border_box_y: float,
    border_top: float,
    border_left: float,
) -> None:
    """Paints correctly formatted and styled inline text primitives or vector list markers."""
    text_content = box.text_content
    if not text_content:
        return

    content_x = border_box_x + border_left + box.padding_left
    content_y = border_box_y + border_top + box.padding_top

    page_idx = int(content_y / PAGE_HEIGHT)
    _ensure_page(pdf, page_idx)

    local_y = content_y - (page_idx * PAGE_HEIGHT)

    color_str = style.get("color", "#000000")
    r, g, b = _parse_color(color_str)

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

    from pypdfpatra.engine.font_metrics import FontMetrics

    FontMetrics.get_instance().set_font_safe(pdf, family, size, fpdf_style)

    # Force FPDF to emit the non-stroking color by invalidating its cache
    # because fill_color and text_color both use the same `rg` PDF operator.
    dummy_r = 1 if r == 0 else r - 1
    pdf.set_text_color(dummy_r, g, b)
    pdf.set_text_color(r, g, b)
    # Words are precisely positioned top-left by the IFC

    # Thanks to true TTF support via @font-face, Unicode renders natively!
    pdf.cell(w=box.w, h=box.h, text=text_content, align="L")


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
        border_box_w = (
            border_left + box.padding_left + box.w + box.padding_right + border_right
        )
        border_box_h = (
            border_top + box.padding_top + box.h + box.padding_bottom + border_bottom
        )

        # Paint Backgrounds spanning multiple pages
        _draw_background(
            pdf, style, border_box_x, border_box_y, border_box_w, border_box_h
        )

        # Draw Borders
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
        )

        # Paint Text Content
        if isinstance(box, TextBox) or box.__class__.__name__ == "MarkerBox":
            _draw_text(
                pdf, box, style, border_box_x, border_box_y, border_top, border_left
            )

        # Paint children (Z-order: backgrounds, borders, then children)
        if box.children:
            draw_boxes(pdf, box.children)
