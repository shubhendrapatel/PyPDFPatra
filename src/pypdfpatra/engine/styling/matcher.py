"""
pypdfpatra.engine.styling.matcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module handles the CSS 'Cascade'. It matches CSS selectors
(like .class or #id) to the Cython Nodes in the tree.
"""

from typing import List
import tinycss2
from pypdfpatra.engine.tree import Node

__all__ = ["apply_styles"]


def apply_styles(node: Node, rules: List[tinycss2.ast.Node]) -> None:
    """
    Recursively matches CSS rules to a Node and its children.
    """
    # 1. Match Rules to this specific Node
    for rule in rules:
        # Check if the rule is a 'Qualified Rule' (has a selector and declarations)
        if isinstance(rule, tinycss2.ast.QualifiedRule):
            # Convert the selector tokens to a string (e.g. ['div'], ['.', 'custom-box'])
            selector = "".join(
                [
                    t.serialize()
                    if hasattr(t, "serialize")
                    else str(t.value)
                    if hasattr(t, "value")
                    else str(t)
                    for t in rule.prelude
                ]
            ).strip()

            matched = False
            # 1. ID Matcher (#my-id)
            if selector.startswith("#"):
                target_id = selector[1:]
                if node.props.get("id") == target_id:
                    matched = True
            # 2. Class Matcher (.my-class)
            elif selector.startswith("."):
                target_class = selector[1:]
                # Handle multiple classes (e.g., class="btn primary")
                node_classes = node.props.get("class", "").split()
                if target_class in node_classes:
                    matched = True
            # 3. Simple Tag Matcher (div)
            else:
                if selector == node.tag:
                    matched = True

            if matched:
                _inject_declarations(node, rule.content)

    # 1.5. Apply Inline Styles (e.g. <div style="...">)
    inline_style_str = node.props.get("style")
    if inline_style_str:
        # tinycss2 parses declaration lists directly
        inline_declarations = tinycss2.parse_declaration_list(
            inline_style_str, skip_comments=True, skip_whitespace=True
        )
        for decl in inline_declarations:
            if isinstance(decl, tinycss2.ast.Declaration):
                node.style[decl.name] = "".join(
                    [
                        t.serialize()
                        if hasattr(t, "serialize")
                        else str(t.value)
                        if hasattr(t, "value")
                        else str(t)
                        for t in decl.value
                    ]
                )

    # 2. Recursively apply to all children in the tree
    for child in node.children:
        apply_styles(child, rules)


def _inject_declarations(node: Node, content: List[tinycss2.ast.Node]) -> None:
    """
    Parses CSS declarations and stores them in the Node's Cython style dictionary.
    """
    declarations = tinycss2.parse_declaration_list(content)
    for decl in declarations:
        if isinstance(decl, tinycss2.ast.Declaration):
            node.style[decl.name] = "".join(
                [
                    t.serialize()
                    if hasattr(t, "serialize")
                    else str(t.value)
                    if hasattr(t, "value")
                    else str(t)
                    for t in decl.value
                ]
            ).strip()
