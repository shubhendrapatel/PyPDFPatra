
import os

from pypdfpatra.html import HTML


def render_coverage():
    base_dir = r"d:\programming\repo\PyPDFPatra\example"
    html_path = os.path.join(base_dir, "coverage.html")
    output_path = "coverage_phase9.pdf"

    with open(html_path, encoding="utf-8") as f:
        html_string = f.read()

    HTML(string=html_string, base_url=base_dir).write_pdf(output_path)
    print(f"Coverage PDF saved to {output_path}")

if __name__ == "__main__":
    render_coverage()
