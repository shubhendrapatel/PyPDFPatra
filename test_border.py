from pypdfpatra.api import build_tree
from pypdfpatra.matcher import apply_styles
from pypdfpatra.engine import resolve_styles, generate_box_tree, layout_block_context, parse_stylesheets

html = """<html><body><style>.b { border: 4px solid #f0ad4e; margin: 10px; }</style><div class="b">Hello</div></body></html>"""

print("Running test...")
root_node = build_tree(html)
rules = parse_stylesheets(root_node)
apply_styles(root_node, rules)
resolve_styles(root_node)

def walk(node):
    if getattr(node, 'tag', '') == 'div':
        print("DIV STYLE:", node.style)
        box = generate_box_tree(node)
        layout_block_context(box, 0.0, 0.0, 500.0)
        print("BORDER TOP:", box.border_top)
    for c in node.children:
        if hasattr(c, 'children'):
            walk(c)

walk(root_node)
