"""
pypdfpatra.engine.style
~~~~~~~~~~~~~~~~~~~~~~~
W3C-compliant CSS Object Model (CSSOM) style resolution step.

This module is responsible for traversing the DOM tree and computing the
final CSS property dictionary for every node. It handles:
1. User-Agent Default Styles (e.g., div -> display: block)
2. Inline styles (parsed from the DOM 'style' attribute)
3. CSS Inheritance (e.g., font-family inherits to children, but margin does not)
"""

from __future__ import annotations
from pypdfpatra.engine.tree import Node

# W3C Specification / HTML5 Standard: Default User-Agent style sheets.
# PyPDFPatra follows the WebKit/Chrome industry-standard default stylesheet
# to ensure HTML renders exactly as users expect it to in a modern browser.
USER_AGENT_STYLES = {
    # Non-rendered elements
    "head": {"display": "none"},
    "style": {"display": "none"},
    "script": {"display": "none"},
    "title": {"display": "none"},
    "meta": {"display": "none"},
    "link": {"display": "none"},
    "param": {"display": "none"},
    # Block formatting defaults
    "html": {"display": "block"},
    "body": {"display": "block", "margin": "8px"},
    "div": {"display": "block"},
    "p": {"display": "block", "margin-top": "1em", "margin-bottom": "1em"},
    "blockquote": {
        "display": "block",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "margin-left": "40px",
        "margin-right": "40px",
    },
    "figure": {
        "display": "block",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "margin-left": "40px",
        "margin-right": "40px",
    },
    "pre": {
        "display": "block",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "font-family": "monospace",
        "white-space": "pre",
    },
    "hr": {"display": "block", "margin-top": "0.5em", "margin-bottom": "0.5em"},
    # Headings
    "h1": {
        "display": "block",
        "font-size": "2em",
        "margin-top": "0.67em",
        "margin-bottom": "0.67em",
        "font-weight": "bold",
    },
    "h2": {
        "display": "block",
        "font-size": "1.5em",
        "margin-top": "0.83em",
        "margin-bottom": "0.83em",
        "font-weight": "bold",
    },
    "h3": {
        "display": "block",
        "font-size": "1.17em",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "font-weight": "bold",
    },
    "h4": {
        "display": "block",
        "font-size": "1em",
        "margin-top": "1.33em",
        "margin-bottom": "1.33em",
        "font-weight": "bold",
    },
    "h5": {
        "display": "block",
        "font-size": "0.83em",
        "margin-top": "1.67em",
        "margin-bottom": "1.67em",
        "font-weight": "bold",
    },
    "h6": {
        "display": "block",
        "font-size": "0.67em",
        "margin-top": "2.33em",
        "margin-bottom": "2.33em",
        "font-weight": "bold",
    },
    # Lists
    "ul": {
        "display": "block",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "padding-left": "40px",
    },
    "ol": {
        "display": "block",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "padding-left": "40px",
    },
    "menu": {
        "display": "block",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "padding-left": "40px",
    },
    "dir": {
        "display": "block",
        "margin-top": "1em",
        "margin-bottom": "1em",
        "padding-left": "40px",
    },
    "dl": {"display": "block", "margin-top": "1em", "margin-bottom": "1em"},
    "dd": {"display": "block", "margin-left": "40px"},
    "li": {"display": "list-item"},
    # Tables (Basic Block Support in MVP)
    "table": {"display": "block", "margin-top": "0px", "margin-bottom": "0px"},
    "thead": {"display": "block"},
    "tbody": {"display": "block"},
    "tfoot": {"display": "block"},
    "tr": {"display": "block"},
    "td": {"display": "block"},
    "th": {"display": "block", "font-weight": "bold"},
    "caption": {"display": "block"},
    # Forms
    "form": {"display": "block", "margin-top": "0em"},
    "fieldset": {
        "display": "block",
        "margin-left": "2px",
        "margin-right": "2px",
        "padding-top": "0.35em",
        "padding-bottom": "0.625em",
        "padding-left": "0.75em",
        "padding-right": "0.75em",
    },
    "legend": {"display": "block"},
    # Inline formatting defaults
    "span": {"display": "inline"},
    "b": {"display": "inline", "font-weight": "bold"},
    "strong": {"display": "inline", "font-weight": "bold"},
    "i": {"display": "inline", "font-style": "italic"},
    "em": {"display": "inline", "font-style": "italic"},
    "cite": {"display": "inline", "font-style": "italic"},
    "var": {"display": "inline", "font-style": "italic"},
    "address": {"display": "block", "font-style": "italic"},
    "u": {"display": "inline", "text-decoration": "underline"},
    "ins": {"display": "inline", "text-decoration": "underline"},
    "s": {"display": "inline", "text-decoration": "line-through"},
    "strike": {"display": "inline", "text-decoration": "line-through"},
    "del": {"display": "inline", "text-decoration": "line-through"},
    "sub": {"display": "inline", "font-size": "0.83em"},
    "sup": {"display": "inline", "font-size": "0.83em"},
    "code": {"display": "inline", "font-family": "monospace"},
    "kbd": {"display": "inline", "font-family": "monospace"},
    "samp": {"display": "inline", "font-family": "monospace"},
    "a": {"display": "inline", "color": "#0000EE", "text-decoration": "underline"},
    "img": {"display": "inline-block"},
    # Anonymous text node default wrapper
    "#text": {"display": "inline"},
}

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
        "text-decoration",  # Technically not inherited in W3C but effectively cascaded in renderers
        "visibility",
        "white-space",
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
    from pypdfpatra.engine.shorthand import expand_shorthand_properties
    computed_style = expand_shorthand_properties(computed_style)

    # Assign finalized dict back to node
    node.style = computed_style

    # 6. Recurse to children
    for child in node.children:
        if isinstance(child, Node):
            resolve_styles(child, computed_style)

    return
