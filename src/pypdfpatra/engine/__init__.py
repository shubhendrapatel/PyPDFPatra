"""
pypdfpatra.engine
~~~~~~~~~~~~~~~~~
The core Cython engine for PyPDFPatra.
This module exposes the high-performance C-extension classes.
"""

from .tree import Box, Node, BlockBox, InlineBox, TextBox, AnonymousBlockBox, LineBox
from .style import resolve_styles
from .box_generator import generate_box_tree
from .layout_block import layout_block_context
from .layout_inline import layout_inline_context
from .css_parser import parse_stylesheets

__all__ = [
    "Box",
    "Node",
    "BlockBox",
    "InlineBox",
    "TextBox",
    "AnonymousBlockBox",
    "LineBox",
    "resolve_styles",
    "generate_box_tree",
    "layout_block_context",
    "layout_inline_context",
    "parse_stylesheets",
]
