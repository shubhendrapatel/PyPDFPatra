from pypdfpatra.api import build_tree
from pypdfpatra.matcher import apply_styles
from pypdfpatra.engine import resolve_styles, generate_box_tree, layout_block_context
from pypdfpatra.engine.tree import BlockBox

def test_margin_collapse():
    html_content = """
    <html>
    <body>
        <div style="background-color: #ff0000; width: 100px; height: 100px; margin-bottom: 50px;">
            <text>Box 1</text>
        </div>
        <div style="background-color: #00ff00; width: 100px; height: 100px; margin-top: 50px;">
            <text>Box 2</text>
        </div>
        
        <div style="background-color: #0000ff; width: 100px; height: 100px; margin-top: 100px;">
            <text>Box 3 (100px gap)</text>
        </div>
    </body>
    </html>
    """
    
    root_node = build_tree(html_content)
    rules = []
    apply_styles(root_node, rules)
    resolve_styles(root_node)
    root_box = generate_box_tree(root_node)
    layout_block_context(root_box, 0.0, 0.0, 500.0)
    
    body_box = root_box.children[0]
    
    div1 = body_box.children[0]
    div2 = body_box.children[1]
    div3 = body_box.children[2]
    
    assert isinstance(div1, BlockBox)
    
    # W3C math: box.y is margin box origin. Background starts at y + margin_top
    # Background ends at y + margin_top + padding_top + h + padding_bottom
    def get_bg_top(box):
        return box.y + box.margin_top
    
    def get_bg_bottom(box):
        return box.y + box.margin_top + box.padding_top + box.h + box.padding_bottom
        
    bottom_of_div1 = get_bg_bottom(div1)
    top_of_div2 = get_bg_top(div2)
    gap_1 = top_of_div2 - bottom_of_div1
    assert gap_1 == 50.0  # margin-bottom: 50px and margin-top: 50px collapses to 50px
    
    bottom_of_div2 = get_bg_bottom(div2)
    top_of_div3 = get_bg_top(div3)
    gap_2 = top_of_div3 - bottom_of_div2
    assert gap_2 == 100.0 # margin-bottom: 0px and margin-top: 100px collapses to 100px
