import fpdf

from pypdfpatra.defaults import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_LINE_HEIGHT_RATIO,
    DEFAULT_MONOSPACE_FONT,
    UNIT_FACTORS,
)


def parse_font(
    style: dict, base_size: float = DEFAULT_FONT_SIZE
) -> tuple[str, str, float]:
    """
    Parses CSS dictionary into (family, style_str, size_float) for FPDF.

    Args:
        style: CSS property dictionary.
        base_size: The font-size of the current element (used for relative units).

    Returns:
        A tuple of (font_family, fpdf_style, font_size_in_pt).
    """
    family = (
        style.get("font-family", DEFAULT_FONT_FAMILY)
        .split(",")[0]
        .strip()
        .strip("'\"")
        .lower()
        .replace(" ", "")
    )
    if family == "monospace":
        family = DEFAULT_MONOSPACE_FONT

    size_str = style.get("font-size", "1em").strip().lower()
    size = base_size

    # Handle numeric units
    if size_str.endswith("rem"):
        try:
            size = DEFAULT_FONT_SIZE * float(size_str[:-3])
        except ValueError:
            pass
    elif size_str.endswith("em"):
        try:
            size = base_size * float(size_str[:-2])
        except ValueError:
            pass
    else:
        # Check absolute units
        for unit, factor in UNIT_FACTORS.items():
            if factor is not None and size_str.endswith(unit):
                try:
                    size = float(size_str[: -len(unit)]) * factor
                    break
                except ValueError:
                    pass

    # Basic style flags for FPDF
    fpdf_style = ""
    if style.get("font-weight", "") == "bold":
        fpdf_style += "B"
    if style.get("font-style", "") == "italic":
        fpdf_style += "I"

    return family, fpdf_style, size


class FontMetrics:
    """
    Measures text width accurately for the Inline Formatting Context (IFC).
    Uses a singleton FPDF instance to ensure we get exactly the right
    metrics that the rendering backend will use.
    """

    _instance = None
    _pdf = None

    @classmethod
    def get_instance(cls) -> "FontMetrics":
        if cls._instance is None:
            cls._instance = cls()
            cls._pdf = fpdf.FPDF(unit="pt")
            cls._pdf.add_page()
            cls._registered_fonts_data = {}  # Store for rendering phase

        return cls._instance

    def register_font(self, family: str, style: str, path: str):
        """Registers a custom TTF font for measurement and later rendering."""
        key = f"{family}-{style}"
        if key not in self._registered_fonts_data:
            self._pdf.add_font(family, style=style, fname=path)
            self._registered_fonts_data[key] = {
                "family": family,
                "style": style,
                "path": path,
            }

    def set_font_safe(
        self,
        pdf_instance: fpdf.FPDF,
        font_family: str,
        font_size: float,
        font_style: str,
    ):
        """
        Attempts to set a font, falling back to base styles if a specific
        bold/italic TTF is unmapped.
        """
        try:
            pdf_instance.set_font(font_family, style=font_style, size=font_size)
        except fpdf.errors.FPDFException:
            try:
                pdf_instance.set_font(font_family, style="", size=font_size)
            except fpdf.errors.FPDFException:
                pdf_instance.set_font(DEFAULT_FONT_FAMILY, style="", size=font_size)

    def get_text_width(
        self,
        text: str,
        font_family: str = DEFAULT_FONT_FAMILY,
        font_size: float = DEFAULT_FONT_SIZE,
        font_style: str = "",
    ) -> float:
        """
        Returns the width of the given string in points.
        """
        self.set_font_safe(self._pdf, font_family, font_size, font_style)
        return self._pdf.get_string_width(text)

    def get_line_height(
        self,
        font_family: str = DEFAULT_FONT_FAMILY,
        font_size: float = DEFAULT_FONT_SIZE,
        font_style: str = "",
        css_line_height: str | float | None = None,
    ) -> float:
        """
        Calculates line height based on CSS property or ratio.

        Args:
            font_family: Registered font family name.
            font_size: Actual font size of the text block in PT.
            font_style: FPDF style string ('', 'B', 'I', 'BI').
            css_line_height: Raw CSS line-height value ('1.2', '24px', '200%', etc.).

        Returns:
            Line height in points.
        """
        if css_line_height is None or css_line_height == "normal":
            return font_size * DEFAULT_LINE_HEIGHT_RATIO

        # 1. Numeric values (e.g. 1.5) are ratios of current font-size
        if isinstance(css_line_height, (int, float)):
            return font_size * float(css_line_height)

        val = str(css_line_height).strip().lower()

        # Handle numeric ratio as string
        try:
            return font_size * float(val)
        except ValueError:
            pass

        # 2. Percentage (%) is relative to font-size
        if val.endswith("%"):
            try:
                return font_size * (float(val[:-1]) / 100.0)
            except ValueError:
                pass

        # 3. Relative units em/rem
        if val.endswith("rem"):
            try:
                return DEFAULT_FONT_SIZE * float(val[:-3])
            except ValueError:
                pass
        if val.endswith("em"):
            try:
                return font_size * float(val[:-2])
            except ValueError:
                pass

        # 4. Absolute units (converted to PT)
        for unit, factor in UNIT_FACTORS.items():
            if factor is not None and val.endswith(unit):
                try:
                    return float(val[: -len(unit)]) * factor
                except ValueError:
                    pass

        # Fallback to default ratio
        return font_size * DEFAULT_LINE_HEIGHT_RATIO


def measure_text(
    text: str, font_family=DEFAULT_FONT_FAMILY, size=DEFAULT_FONT_SIZE, style=""
) -> float:
    return FontMetrics.get_instance().get_text_width(text, font_family, size, style)


def get_line_height(
    font_family=DEFAULT_FONT_FAMILY,
    size=DEFAULT_FONT_SIZE,
    style="",
    css_line_height=None,
) -> float:
    return FontMetrics.get_instance().get_line_height(
        font_family, size, style, css_line_height=css_line_height
    )
