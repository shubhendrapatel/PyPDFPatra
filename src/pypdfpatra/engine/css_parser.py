"""
pypdfpatra.engine.css_parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parses <style> blocks from the DOM into a list of tinycss2 AST rules.
"""

from typing import List
import tinycss2
from pypdfpatra.engine.tree import Node

__all__ = ["parse_stylesheets"]


def _extract_css_from_style_node(node: Node) -> str:
    """Recursively extract all text content from a <style> node."""
    css_text = []
    for child in node.children:
        if isinstance(child, Node) and child.tag == "#text":
            css_text.append(child.style.get("content", ""))
        elif isinstance(child, Node):
            css_text.append(_extract_css_from_style_node(child))
    return "".join(css_text)


def _find_style_nodes(node: Node, style_nodes: List[Node]) -> None:
    """Finds all <style> nodes in the DOM tree."""
    if node.tag == "style":
        style_nodes.append(node)
    
    for child in node.children:
        if isinstance(child, Node):
            _find_style_nodes(child, style_nodes)


def parse_stylesheets(root_node: Node) -> List[tinycss2.ast.Node]:
    """
    Finds all <style> nodes in the DOM, extracts their CSS text,
    and parses them into tinycss2 AST rules.
    
    Args:
        root_node (Node): The root of the DOM tree.
        
    Returns:
        List[tinycss2.ast.Node]: A concatenated list of all parsed CSS rules.
    """
    style_nodes: List[Node] = []
    _find_style_nodes(root_node, style_nodes)
    
    all_rules: List[tinycss2.ast.Node] = []
    
    for style_node in style_nodes:
        css_text = _extract_css_from_style_node(style_node)
        if css_text.strip():
            rules = tinycss2.parse_stylesheet(
                css_text, skip_comments=True, skip_whitespace=True
            )
            all_rules.extend(rules)
            
    return all_rules
