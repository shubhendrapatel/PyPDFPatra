import fpdf

def parse_font(style: dict, base_size: float = 16.0) -> tuple:
    """Parses CSS dictionary into (family, style_str, size_float) for FPDF."""
    family = style.get("font-family", "helvetica").split(",")[0].strip().strip("'\"").lower()
    if family == "monospace":
        family = "courier"
        
    size_str = style.get("font-size", "1em").strip().lower()
    size = base_size
    if size_str.endswith("em"):
        try:
            size = base_size * float(size_str[:-2])
        except ValueError:
            pass
    elif size_str.endswith("px") or size_str.endswith("pt"):
        try:
            size = float(size_str[:-2])
        except ValueError:
            pass

    # Basic style flags for FPDF
    fpdf_style = ""
    if style.get("font-weight", "") == "bold":
        fpdf_style += "B"
    if style.get("font-style", "") == "italic":
        fpdf_style += "I"
    if "underline" in style.get("text-decoration", ""):
        fpdf_style += "U"
        
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
        return cls._instance

    def get_text_width(
        self,
        text: str,
        font_family: str = "helvetica",
        font_size: float = 16.0,
        font_style: str = "",
    ) -> float:
        """
        Returns the width of the given string in points.
        """
        self._pdf.set_font(font_family, style=font_style, size=font_size)
        return self._pdf.get_string_width(text)

    def get_line_height(
        self,
        font_family: str = "helvetica",
        font_size: float = 16.0,
        font_style: str = "",
    ) -> float:
        """
        Returns standard line height (currently just 1.2 * font_size).
        """
        return font_size * 1.2


def measure_text(text: str, font_family="helvetica", size=16.0, style="") -> float:
    return FontMetrics.get_instance().get_text_width(text, font_family, size, style)


def get_line_height(font_family="helvetica", size=16.0, style="") -> float:
    return FontMetrics.get_instance().get_line_height(font_family, size, style)
