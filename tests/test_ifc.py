from pypdfpatra.api import build_tree
from pypdfpatra.matcher import apply_styles
from pypdfpatra.engine import resolve_styles, generate_box_tree, layout_block_context
from pypdfpatra.engine.tree import BlockBox, AnonymousBlockBox, LineBox


def test_ifc_line_breaking():
    html_content = """
    <html>
    <body>
        <div style="background-color: #f0f0f0; width: 300px; padding: 20px;">
            <text>
                This is a very long paragraph of text that should automatically wrap 
                when it hits the edge of its 300px container. If the Inline Formatting 
                Context (IFC) is working correctly, this text will flow naturally across 
                multiple lines, generating precise W3C Line Boxes for each horizontal block. 
                Line breaking is famously difficult to write from scratch, so let's hope 
                our implementation is robust enough to handle this!
            </text>
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

    # root -> body -> div
    body_box = root_box.children[0]
    div_box = body_box.children[0]

    assert isinstance(div_box, BlockBox)
    assert div_box.w == 300.0  # Content width

    # the text should be wrapped in an AnonymousBlockBox
    anon_block = div_box.children[0]
    assert isinstance(anon_block, AnonymousBlockBox)

    # IFC should have created multiple LineBoxes
    assert len(anon_block.children) > 1

    for line_box in anon_block.children:
        assert isinstance(line_box, LineBox)
        assert line_box.w == 300.0
