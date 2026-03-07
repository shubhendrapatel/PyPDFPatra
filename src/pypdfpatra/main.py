"""
pypdfpatra.main
~~~~~~~~~~~~~~~
The public WeasyPrint-style API for PyPDFPatra.
"""

# TODO: use tinycss2 for css parsing
import tinycss2
import fpdf

from pypdfpatra.api import build_tree
from pypdfpatra.matcher import apply_styles
from pypdfpatra.engine import resolve_styles, generate_box_tree, layout_block_context
from pypdfpatra.render import draw_boxes
from pypdfpatra.logger import logger


class HTML:
    """
    The main entry point for generating PDFs from HTML.
    Follows the API conventions of WeasyPrint.
    """

    def __init__(self, string: str = None):
        """
        Initializes the document configuration.
        """
        if string is None:
            raise ValueError("HTML requires a string argument for MVP.")
        self.html_string = string

    def write_pdf(self, target: str):
        """
        Executes the entire layout and rendering pipeline and outputs a PDF.
        """
        # 1. Parsing Phase (Python HTML Parser -> Cython DOM)
        logger.info("[1/5] Parsing HTML...")
        root_node = build_tree(self.html_string)

        # 2. CSS Matching & W3C Style Resolution (CSSOM Phase)
        logger.info("[2/5] Resolving W3C Cascading Styles...")
        rules = []
        apply_styles(root_node, rules)
        resolve_styles(root_node)

        # 3. W3C Render Tree Generation
        logger.info("[3/5] Generating W3C Box Tree...")
        root_box = generate_box_tree(root_node)

        # 4. W3C Block Formatting Context Layout
        logger.info("[4/5] Calculating Layout Geometry...")
        if root_box is not None:
            layout_block_context(root_box, 0.0, 0.0, 595.0)

        # 5. Rendering Phase
        logger.info("[5/5] Rendering Graphics Context...")
        pdf = fpdf.FPDF(unit="pt", format="A4")
        pdf.set_auto_page_break(False)
        pdf.add_page()

        if root_box is not None:
            draw_boxes(pdf, [root_box])

        # 5. Output Phase
        logger.info(f"[5/5] Saving to {target}...")
        pdf.output(target)
        logger.info("Done!")
