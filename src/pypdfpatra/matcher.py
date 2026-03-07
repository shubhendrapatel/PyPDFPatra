"""
pypdfpatra.matcher
~~~~~~~~~~~~~~~~~~
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

    This function traverses the DOM tree and applies styles from the parsed CSS
    rules to each `Node` where the selector matches. Currently, it implements
    a basic tag-name matching strategy.

    Args:
        node (Node): The Cython Node to evaluate and style.
        rules (List[tinycss2.ast.Node]): A list of parsed CSS rules from tinycss2.
    """
    # 1. Match Rules to this specific Node
    for rule in rules:
        # Check if the rule is a 'Qualified Rule' (has a selector and declarations)
        if isinstance(rule, tinycss2.ast.QualifiedRule):
            # Convert the selector tokens to a string (e.g. ['div'] -> 'div')
            selector = "".join([t.value for t in rule.prelude if hasattr(t, "value")])

            # Simple Matcher: Check if tag name matches selector
            if selector.strip() == node.tag:
                _inject_declarations(node, rule.content)

    # 1.5. Apply Inline Styles (e.g. <div style="...">)
    inline_style_str = node.props.get("style")
    if inline_style_str:
        # tinycss2 parses declaration lists directly
        inline_declarations = tinycss2.parse_declaration_list(
            inline_style_str, skip_comments=True, skip_whitespace=True
        )
        # We can bypass _inject_declarations logic slightly, or just pass the parsed nodes
        # wait, tinycss2.parse_declaration_list takes a string or tokens. If string, it returns Declaration objects directly.
        for decl in inline_declarations:
            if isinstance(decl, tinycss2.ast.Declaration):
                node.style[decl.name] = "".join(
                    [
                        str(t.value) if hasattr(t, "value") else str(t)
                        for t in decl.value
                    ]
                )

    # 2. Recursively apply to all children in the tree
    for child in node.children:
        apply_styles(child, rules)


def _inject_declarations(node: Node, content: List[tinycss2.ast.Node]) -> None:
    """
    Parses CSS declarations and stores them in the Node's Cython style dictionary.

    Example: 'color: red' -> node.style['color'] = 'red'

    Args:
        node (Node): The node whose style dictionary should be updated.
        content (List[tinycss2.ast.Node]): The token list forming the declaration
            block to parse.
    """
    declarations = tinycss2.parse_declaration_list(content)
    for decl in declarations:
        if isinstance(decl, tinycss2.ast.Declaration):
            # Store the property and its value in the high-speed Node.style
            # Convert all values to strings to handle both string and numeric tokens
            node.style[decl.name] = "".join(
                [str(t.value) if hasattr(t, "value") else str(t) for t in decl.value]
            )
