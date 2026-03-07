import os
from pypdfpatra import HTML
from pypdfpatra.logger import logger

if __name__ == "__main__":
    test_path = os.path.join(os.path.dirname(__file__), "coverage.html")
    with open(test_path, "r", encoding="utf-8") as f:
        html_string = f.read()

    pdf = HTML(string=html_string)
    output_path = os.path.join(os.path.dirname(__file__), "coverage.pdf")
    pdf.write_pdf(output_path)
    logger.info(f"Generated coverage test at {output_path}")
