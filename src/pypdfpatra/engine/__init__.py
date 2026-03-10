"""
pypdfpatra.engine
~~~~~~~~~~~~~~~~~
The core Cython engine for PyPDFPatra.
This module exposes the high-performance C-extension classes
and sub-packages for styling and layout.
"""

from .layout import (
    generate_box_tree,
    layout_block_context,
    layout_inline_context,
    layout_table_context,
    shift_box,
)
from .styling import (
    apply_styles,
    expand_shorthand_properties,
    parse_stylesheets,
    resolve_styles,
)
from .tree import (
    AnonymousBlockBox,
    BlockBox,
    Box,
    InlineBox,
    LineBox,
    Node,
    TableBox,
    TableCellBox,
    TableRowBox,
    TableRowGroupBox,
    TextBox,
)

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
