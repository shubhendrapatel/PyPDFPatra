"""
pypdfpatra.defaults
~~~~~~~~~~~~~~~~~~
Standard W3C and PDF backend defaults.
"""

# A4 dimensions in points (72 DPI)
PAGE_WIDTH = 595.0
PAGE_HEIGHT = 842.0

# Standard PDF print margins (40pt).
DEFAULT_MARGIN_TOP = 40.0
DEFAULT_MARGIN_BOTTOM = 40.0
DEFAULT_MARGIN_LEFT = 40.0
DEFAULT_MARGIN_RIGHT = 40.0

# Available content area
CONTENT_WIDTH = PAGE_WIDTH - DEFAULT_MARGIN_LEFT - DEFAULT_MARGIN_RIGHT
CONTENT_HEIGHT = PAGE_HEIGHT - DEFAULT_MARGIN_TOP - DEFAULT_MARGIN_BOTTOM

# Typography Defaults
DEFAULT_FONT_FAMILY = "helvetica"
DEFAULT_FONT_SIZE = 16.0
DEFAULT_LINE_HEIGHT_RATIO = 1.2
DEFAULT_MONOSPACE_FONT = "courier"
SMALL_CAPS_RATIO = 0.8  # Scaling factor for small-caps variant

# Unit conversion factors to Points (FPDF default unit)
DPI = 72.0
PT_TO_PT = 1.0
PX_TO_PT = 1.0  # Currently treated as 1:1 for simplicity; theoretically should be 72/96
IN_TO_PT = DPI
MM_TO_PT = DPI / 25.4
CM_TO_PT = DPI / 2.54

UNIT_FACTORS = {
    "px": PX_TO_PT,
    "pt": PT_TO_PT,
    "mm": MM_TO_PT,
    "cm": CM_TO_PT,
    "in": IN_TO_PT,
    "em": None,  # Dynamic
    "rem": None,  # Dynamic
    "%": None,  # Dynamic
}

# Color Defaults
DEFAULT_COLOR = "#000000"
DEFAULT_BACKGROUND_COLOR = "transparent"

# W3C Selectors
SUPPORTED_PSEUDO_ELEMENTS = ("before", "after", "marker", "placeholder")
