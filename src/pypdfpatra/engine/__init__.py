"""
pypdfpatra.engine
~~~~~~~~~~~~~~~~~
The core Cython engine for PyPDFPatra.
This module exposes the high-performance C-extension classes
and sub-packages for styling and layout.
"""

from .tree import Box, Node, BlockBox, InlineBox, TextBox, AnonymousBlockBox, LineBox, TableBox, TableRowBox, TableRowGroupBox, TableCellBox
from .styling import resolve_styles, apply_styles, parse_stylesheets, expand_shorthand_properties
from .layout import generate_box_tree, layout_block_context, layout_inline_context, shift_box, layout_table_context

__all__ = [
    "Box",
    "Node",
    "BlockBox",
    "InlineBox",
    "TextBox",
    "AnonymousBlockBox",
    "LineBox",
    "TableBox",
    "TableRowBox",
    "TableRowGroupBox",
    "TableCellBox",
    "resolve_styles",
    "apply_styles",
    "parse_stylesheets",
    "expand_shorthand_properties",
    "generate_box_tree",
    "layout_block_context",
    "layout_inline_context",
    "shift_box",
    "layout_table_context",
]
