
from pypdfpatra.api import build_tree
from pypdfpatra.defaults import CONTENT_WIDTH, DEFAULT_MARGIN_LEFT, DEFAULT_MARGIN_TOP
from pypdfpatra.engine import (
    apply_styles,
    generate_box_tree,
    layout_block_context,
    parse_stylesheets,
    resolve_styles,
)


def test_absolute_containing_block():
    html_content = """
    <html>
    <head>
        <style>
            .relative-root {
                position: relative;
                width: 400px;
                height: 400px;
                border: 2px solid blue;
                margin: 10px;
                padding: 10px;
                background-color: #f0f0ff;
            }
            .static-child {
                position: static;
                margin: 10px;
                padding: 10px;
                border: 1px solid gray;
                background-color: #f0f0f0;
            }
            .absolute-box {
                position: absolute;
                top: 0;
                left: 0;
                width: 50px;
                height: 50px;
                background-color: red;
            }
        </style>
    </head>
    <body>
        <div class="relative-root">
            Relative Root
            <div class="static-child">
                Static Child
                <div class="absolute-box">Abs</div>
            </div>
        </div>
    </body>
    </html>
    """

    # Defaults in pypdfpatra:
    # DEFAULT_MARGIN_LEFT = 36.0
    # DEFAULT_MARGIN_TOP = 36.0

    root_node = build_tree(html_content)
    rules = parse_stylesheets(root_node, "")
    apply_styles(root_node, rules)
    resolve_styles(root_node)
    root_box = generate_box_tree(root_node, "")

    if root_box is not None:
        layout_block_context(
            root_box, DEFAULT_MARGIN_LEFT, DEFAULT_MARGIN_TOP, CONTENT_WIDTH
        )

    def find_abs_box(box):
        if getattr(box, 'position', None) == 'absolute':
            return box
        for child in getattr(box, 'children', []):
            found = find_abs_box(child)
            if found:
                return found
        return None

    abs_box = find_abs_box(root_box)
    if abs_box:
        print(f"Absolute Box Position: x={abs_box.x}, y={abs_box.y}")
        # Expected if relative-root is containing block:
        # relative-root (margin 10) starting inside page margin (36, 36)
        # relative-root border-box starts at (36+0, 36+0) = (36, 36) -- Wait, layout_block_context(root_box, ml, mt, cw)
        # root_box.x = 36, root_box.y = 36.
        # relative-root is a child.
        # body.x = 36 + body.margin_left...

        # Let's find relative-root
        def find_box_by_class(box, class_name):
            style = getattr(box.node, 'style', {})
            if style.get('class') == class_name: # Node classes are stored differently?
                return box
            # Check node props
            if getattr(box.node, 'props', {}).get('class') == class_name:
                return box
            for child in getattr(box, 'children', []):
                found = find_box_by_class(child, class_name)
                if found:
                    return found
            return None

        rel_root = find_box_by_class(root_box, "relative-root")
        if rel_root:
            # Padding box of relative-root:
            px = rel_root.x + rel_root.margin_left + rel_root.border_left
            py = rel_root.y + rel_root.margin_top + rel_root.border_top
            print(f"Relative Root Padding Box: x={px}, y={py}")

            if abs_box.x == px and abs_box.y == py:
                print("SUCCESS: Absolute box is correctly positioned relative to the nearest positioned ancestor.")
            else:
                print("FAILURE: Absolute box is WRONGLY positioned relative to something else (probably parent).")
        else:
            print("Relative Root not found!")
    else:
        print("Absolute Box not found in tree!")

if __name__ == "__main__":
    test_absolute_containing_block()
