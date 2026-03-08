"""
pypdfpatra.api
~~~~~~~~~~~~~~
The high-level Python API for PyPDFPatra.
This module handles HTML parsing and bridges it to the Cython Engine.
"""

from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

from pypdfpatra.engine.tree import Node

__all__ = ["PatraParser", "build_tree"]


# Tags that are self-closing by definition in HTML5 and should never be pushed
# onto the parent stack (they have no closing tag).
_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


class PatraParser(HTMLParser):
    """
    A specialized HTML parser that generates a tree of Cython-based Nodes.

    It uses a stack-based approach to maintain parent-child relationships
    while traversing the HTML structure.

    Attributes:
        root (Node): The root container node holding the entire parsed document.
        stack (List[Node]): A stack used to track the current parent block.
    """

    def __init__(self) -> None:
        super().__init__()
        # Initialize a root 'container' node to hold the entire document
        self.root: Node = Node("root")
        self.stack: List[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        """
        Triggered when a new HTML tag (e.g. <div>) is found.
        Creates a new Cython Node and appends it to the current parent.

        Args:
            tag (str): The HTML tag name (lowercased by HTMLParser).
            attrs (List[Tuple[str, Optional[str]]]): A list of (name, value) attribute tuples.
        """
        # Convert list of tuples [('class', 'main')] -> {'class': 'main'}
        attr_dict: Dict[str, str] = {k: v for k, v in attrs if v is not None}

        # Parse and inline `style` attribute into the node's style dict
        style_str: str = attr_dict.pop("style", "")
        node = Node(tag, attr_dict)
        if style_str:
            for declaration in style_str.split(";"):
                declaration = declaration.strip()
                if ":" in declaration:
                    prop, _, val = declaration.partition(":")
                    node.style[prop.strip()] = val.strip()

        # Attach to the current parent
        self.stack[-1].add_child(node)

        # Void elements have no children and no closing tag — do not push.
        if tag not in _VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        """
        Triggered by XHTML-style self-closing tags (e.g. <br/>).
        Creates the Node and attaches it without pushing to the stack.
        """
        attr_dict: Dict[str, str] = {k: v for k, v in attrs if v is not None}
        node = Node(tag, attr_dict)
        self.stack[-1].add_child(node)

    def handle_endtag(self, tag: str) -> None:
        """
        Triggered when a closing tag (e.g. </div>) is found.
        Moves the context back up to the parent element.

        Args:
            tag (str): The HTML tag name that is closing.
        """
        # Guard against popping the root off the stack
        if len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        """
        Triggered when raw text content is found inside a tag (e.g. the
        "Hello" inside <p>Hello</p>). Creates a virtual 'text' Node to
        carry the content through to layout and rendering.

        Args:
            data (str): The raw character data between tags.
        """
        if not self.stack:
            return

        # Check if we are inside a <pre> tag (which preserves whitespace)
        in_pre = any(node.tag == "pre" for node in self.stack)

        # Discard strings that are ONLY whitespace (like newlines between HTML tags)
        # to prevent creating empty text nodes between block elements.
        if not data.strip() and not in_pre:
            return

        if in_pre:
            cleaned = data
        else:
            import re

            # Collapse multiple whitespaces into a single space, but KEEP leading/trailing
            cleaned = re.sub(r"\s+", " ", data)

        text_node = Node("#text")
        text_node.style["content"] = cleaned
        self.stack[-1].add_child(text_node)


def build_tree(html_string: str) -> Node:
    """
    The main entry point to turn a raw HTML string into a Cython Node Tree.

    Args:
        html_string (str): The raw HTML content (e.g. "<div>Hello</div>").

    Returns:
        Node: The root Node of the generated tree (the outermost element).
    """
    parser = PatraParser()
    parser.feed(html_string)

    # Return the first real element from our synthetic 'root' wrapper.
    return parser.root.children[0] if parser.root.children else parser.root
