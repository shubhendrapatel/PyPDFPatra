"""
Transform Matrix Operations for PDF Rendering

Converts CSS transform functions to PDF transformation matrices.
Handles matrix composition for chained transforms.

PDF uses affine transformation matrices in the form: [a, b, c, d, e, f]
Which applies the transformation: x' = a*x + c*y + e
                                 y' = b*x + d*y + f
"""

import math
from typing import Any, Dict, List

# Identity matrix
IDENTITY_MATRIX = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]


def multiply_matrices(m1: List[float], m2: List[float]) -> List[float]:
    """
    Multiply two 2D affine transformation matrices.

    PDF matrices are [a, b, c, d, e, f] representing:
    | a  c  e |
    | b  d  f |
    | 0  0  1 |

    Result = m1 × m2 (apply m2 first, then m1)

    Args:
        m1, m2: Transformation matrices [a, b, c, d, e, f]

    Returns:
        Composed transformation matrix [a, b, c, d, e, f]
    """
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2

    # Matrix multiplication for 3x3 affine matrices
    a = a1 * a2 + c1 * b2
    b = b1 * a2 + d1 * b2
    c = a1 * c2 + c1 * d2
    d = b1 * c2 + d1 * d2
    e = a1 * e2 + c1 * f2 + e1
    f = b1 * e2 + d1 * f2 + f1

    return [a, b, c, d, e, f]


def translate_matrix(tx: float, ty: float) -> List[float]:
    """
    Create a translation transformation matrix.

    Moves points by (tx, ty).
    Matrix: | 1  0  tx |
            | 0  1  ty |
            | 0  0  1  |

    Args:
        tx: Translation in X direction (pixels)
        ty: Translation in Y direction (pixels)

    Returns:
        Transformation matrix [1, 0, 0, 1, tx, ty]
    """
    return [1.0, 0.0, 0.0, 1.0, tx, ty]


def translateX_matrix(tx: float) -> List[float]:
    """Create a translation matrix for X-axis only."""
    return translate_matrix(tx, 0.0)


def translateY_matrix(ty: float) -> List[float]:
    """Create a translation matrix for Y-axis only."""
    return translate_matrix(0.0, ty)


def scale_matrix(
    sx: float, sy: float, origin_x: float = 0.0, origin_y: float = 0.0
) -> List[float]:
    """
    Create a scaling transformation matrix.

    Scales points by (sx, sy) relative to an origin point.
    Default origin (0, 0) scales from the element's top-left.

    If origin is not (0, 0):
    1. Translate by -origin
    2. Scale
    3. Translate by +origin

    Args:
        sx: Scale factor in X direction
        sy: Scale factor in Y direction
        origin_x: Origin point X coordinate (default 0)
        origin_y: Origin point Y coordinate (default 0)

    Returns:
        Transformation matrix [sx, 0, 0, sy, e, f]
    """
    if origin_x == 0.0 and origin_y == 0.0:
        # Simple case: scale from (0, 0)
        return [sx, 0.0, 0.0, sy, 0.0, 0.0]

    # Complex case: scale from arbitrary origin
    # Translate(-origin) → Scale → Translate(+origin)
    m = translate_matrix(-origin_x, -origin_y)
    m = multiply_matrices([sx, 0.0, 0.0, sy, 0.0, 0.0], m)
    m = multiply_matrices(translate_matrix(origin_x, origin_y), m)

    return m


def scaleX_matrix(sx: float) -> List[float]:
    """Create a scaling matrix for X-axis only."""
    return scale_matrix(sx, 1.0)


def scaleY_matrix(sy: float) -> List[float]:
    """Create a scaling matrix for Y-axis only."""
    return scale_matrix(1.0, sy)


def rotate_matrix(
    angle_rad: float, origin_x: float = 0.0, origin_y: float = 0.0
) -> List[float]:
    """
    Create a rotation transformation matrix.

    Rotates points by the given angle around an origin point.
    Positive angles rotate counter-clockwise.

    If origin is not (0, 0), applies: Translate(-origin) → Rotate → Translate(+origin)

    Args:
        angle_rad: Rotation angle in radians
        origin_x: Origin point X coordinate (default 0)
        origin_y: Origin point Y coordinate (default 0)

    Returns:
        Transformation matrix [cos(θ), sin(θ), -sin(θ), cos(θ), e, f]
    """
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    if origin_x == 0.0 and origin_y == 0.0:
        # Simple case: rotate around (0, 0)
        return [cos_a, sin_a, -sin_a, cos_a, 0.0, 0.0]

    # Complex case: rotate around arbitrary origin
    # Translate(-origin) → Rotate → Translate(+origin)
    m = translate_matrix(-origin_x, -origin_y)
    m = multiply_matrices([cos_a, sin_a, -sin_a, cos_a, 0.0, 0.0], m)
    m = multiply_matrices(translate_matrix(origin_x, origin_y), m)

    return m


def skew_matrix(skew_x_rad: float, skew_y_rad: float) -> List[float]:
    """
    Create a skewing (shear) transformation matrix.

    Skews points by the given angles (in radians).

    Args:
        skew_x_rad: X-axis skew angle (radians)
        skew_y_rad: Y-axis skew angle (radians)

    Returns:
        Transformation matrix [1, tan(y), tan(x), 1, 0, 0]
    """
    tan_x = math.tan(skew_x_rad)
    tan_y = math.tan(skew_y_rad)

    return [1.0, tan_y, tan_x, 1.0, 0.0, 0.0]


def skewX_matrix(skew_x_rad: float) -> List[float]:
    """Create a skewing matrix for X-axis only."""
    return skew_matrix(skew_x_rad, 0.0)


def skewY_matrix(skew_y_rad: float) -> List[float]:
    """Create a skewing matrix for Y-axis only."""
    return skew_matrix(0.0, skew_y_rad)


def matrix_matrix(
    a: float, b: float, c: float, d: float, e: float, f: float
) -> List[float]:
    """
    Create a transformation matrix from explicit values.

    Args:
        a, b, c, d, e, f: Matrix coefficients

    Returns:
        Transformation matrix [a, b, c, d, e, f]
    """
    return [a, b, c, d, e, f]


# Dispatch table for matrix generation
TRANSFORM_MATRIX_GENERATORS = {
    "translate": lambda t: translate_matrix(t["args"][0], t["args"][1]),
    "translateX": lambda t: translateX_matrix(t["args"][0]),
    "translateY": lambda t: translateY_matrix(t["args"][0]),
    "scale": lambda t: scale_matrix(t["args"][0], t["args"][1]),
    "scaleX": lambda t: scaleX_matrix(t["args"][0]),
    "scaleY": lambda t: scaleY_matrix(t["args"][0]),
    "rotate": lambda t: rotate_matrix(t["args"][0]),
    "skew": lambda t: skew_matrix(t["args"][0], t["args"][1]),
    "skewX": lambda t: skewX_matrix(t["args"][0]),
    "skewY": lambda t: skewY_matrix(t["args"][0]),
    "matrix": lambda t: matrix_matrix(*t["args"]),
}


def transform_to_matrix(transform: Dict[str, Any]) -> List[float]:
    """
    Convert a parsed transform function to a PDF transformation matrix.

    Args:
        transform: Dict with 'type' and 'args' keys (from transform_parser)

    Returns:
        PDF transformation matrix [a, b, c, d, e, f]

    Raises:
        ValueError: If transform type is unknown
    """
    transform_type = transform.get("type", "").lower()

    if transform_type not in TRANSFORM_MATRIX_GENERATORS:
        raise ValueError(f"Unknown transform type: '{transform_type}'")

    generator = TRANSFORM_MATRIX_GENERATORS[transform_type]
    return generator(transform)


def compose_transforms(transforms: List[Dict[str, Any]]) -> List[float]:
    """
    Compose multiple transform functions into a single matrix.

    Transforms are applied in order (left to right in CSS, right to left in matrices).

    Args:
        transforms: List of parsed transform dicts

    Returns:
        Composed transformation matrix [a, b, c, d, e, f]
    """
    if not transforms:
        return IDENTITY_MATRIX[:]

    # Start with identity
    result = IDENTITY_MATRIX[:]

    # Apply each transform from left to right
    # (In CSS: translate(10px) rotate(45deg) means translate first, then rotate)
    for transform in transforms:
        transform_matrix = transform_to_matrix(transform)
        # Compose: result = transform_matrix × result
        # This ensures transforms are applied in CSS order
        result = multiply_matrices(transform_matrix, result)

    return result


def normalize_matrix(matrix: List[float], decimal_places: int = 6) -> List[float]:
    """
    Round matrix values to avoid floating-point precision issues in PDF.

    Very small values (< 1e-10) are rounded to 0.

    Args:
        matrix: Transformation matrix
        decimal_places: Number of decimal places to round to

    Returns:
        Normalized matrix
    """
    factor = 10**decimal_places
    result = []

    for val in matrix:
        # Zero out very small values (floating-point artifacts)
        if abs(val) < 1e-10:
            result.append(0.0)
        else:
            # Round to specified precision
            result.append(round(val * factor) / factor)

    return result
