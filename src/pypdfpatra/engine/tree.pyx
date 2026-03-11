# src/pypdfpatra/engine/tree.pyx

"""
pypdfpatra.engine.tree
~~~~~~~~~~~~~~~~~~~~~~~
Core Cython extension types for the HTML DOM tree and PDF layout boxes.
"""

from pypdfpatra.engine.tree cimport Box, Node


cdef class Box:
    """
    A Cython extension type representing the computed geometry for one
    element in the PDF layout.
    """

    def __init__(self, object node=None):
        self.node = node
        self.children = []
        
        # Position and size of the content box
        self.x = 0.0
        self.y = 0.0
        self.w = 0.0
        self.h = 0.0

        # CSS spacing (all default to 0)
        self.margin_top    = 0.0
        self.margin_right  = 0.0
        self.margin_bottom = 0.0
        self.margin_left   = 0.0

        self.padding_top    = 0.0
        self.padding_right  = 0.0
        self.padding_bottom = 0.0
        self.padding_left   = 0.0

        self.border_top    = 0.0
        self.border_right  = 0.0
        self.border_bottom = 0.0
        self.border_left   = 0.0

cdef class BlockBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class AnonymousBlockBox(BlockBox):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class InlineBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class InlineBlockBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class LineBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class MarkerBox(Box):
    def __init__(self, str text_content="", object node=None):
        super().__init__(node)
        self.text_content = text_content

cdef class TableBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)
        self.thead_rows = []

cdef class TableRowGroupBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class TableRowBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class TableCellBox(Box):
    def __init__(self, object node=None):
        super().__init__(node)

cdef class ImageBox(Box):
    def __init__(self, str img_src="", float image_w=0.0, float image_h=0.0, str alt_text="", object node=None):
        super().__init__(node)
        self.img_src = img_src
        self.image_w = image_w
        self.image_h = image_h
        self.alt_text = alt_text

cdef class TextBox(Box):
    def __init__(self, str text_content="", object node=None):
        super().__init__(node)
        self.text_content = text_content


cdef class Node:
    """
    A Cython extension type representing a single element in the parsed
    HTML/DOM tree.

    Mirrors a DOM node: carries the HTML tag name, HTML attributes, computed
    CSS styles, and the list of `Box` geometry objects generated during layout.

    Args:
        tag (str): The HTML tag name (e.g. 'div', 'p', 'text').
        props (dict, optional): HTML attributes dict. Defaults to {}.
    """

    def __init__(self, str tag, dict props=None):
        self.tag      = tag
        self.props    = props or {}
        self.children = []  # Child Node objects
        self.style    = {}  # CSS property dict, e.g. {'color': 'red'}
        self.boxes    = []  # Box geometry objects created during layout
        self.pseudos  = {}  # Storage for ::before, ::after, etc.
        self.parent        = None

    def add_child(self, Node child):
        """
        Appends a child Node, building the hierarchical DOM tree.

        Args:
            child (Node): The child Node to append.
        """
        child.parent = self
        self.children.append(child)
