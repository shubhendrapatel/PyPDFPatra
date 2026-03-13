"""
pypdfpatra.engine.shorthand
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides functions to expand W3C CSS shorthand properties into their
fundamental sub-properties (e.g., margin: 10px 20px -> margin-top, etc).
"""

__all__ = ["expand_shorthand_properties"]


def _expand_quad_shorthand(prop: str, value: str, output_dict: dict) -> None:
    """
    Expands TRBL (Top, Right, Bottom, Left) shorthands like margin and padding.
    W3C Spec:
    - 1 value: Top, Right, Bottom, Left
    - 2 values: [Top, Bottom], [Right, Left]
    - 3 values: Top, [Right, Left], Bottom
    - 4 values: Top, Right, Bottom, Left
    """
    if not value:
        return

    # A simple split by whitespace handles most basic pixel/em cases.
    parts = value.strip().split()
    parts_count = len(parts)

    if parts_count == 1:
        top = right = bottom = left = parts[0]
    elif parts_count == 2:
        top = bottom = parts[0]
        right = left = parts[1]
    elif parts_count == 3:
        top = parts[0]
        right = left = parts[1]
        bottom = parts[2]
    elif parts_count >= 4:
        top = parts[0]
        right = parts[1]
        bottom = parts[2]
        left = parts[3]
    else:
        return

    # Handle border-width -> border-top-width
    if prop.startswith("border-"):
        prefix, suffix = "border", prop[6:]  # e.g. '-width'
    else:
        prefix, suffix = prop, ""

    output_dict[f"{prefix}-top{suffix}"] = top
    output_dict[f"{prefix}-right{suffix}"] = right
    output_dict[f"{prefix}-bottom{suffix}"] = bottom
    output_dict[f"{prefix}-left{suffix}"] = left


def _expand_border_shorthand(value: str, output_dict: dict) -> None:
    """
    Expands CSS 'border: 1px solid black' into its component parts,
    then expands those into TRBL parts.
    """
    width, style, color = "medium", "none", "currentcolor"

    parts = value.strip().split()
    for part in parts:
        part_lower = part.lower()
        if part_lower in (
            "none",
            "hidden",
            "dotted",
            "dashed",
            "solid",
            "double",
            "groove",
            "ridge",
            "inset",
            "outset",
        ):
            style = part
        elif part_lower in ("thin", "medium", "thick") or (
            any(char.isdigit() for char in part) and not part.startswith("#")
        ):
            width = part
        else:
            color = part

    output_dict["border-width"] = width
    output_dict["border-style"] = style
    output_dict["border-color"] = color

    # Expand to top, right, bottom, left
    _expand_quad_shorthand("border-width", width, output_dict)
    _expand_quad_shorthand("border-style", style, output_dict)
    _expand_quad_shorthand("border-color", color, output_dict)


def expand_shorthand_properties(style_dict: dict) -> dict:
    """
    Takes a dictionary of computed CSS properties and explodes any shorthand
    properties into their individual fundamental W3C components.

    Args:
        style_dict (dict): A dictionary mapping CSS properties to their string values.

    Returns:
        dict: A new dictionary with shorthands fully expanded.
    """
    expanded = {}

    for prop, val in style_dict.items():
        if prop in (
            "margin",
            "padding",
            "border-width",
            "border-style",
            "border-color",
        ):
            _expand_quad_shorthand(prop, val, expanded)
        elif prop == "border":
            _expand_border_shorthand(val, expanded)
        elif prop == "background":
            # Simplistic expansion: assume the value contains a color
            # PyPDFPatra currently only renders colors from background-color
            expanded["background-color"] = val
        elif prop == "flex":
            # Very basic flex shorthand expansion: flex: <grow>
            # Standard: [ <'flex-grow'> <'flex-shrink'>? || <'flex-basis'> ]
            parts = val.strip().split()
            if parts:
                expanded["flex-grow"] = parts[0]
                if len(parts) > 1:
                    expanded["flex-shrink"] = parts[1]
                if len(parts) > 2:
                    expanded["flex-basis"] = parts[2]
        elif prop in ("border-top", "border-right", "border-bottom", "border-left"):
            # Expands e.g. 'border-left: 1px solid black' into 'border-left-width', etc.
            temp = {}
            _expand_border_shorthand(val, temp)
            # Re-map from generic 'border-width' to specific 'border-left-width'
            edge = prop[7:]  # top, right, bottom, or left
            expanded[f"border-{edge}-width"] = temp.get("border-width")
            expanded[f"border-{edge}-style"] = temp.get("border-style")
            expanded[f"border-{edge}-color"] = temp.get("border-color")
        else:
            # We preserve existing fundamental properties
            # If the user explicitly defined `margin-top: 10px; margin: 0px`,
            # we will overwrite but for simpler AST parsing this is usually handled
            # by cascade order. Right now simply inject.
            expanded[prop] = val

    return expanded
