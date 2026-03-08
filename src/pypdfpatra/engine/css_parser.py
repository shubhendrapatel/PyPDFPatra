"""
pypdfpatra.engine.css_parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parses <style> blocks from the DOM into a list of tinycss2 AST rules.
"""

from typing import List
import tinycss2
from pypdfpatra.engine.tree import Node

__all__ = ["parse_stylesheets"]


import os
from pypdfpatra.engine.font_metrics import FontMetrics

def _extract_css_from_style_node(node: Node) -> str:
    """Recursively extract all text content from a <style> node."""
    css_text = []
    for child in node.children:
        if isinstance(child, Node) and child.tag == "#text":
            css_text.append(child.style.get("content", ""))
        elif isinstance(child, Node):
            css_text.append(_extract_css_from_style_node(child))
    return "".join(css_text)

def _find_css_sources(node: Node, css_sources: List[str], base_url: str) -> None:
    """Finds all <style> and <link> nodes in the DOM tree to extract CSS code."""
    if node.tag == "style":
        text = _extract_css_from_style_node(node)
        if text.strip():
            css_sources.append(text)
    elif node.tag == "link":
        rel = node.props.get("rel", "").lower()
        if rel == "stylesheet" and "href" in node.props:
            href = node.props["href"]
            if base_url and not href.startswith(("http://", "https://", "file://", "/")):
                asset_path = os.path.join(base_url, href)
            else:
                asset_path = href
            
            try:
                if os.path.exists(asset_path):
                    with open(asset_path, "r", encoding="utf-8") as f:
                        css_sources.append(f.read())
            except Exception as e:
                import logging
                logging.warning(f"Failed to load stylesheet {asset_path}: {e}")
                
    for child in node.children:
        if isinstance(child, Node):
            _find_css_sources(child, css_sources, base_url)

def _register_font_face(rule: tinycss2.ast.AtRule, base_url: str):
    """Extracts @font-face properties and registers the TTF to FontMetrics."""
    declarations = tinycss2.parse_declaration_list(rule.content, skip_whitespace=True, skip_comments=True)
    font_family = None
    font_weight = "normal"
    font_style = "normal"
    src_url = None
    
    for decl in declarations:
        if isinstance(decl, tinycss2.ast.Declaration):
            name = decl.name
            val = "".join([t.serialize() if hasattr(t, "serialize") else str(t.value) if hasattr(t, "value") else str(t) for t in decl.value]).strip()
            if name == "font-family":
                font_family = val.strip("\"'").replace(" ", "")
            elif name == "font-weight":
                font_weight = val
            elif name == "font-style":
                font_style = val
            elif name == "src":
                for token in decl.value:
                    if getattr(token, "type", "") == "url":
                        src_url = token.value
                        break
    
    if font_family and src_url:
        if base_url and not src_url.startswith(("http://", "https://", "file://", "/")):
             font_path = os.path.join(base_url, src_url)
        else:
             font_path = src_url
             
        if os.path.exists(font_path):
             fpdf_style = ""
             if str(font_weight) in ("bold", "700", "800", "900"):
                 fpdf_style += "B"
             if font_style == "italic":
                 fpdf_style += "I"
                 
             try:
                 FontMetrics.get_instance().register_font(font_family.lower(), fpdf_style, font_path)
             except Exception as e:
                 import logging
                 logging.warning(f"Failed to load custom font {font_family} from {font_path}: {e}")


def parse_stylesheets(root_node: Node, base_url: str = "") -> List[tinycss2.ast.Node]:
    """
    Finds CSS sources in the DOM, extracts text, handles @font-face loading,
    and parses them into tinycss2 AST rules for cascading.
    
    Args:
        root_node (Node): The root of the DOM tree.
        base_url (str): Absolute disk path for resolving external files.
        
    Returns:
        List[tinycss2.ast.Node]: Concatenated CSS rules list.
    """
    css_sources: List[str] = []
    _find_css_sources(root_node, css_sources, base_url)
    
    all_rules: List[tinycss2.ast.Node] = []
    
    for css_text in css_sources:
        rules = tinycss2.parse_stylesheet(
            css_text, skip_comments=True, skip_whitespace=True
        )
        
        # Extract custom font faces for Singleton FPDF measure registration
        for rule in rules:
            if isinstance(rule, tinycss2.ast.AtRule) and rule.lower_at_keyword == "font-face":
                _register_font_face(rule, base_url)
                
        all_rules.extend(rules)
            
    return all_rules
