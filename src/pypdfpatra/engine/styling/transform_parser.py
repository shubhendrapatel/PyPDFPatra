"""
Transform CSS Property Parser

Parses CSS transform property values into a structured format.
Supports: translate(), scale(), rotate(), skew(), matrix()

Design: Extensible for adding new transform functions later.
Each parser function returns a dict with 'type' and 'args' keys.
"""

import math
import re
from typing import Any, Dict, List, Tuple

from pypdfpatra.defaults import UNIT_FACTORS

# Angle unit conversion to radians
ANGLE_UNITS = {
    "deg": lambda x: math.radians(x),
    "rad": lambda x: x,
    "grad": lambda x: math.radians(x * 360 / 400),
    "turn": lambda x: math.radians(x * 360),
}

# Default values for transform functions (W3C spec)
TRANSFORM_DEFAULTS = {
    "translate": {"y": 0},
    "translateX": {"x": 0},
    "translateY": {"y": 0},
    "scale": {"x": 1, "y": 1},
    "scaleX": {"x": 1},
    "scaleY": {"y": 1},
    "rotate": {"angle": 0},
    "skew": {"x": 0, "y": 0},
    "skewX": {"x": 0},
    "skewY": {"y": 0},
}


def parse_length_value(value_str: str) -> Tuple[float, str]:
    """
    Parse a CSS length value like '20px', '1.5em', etc.

    Returns: (numeric_value, unit_string)
    Raises: ValueError if format is invalid
    """
    value_str = value_str.strip()
    match = re.match(r"^([+-]?[\d.]+)\s*([a-z%]+)$", value_str, re.IGNORECASE)

    if not match:
        raise ValueError(f"Invalid length value: '{value_str}'")

    numeric = float(match.group(1))
    unit = match.group(2).lower()

    return numeric, unit


def parse_angle_value(value_str: str) -> float:
    """
    Parse a CSS angle value like '45deg', '3.14rad', etc.

    Returns: angle in radians
    Raises: ValueError if format is invalid
    """
    value_str = value_str.strip()
    match = re.match(r"^([+-]?[\d.]+)\s*([a-z]+)$", value_str, re.IGNORECASE)

    if not match:
        raise ValueError(f"Invalid angle value: '{value_str}'")

    numeric = float(match.group(1))
    unit = match.group(2).lower()

    if unit not in ANGLE_UNITS:
        raise ValueError(f"Unknown angle unit: '{unit}'")

    return ANGLE_UNITS[unit](numeric)


def parse_number_value(value_str: str) -> float:
    """
    Parse a unitless numeric value.

    Returns: float value
    Raises: ValueError if format is invalid
    """
    value_str = value_str.strip()
    try:
        return float(value_str)
    except ValueError as e:
        raise ValueError(f"Invalid number value: '{value_str}'") from e


def extract_function_args(func_str: str) -> List[str]:
    """
    Extract function arguments from a CSS function string.

    Input: 'translate(10px, 20px)' -> ['10px', '20px']
    Input: 'rotate(45deg)' -> ['45deg']

    Returns: List of argument strings (raw, unparsed)
    """
    # Remove function name and parentheses
    match = re.match(r"^[a-z]+\s*\(\s*(.*)\s*\)$", func_str.strip(), re.IGNORECASE)
    if not match:
        return []

    args_str = match.group(1)
    if not args_str:
        return []

    # Split by comma, handling nested functions gracefully
    args = []
    current = ""
    paren_depth = 0

    for char in args_str:
        if char == "(":
            paren_depth += 1
            current += char
        elif char == ")":
            paren_depth -= 1
            current += char
        elif char == "," and paren_depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        args.append(current.strip())

    return args


def parse_translate(args: List[str]) -> Dict[str, Any]:
    """
    Parse translate(x [, y]) function.

    Returns: {'type': 'translate', 'args': [tx, ty], 'units': ('px', 'px')}
    """
    if not args or len(args) > 2:
        raise ValueError(f"translate() expects 1-2 arguments, got {len(args)}")

    tx_val, tx_unit = parse_length_value(args[0])
    ty_val = 0.0
    ty_unit = "px"

    if len(args) == 2:
        ty_val, ty_unit = parse_length_value(args[1])

    return {
        "type": "translate",
        "args": [tx_val, ty_val],
        "units": (tx_unit, ty_unit),
    }


def parse_translateX(args: List[str]) -> Dict[str, Any]:
    """Parse translateX(x) function."""
    if len(args) != 1:
        raise ValueError(f"translateX() expects 1 argument, got {len(args)}")

    tx_val, tx_unit = parse_length_value(args[0])

    return {
        "type": "translateX",
        "args": [tx_val],
        "units": (tx_unit,),
    }


def parse_translateY(args: List[str]) -> Dict[str, Any]:
    """Parse translateY(y) function."""
    if len(args) != 1:
        raise ValueError(f"translateY() expects 1 argument, got {len(args)}")

    ty_val, ty_unit = parse_length_value(args[0])

    return {
        "type": "translateY",
        "args": [ty_val],
        "units": (ty_unit,),
    }


def parse_scale(args: List[str]) -> Dict[str, Any]:
    """Parse scale(x [, y]) function."""
    if not args or len(args) > 2:
        raise ValueError(f"scale() expects 1-2 arguments, got {len(args)}")

    sx = parse_number_value(args[0])
    sy = sx  # Default: if only 1 arg, y = x

    if len(args) == 2:
        sy = parse_number_value(args[1])

    return {
        "type": "scale",
        "args": [sx, sy],
    }


def parse_scaleX(args: List[str]) -> Dict[str, Any]:
    """Parse scaleX(x) function."""
    if len(args) != 1:
        raise ValueError(f"scaleX() expects 1 argument, got {len(args)}")

    sx = parse_number_value(args[0])

    return {
        "type": "scaleX",
        "args": [sx],
    }


def parse_scaleY(args: List[str]) -> Dict[str, Any]:
    """Parse scaleY(y) function."""
    if len(args) != 1:
        raise ValueError(f"scaleY() expects 1 argument, got {len(args)}")

    sy = parse_number_value(args[0])

    return {
        "type": "scaleY",
        "args": [sy],
    }


def parse_rotate(args: List[str]) -> Dict[str, Any]:
    """Parse rotate(angle) function."""
    if len(args) != 1:
        raise ValueError(f"rotate() expects 1 argument, got {len(args)}")

    angle_rad = parse_angle_value(args[0])

    return {
        "type": "rotate",
        "args": [angle_rad],
    }


def parse_skew(args: List[str]) -> Dict[str, Any]:
    """Parse skew(x [, y]) function."""
    if not args or len(args) > 2:
        raise ValueError(f"skew() expects 1-2 arguments, got {len(args)}")

    skew_x = parse_angle_value(args[0])
    skew_y = 0.0

    if len(args) == 2:
        skew_y = parse_angle_value(args[1])

    return {
        "type": "skew",
        "args": [skew_x, skew_y],
    }


def parse_skewX(args: List[str]) -> Dict[str, Any]:
    """Parse skewX(x) function."""
    if len(args) != 1:
        raise ValueError(f"skewX() expects 1 argument, got {len(args)}")

    skew_x = parse_angle_value(args[0])

    return {
        "type": "skewX",
        "args": [skew_x],
    }


def parse_skewY(args: List[str]) -> Dict[str, Any]:
    """Parse skewY(y) function."""
    if len(args) != 1:
        raise ValueError(f"skewY() expects 1 argument, got {len(args)}")

    skew_y = parse_angle_value(args[0])

    return {
        "type": "skewY",
        "args": [skew_y],
    }


def parse_matrix(args: List[str]) -> Dict[str, Any]:
    """Parse matrix(a, b, c, d, e, f) function."""
    if len(args) != 6:
        raise ValueError(f"matrix() expects 6 arguments, got {len(args)}")

    values = [parse_number_value(arg) for arg in args]

    return {
        "type": "matrix",
        "args": values,
    }


# Dispatch table for parser functions
TRANSFORM_PARSERS = {
    "translate": parse_translate,
    "translatex": parse_translateX,
    "translatey": parse_translateY,
    "scale": parse_scale,
    "scalex": parse_scaleX,
    "scaley": parse_scaleY,
    "rotate": parse_rotate,
    "skew": parse_skew,
    "skewx": parse_skewX,
    "skewy": parse_skewY,
    "matrix": parse_matrix,
}


def parse_transform_string(transform_str: str) -> List[Dict[str, Any]]:
    """
    Parse a CSS transform property value into a list of transform functions.

    Input: 'translate(10px, 20px) rotate(45deg) scale(1.5)'
    Output: [
        {'type': 'translate', 'args': [10.0, 20.0], 'units': ('px', 'px')},
        {'type': 'rotate', 'args': [0.7853981633974483]},  # 45 deg in radians
        {'type': 'scale', 'args': [1.5, 1.5]},
    ]

    Args:
        transform_str: CSS transform property value
        (e.g., 'translate(10px) rotate(45deg)')

    Returns:
        List of dicts with 'type' and 'args' keys
        Returns empty list for 'none' or empty strings

    Raises:
        ValueError: If transform syntax is invalid
    """
    transform_str = transform_str.strip().lower()

    # Handle 'none' and empty/whitespace strings
    if not transform_str or transform_str == "none":
        return []

    transforms = []

    # Extract all function calls: function_name(args)
    func_pattern = r"([a-z]+)\s*\(\s*[^)]*\)"
    functions = re.finditer(func_pattern, transform_str, re.IGNORECASE)

    for match in functions:
        func_call = match.group(0)
        func_name = match.group(1).lower()

        if func_name not in TRANSFORM_PARSERS:
            raise ValueError(f"Unknown transform function: '{func_name}'")

        # Extract arguments
        args = extract_function_args(func_call)

        # Parse using appropriate parser
        parser_func = TRANSFORM_PARSERS[func_name]
        try:
            transform_dict = parser_func(args)
            transforms.append(transform_dict)
        except ValueError as e:
            raise ValueError(f"Error parsing {func_name}(): {e}") from e

    return transforms


def normalize_length_to_pixels(
    value: float, unit: str, ref_font_size: float = None, root_font_size: float = 16.0
) -> float:
    """
    Convert a length value to pixels, handling em/rem/% units.

    Args:
        value: Numeric value
        unit: Unit string ('px', 'em', 'rem', 'pt', etc.)
        ref_font_size: Font size of the element (for 'em', default 16px)
        root_font_size: Root font size (for 'rem', default 16px)

    Returns:
        Value in pixels
    """
    if unit in UNIT_FACTORS and UNIT_FACTORS[unit] is not None:
        return value * UNIT_FACTORS[unit]

    if unit == "em":
        ref_size = ref_font_size if ref_font_size is not None else 16.0
        return value * ref_size

    if unit == "rem":
        return value * root_font_size

    # % and other dynamic units default to 0 (should be handled at layout time)
    return 0.0
