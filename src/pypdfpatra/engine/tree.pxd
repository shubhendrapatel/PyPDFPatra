# src/pypdfpatra/engine/tree.pxd

"""
Cython header file defining the core data structures for the PyPDFPatra engine.
These C-level extension types provide high-performance foundations for the
HTML DOM and CSS Box Model.

Design note: Box attributes are flat `cdef public double` fields rather than
nested C-structs. Nested C-structs inside `cdef class` are inaccessible from
Python when objects are stored in and retrieved from Python lists, causing
Access Violation crashes. Flat attributes are always safely accessible.
"""


# Box: Represents a rendered geometry unit for one node in the PDF layout.
# All coordinates and sizes are in PDF points.
cdef class Box:
    # Content box geometry (inner dimensions, after margin + padding)
    cdef public double x
    cdef public double y
    cdef public double w
    cdef public double h

    # CSS Box Model spacing
    cdef public double margin_top
    cdef public double margin_right
    cdef public double margin_bottom
    cdef public double margin_left

    cdef public double padding_top
    cdef public double padding_right
    cdef public double padding_bottom
    cdef public double padding_left

    cdef public double border_top
    cdef public double border_right
    cdef public double border_bottom
    cdef public double border_left

    # Render Tree Structure
    cdef public list children
    cdef public object node  # Reference back to the DOM Node

cdef class BlockBox(Box):
    pass
    
cdef class AnonymousBlockBox(BlockBox):
    pass

cdef class InlineBox(Box):
    pass

cdef class InlineBlockBox(Box):
    pass

cdef class LineBox(Box):
    pass

cdef class MarkerBox(Box):
    cdef public str text_content

cdef class TableBox(Box):
    pass

cdef class TableRowGroupBox(Box):
    pass

cdef class TableRowBox(Box):
    pass

cdef class TableCellBox(Box):
    pass

cdef class ImageBox(Box):
    cdef public str img_src
    cdef public float image_w
    cdef public float image_h
    cdef public str alt_text

cdef class TextBox(Box):
    cdef public str text_content

# Node: Represents a single element in the parsed HTML/DOM tree.
cdef class Node:
    cdef public str tag
    cdef public dict props
    cdef public list children
    cdef public dict style
    cdef public list boxes   # A Node can map to multiple Box objects.
