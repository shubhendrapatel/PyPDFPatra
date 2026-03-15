"""
pypdfpatra.engine.layout.common
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shared data structures and constants for the layout engine.
"""


class PosCB:
    """Contains context for positioning (containing block)."""

    __slots__ = ("x", "y", "w", "h", "is_icb")

    def __init__(self, x: float, y: float, w: float, h: float, is_icb: bool = False):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_icb = is_icb
