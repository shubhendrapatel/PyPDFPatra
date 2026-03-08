import fpdf

def parse_font(style: dict, base_size: float = 16.0) -> tuple:
    """Parses CSS dictionary into (family, style_str, size_float) for FPDF."""
    family = style.get("font-family", "helvetica").split(",")[0].strip().strip("'\"").lower().replace(" ", "")
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
            cls._registered_fonts_data = {}  # Store for rendering phase
            
        return cls._instance

    def register_font(self, family: str, style: str, path: str):
        """Registers a custom TTF font for measurement and later rendering."""
        key = f"{family}-{style}"
        if key not in self._registered_fonts_data:
            self._pdf.add_font(family, style=style, fname=path)
            self._registered_fonts_data[key] = {"family": family, "style": style, "path": path}

    def set_font_safe(
        self,
        pdf_instance: fpdf.FPDF,
        font_family: str,
        font_size: float,
        font_style: str,
    ):
        """Attempts to set a font, falling back to base styles if a specific bold/italic TTF is unmapped."""
        try:
            pdf_instance.set_font(font_family, style=font_style, size=font_size)
        except fpdf.errors.FPDFException:
            try:
                pdf_instance.set_font(font_family, style="", size=font_size)
            except fpdf.errors.FPDFException:
                pdf_instance.set_font("helvetica", style="", size=font_size)

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
        self.set_font_safe(self._pdf, font_family, font_size, font_style)
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
