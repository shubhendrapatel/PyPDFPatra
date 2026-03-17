import pypdfpatra.render as render
from pypdfpatra.api import build_tree
from pypdfpatra.engine import (
    apply_styles,
    generate_box_tree,
    layout_block_context,
    parse_stylesheets,
    resolve_styles,
)


class DummyPDF:
    def __init__(self):
        self.pages = []
        self.page = 0
        self.y = 0

    def add_link(self):
        return 0

    def set_link(self, *args, **kwargs):
        pass

    def add_page(self):
        self.pages.append(None)

    def set_fill_color(self, *args, **kwargs):
        pass

    def rect(self, *args, **kwargs):
        pass

    def _out(self, *args, **kwargs):
        pass

    def set_draw_color(self, *args, **kwargs):
        pass

    def set_line_width(self, *args, **kwargs):
        pass

    def line(self, *args, **kwargs):
        pass

    def set_xy(self, *args, **kwargs):
        pass

    def set_text_color(self, *args, **kwargs):
        pass

    def cell(self, *args, **kwargs):
        pass

    def link(self, *args, **kwargs):
        pass

    def start_section(self, *args, **kwargs):
        pass

    def set_font(self, *args, **kwargs):
        pass

    def ellipse(self, *args, **kwargs):
        pass

    def image(self, *args, **kwargs):
        pass

    def set_dash_pattern(self, *args, **kwargs):
        pass


def test_stacking_order():
    print("DEBUG: entering test_stacking_order")
    html_content = """
    <html>
    <body style="margin: 0; padding: 0;">
        <div class="positioned" style="position: relative; top: 50px; left: 50px; width: 100px; height: 100px; background-color: blue;">Pos</div>
        <div class="static" style="width: 100px; height: 100px; margin-top: -50px; background-color: red;">Static</div>
    </body>
    </html>
    """
    print("DEBUG: HTML content defined")

    root_node = build_tree(html_content)
    rules = parse_stylesheets(root_node, "")
    apply_styles(root_node, rules)
    resolve_styles(root_node)
    root_box = generate_box_tree(root_node, "")
    layout_block_context(root_box, 0, 0, 1000)
    print("DEBUG: after layout")

    body_box = root_box.children[0]
    boxes = body_box.children

    pdf = DummyPDF()
    print("DEBUG: after DummyPDF creation")
    original_draw_bg = render._draw_background
    order = []

    def mocked_draw_bg(pdf, style, x, y, w, h):
        bg = style.get("background-color")
        if bg in ("blue", "red"):
            order.append(bg)

    render._draw_background = mocked_draw_bg
    try:
        render.draw_boxes(pdf, boxes)
    finally:
        render._draw_background = original_draw_bg

    print(f"Paint Order (by background color): {order}")

    if order == ["red", "blue"]:
        print("SUCCESS: Positioned box is on top (paints last).")
    else:
        print(f"FAILURE: Incorrect paint order: {order}")


if __name__ == "__main__":
    test_stacking_order()
