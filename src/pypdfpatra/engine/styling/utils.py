"""
pypdfpatra.engine.styling.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Utility functions for CSS property parsing and conversion.
"""


def parse_length(value: str, default: float = 0.0) -> float:
    """
    Parses a CSS length string (e.g., '10pt', '1in', '2.54cm') into points (pt).
    If no unit is provided, it assumes points.

    Args:
        value (str): The CSS length string to parse.
        default (float): The default value to return if parsing fails.

    Returns:
        float: The parsed length in points.
    """
    if not value:
        return float(default)

    val = str(value).strip().lower()
    try:
        if val.endswith("pt") or val.endswith("px"):
            return float(val[:-2])
        if val.endswith("in"):
            return float(val[:-2]) * 72.0
        if val.endswith("cm"):
            return float(val[:-2]) * 72.0 / 2.54
        if val.endswith("mm"):
            return float(val[:-2]) * 72.0 / 25.4

        # Strip any other non-numeric characters at the end (basic heuristic)
        import re

        match = re.match(r"^([+-]?\d*\.?\d+)", val)
        if match:
            return float(match.group(1))

        return float(val)
    except (ValueError, TypeError):
        return float(default)
