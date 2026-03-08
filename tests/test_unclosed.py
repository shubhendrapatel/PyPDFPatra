from pypdfpatra.api import build_tree


def test_unclosed_tags():
    html = "<html><body><h1>Parse me!"
    root_node = build_tree(html)

    assert root_node.tag == "html"
    assert len(root_node.children) == 1

    body_node = root_node.children[0]
    assert body_node.tag == "body"
    assert len(body_node.children) == 1

    h1_node = body_node.children[0]
    assert h1_node.tag == "h1"
    assert len(h1_node.children) == 1

    text_node = h1_node.children[0]
    assert text_node.tag == "#text"
    assert text_node.style["content"] == "Parse me!"
