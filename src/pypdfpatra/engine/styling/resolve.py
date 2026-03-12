"""
pypdfpatra.engine.styling.resolve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
W3C-compliant CSS Object Model (CSSOM) style resolution step.

This module is responsible for traversing the DOM tree and computing the
final CSS property dictionary for every node. It handles:
1. User-Agent Default Styles (e.g., div -> display: block)
2. Inline styles (parsed from the DOM 'style' attribute)
3. CSS Inheritance (e.g., font-family inherits to children, but margin does not)
"""

from __future__ import annotations

from pypdfpatra.engine.tree import Node

from .shorthand import expand_shorthand_properties
from .user_agent import USER_AGENT_STYLES

# W3C Specification: Properties that automatically inherit to descendants
# if they are not explicitly overridden by the child.
INHERITED_PROPERTIES = frozenset(
    {
        "font-family",
        "font-size",
        "font-style",
        "font-weight",
        "line-height",
        "color",
        "text-align",
        "text-decoration",  # Cascaded in most renderers
        "visibility",
        "white-space",
        "list-style-type",
        "text-transform",
    }
)


def resolve_styles(node: Node, parent_style: dict = None) -> None:
    """
    Recursively computes the final CSS cascade for a single node and its children.
    Modifies the `node.style` dictionary in-place.

    Args:
        node: The DOM Node to process.
        parent_style: The computed style dictionary of the parent node.
    """
    if parent_style is None:
        parent_style = {}

    computed_style = {}

    # 1. Start with User-Agent defaults based on tag name
    tag = getattr(node, "tag", "").lower()
    ua_style = USER_AGENT_STYLES.get(tag, {})

    # Text nodes have no tag, but act as inline text
    if tag == "#text":
        ua_style = USER_AGENT_STYLES["#text"]

    # 2. Inherit properties from parent
    for prop in INHERITED_PROPERTIES:
        if prop in parent_style:
            computed_style[prop] = parent_style[prop]

    # 3. Apply UA default overrides
    for prop, val in ua_style.items():
        computed_style[prop] = val

    # 4. Apply explicit inline/matched styles on the node itself (highest priority)
    # The parser currently stores inline styles directly in `node.style`.
    for prop, val in node.style.items():
        if prop == "content":
            computed_style[prop] = val
        else:
            computed_style[prop] = val.strip()

    # 5. Handle "inherit" keyword (W3C specific feature)
    for prop, val in list(computed_style.items()):
        if str(val).lower() == "inherit" and prop in parent_style:
            computed_style[prop] = parent_style[prop]

    # 5.5 Expand all shorthands (e.g., margin -> margin-top, margin-bottom...)
    computed_style = expand_shorthand_properties(computed_style)

    # Assign finalized dict back to node
    node.style = computed_style

    # 6. Recurse to children
    for child in node.children:
        if isinstance(child, Node):
            resolve_styles(child, computed_style)

    return
