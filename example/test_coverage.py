import os

from pypdfpatra import HTML
from pypdfpatra.logger import logger

if __name__ == "__main__":
    test_path = os.path.join(os.path.dirname(__file__), "coverage.html")

    pdf = HTML(filename=test_path)
    output_path = os.path.join(os.path.dirname(__file__), "coverage.pdf")
    pdf.write_pdf(output_path)
    logger.info(f"Generated coverage test at {output_path}")
