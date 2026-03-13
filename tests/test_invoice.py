
import os

from pypdfpatra.html import HTML


def render_invoice():
    # Use absolute paths for the example files
    base_dir = r"d:\programming\repo\PyPDFPatra\example\weasyprint-samples-main\invoice"
    html_path = os.path.join(base_dir, "invoice.html")
    output_path = "invoice_test.pdf"

    # Read HTML and render
    # Note: We might need to handle external CSS if pypdfpatra doesn't do it automatically.
    # pypdfpatra's HTML class usually handles file paths or strings.

    with open(html_path, encoding="utf-8") as f:
        html_string = f.read()

    # We need to set the base_url so it finds the CSS
    HTML(string=html_string, base_url=base_dir).write_pdf(output_path)
    print(f"Invoice PDF saved to {output_path}")

if __name__ == "__main__":
    render_invoice()
