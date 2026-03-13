"""
pypdfpatra.html
~~~~~~~~~~~~~~~
The public WeasyPrint-style API for PyPDFPatra.
"""

import os

import fpdf

from pypdfpatra.api import build_tree
from pypdfpatra.defaults import (
    CONTENT_WIDTH,
    DEFAULT_MARGIN_LEFT,
    DEFAULT_MARGIN_TOP,
    PAGE_HEIGHT,
    PAGE_WIDTH,
)
from pypdfpatra.engine import (
    apply_styles,
    generate_box_tree,
    layout_block_context,
    parse_stylesheets,
    resolve_styles,
)
from pypdfpatra.engine.font_metrics import FontMetrics
from pypdfpatra.logger import logger
from pypdfpatra.render import draw_boxes, register_anchors


class HTML:
    """
    The main entry point for generating PDFs from HTML.
    Follows the API conventions of WeasyPrint.
    """

    def __init__(
        self, string: str = None, filename: str = None, base_url: str = None, **kwargs
    ):
        """
        Initializes the document configuration.
        """
        self.base_url = base_url or ""
        # Maintain WeasyPrint API compatability
        if len(kwargs) == 0 and string is not None and filename is None:
            # If passed purely as positional, guess if it's a file or string
            if string.endswith(".html") or string.endswith(".htm"):
                filename = string
                string = None

        if filename is not None:
            if not self.base_url:
                self.base_url = os.path.dirname(os.path.abspath(filename))
            with open(filename, encoding="utf-8") as f:
                self.html_string = f.read()
        elif string is not None:
            self.html_string = string
            if not self.base_url:
                self.base_url = os.getcwd()
        else:
            raise ValueError("HTML requires either a 'string' or 'filename' argument.")

    def write_pdf(self, target: str):
        """
        Executes the entire layout and rendering pipeline and outputs a PDF.
        """
        # 1. Parsing Phase (Python HTML Parser -> Cython DOM)
        logger.info("[1/5] Parsing HTML...")
        root_node = build_tree(self.html_string)

        # 2. CSS Matching & W3C Style Resolution (CSSOM Phase)
        logger.info("[2/5] Resolving W3C Cascading Styles...")
        rules = parse_stylesheets(root_node, self.base_url)
        apply_styles(root_node, rules)
        resolve_styles(root_node)

        # 3. W3C Render Tree Generation
        logger.info("[3/5] Generating W3C Box Tree...")
        root_box = generate_box_tree(root_node, self.base_url)

        # 4. W3C Block Formatting Context Layout
        logger.info("[4/5] Calculating Layout Geometry...")
        if root_box is not None:
            # Shift everything by the top-left margin
            layout_block_context(
                root_box, DEFAULT_MARGIN_LEFT, DEFAULT_MARGIN_TOP, CONTENT_WIDTH
            )

        # 5. Rendering Phase
        logger.info("[5/5] Rendering Graphics Context...")

        pdf = fpdf.FPDF(unit="pt", format=(PAGE_WIDTH, PAGE_HEIGHT))
        pdf.set_auto_page_break(False)
        pdf.add_page()

        # Load custom fonts
        fm = FontMetrics.get_instance()
        if hasattr(fm, "_registered_fonts_data"):
            for _font_key, font_args in fm._registered_fonts_data.items():
                try:
                    pdf.add_font(
                        font_args["family"],
                        style=font_args["style"],
                        fname=font_args["path"],
                    )
                except Exception as e:
                    logger.warning(f"Failed to add font to PDF: {e}")

        if root_box is not None:
            # 5a. Anchor Registration (Phase 7 Internal Links)
            anchor_map = register_anchors(pdf, [root_box])
            # 5b. Main Content (Skip fixed elements for now)
            draw_boxes(pdf, [root_box], anchor_map=anchor_map, skip_fixed=True)

            # 5c. Global Fixed Elements (Repeat on every page)
            from pypdfpatra.render import collect_fixed_boxes
            fixed_boxes = collect_fixed_boxes([root_box])
            if fixed_boxes:
                total_pages = len(pdf.pages)
                for page_idx in range(total_pages):
                    for fb in fixed_boxes:
                        # Calculate shift from its original layout page to current page
                        original_page = int((fb.y + fb.margin_top) / PAGE_HEIGHT)
                        repeat_dy = (page_idx - original_page) * PAGE_HEIGHT
                        draw_boxes(pdf, [fb], dy=repeat_dy, skip_fixed=False)

        # 5. Output Phase
        logger.info(f"[5/5] Saving to {target}...")
        pdf.output(target)
        logger.info("Done!")
