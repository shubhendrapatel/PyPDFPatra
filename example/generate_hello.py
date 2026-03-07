"""
example/generate_hello.py
~~~~~~~~~~~~~~~~~~~~~~~~~
A simple script to demonstrate the WeasyPrint-style API of PyPDFPatra.
"""

from pypdfpatra import HTML

# A simple HTML snippet with inline styles that the MVP parser can handle.
# Notice we are using standard CSS box model properties and a hex background color.
html_content = """
<div>
    <h1>PyPDFPatra MVP</h1>
    <div style="background-color: #ff0000; width: 400px; height: 100px; margin-left: 50px; margin-top: 50px;">
        <p>This is a red box drawn by Cython layout math and fpdf2!</p>
    </div>
    
    <div style="background-color: #00ff00; width: 300px; height: 50px; margin-left: 100px; margin-top: 20px;">
        <p>This is a green box stacked below it!</p>
    </div>
</div>
"""


def generate():
    print("Initializing PyPDFPatra HTML Object...")

    # 1. Initialize the HTML wrapper just like WeasyPrint
    doc = HTML(string=html_content)

    # 2. Execute the parsing, layout, and rendering pipeline
    output_filename = "output.pdf"
    doc.write_pdf(output_filename)

    print(f"\nSuccess! Check out {output_filename} in the current directory.")


if __name__ == "__main__":
    generate()
