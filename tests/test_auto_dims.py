
from pypdfpatra.api import build_tree
from pypdfpatra.engine import (
    apply_styles,
    generate_box_tree,
    layout_block_context,
    parse_stylesheets,
    resolve_styles,
)


def test_auto_dimensions():
    html_content = """
    <html>
    <head>
        <style>
            .container {
                position: relative;
                width: 400px;
                height: 400px;
                border: 1px solid black;
            }
            .abs-stretched {
                position: absolute;
                top: 10px;
                bottom: 20px;
                left: 30px;
                right: 40px;
                background-color: red;
            }
        </style>
    </head>
    <body style="margin: 0; padding: 0;">
        <div class="container">
            <div class="abs-stretched">Stretched</div>
        </div>
    </body>
    </html>
    """

    root_node = build_tree(html_content)
    rules = parse_stylesheets(root_node, "")
    apply_styles(root_node, rules)
    resolve_styles(root_node)
    root_box = generate_box_tree(root_node, "")

    if root_box is not None:
        layout_block_context(
            root_box, 0, 0, 1000 # Large enough
        )

    def find_box_by_class(box, class_name):
        if getattr(box.node, 'props', {}).get('class') == class_name:
            return box
        for child in getattr(box, 'children', []):
            found = find_box_by_class(child, class_name)
            if found:
                return found
        return None

    stretched = find_box_by_class(root_box, "abs-stretched")
    if stretched:
        print(f"Stretched Box: x={stretched.x}, y={stretched.y}, w={stretched.w}, h={stretched.h}")
        # Container is 400x400.
        # top: 10, bottom: 20 -> Height should be 400 - 10 - 20 = 370.
        # left: 30, right: 40 -> Width should be 400 - 30 - 40 = 330.

        expected_w = 400 - 30 - 40
        expected_h = 400 - 10 - 20

        if stretched.w == expected_w and stretched.h == expected_h:
            print("SUCCESS: Absolute box auto-dimensions based on offsets are correct.")
        else:
            print(f"FAILURE: Absolute box auto-dimensions are WRONG. Expected w={expected_w}, h={expected_h}")
    else:
        print("Stretched Box not found!")

if __name__ == "__main__":
    test_auto_dimensions()
