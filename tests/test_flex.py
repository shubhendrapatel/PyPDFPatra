
from pypdfpatra.html import HTML


def test_flex_row():
    html_content = """
    <html>
    <body style="font-family: helvetica;">
        <div style="display: flex; background: #eee; padding: 10px; border: 1px solid #ccc;">
            <div style="background: #ffcccc; padding: 5px; border: 1px solid red;">Flex Item 1</div>
            <div style="background: #ccffcc; padding: 5px; border: 1px solid green;">Flex Item 2</div>
            <div style="background: #ccccff; padding: 5px; border: 1px solid blue;">Flex Item 3</div>
        </div>
    </body>
    </html>
    """
    output_path = "test_flex.pdf"
    HTML(string=html_content).write_pdf(output_path)
    print(f"Flex test saved to {output_path}")

if __name__ == "__main__":
    test_flex_row()
