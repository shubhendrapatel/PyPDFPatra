
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
    output_path = "test_flex_row.pdf"
    HTML(string=html_content).write_pdf(output_path)
    print(f"Flex Row test saved to {output_path}")

def test_flex_column():
    html_content = """
    <html>
    <body style="font-family: helvetica;">
        <div style="display: flex; flex-direction: column; background: #eee; padding: 10px; border: 1px solid #ccc;">
            <div style="background: #ffcccc; padding: 5px; border: 1px solid red;">Flex Column 1</div>
            <div style="background: #ccffcc; padding: 5px; border: 1px solid green;">Flex Column 2</div>
            <div style="background: #ccccff; padding: 5px; border: 1px solid blue;">Flex Column 3</div>
        </div>
    </body>
    </html>
    """
    output_path = "test_flex_column.pdf"
    HTML(string=html_content).write_pdf(output_path)
    print(f"Flex Column test saved to {output_path}")

def test_flex_alignment():
    html_content = """
    <html>
    <body style="font-family: helvetica;">
        <h3>Flex Row: justify-content: center; align-items: center;</h3>
        <div style="display: flex; justify-content: center; align-items: center; background: #eee; height: 100px; border: 1px solid #ccc;">
            <div style="background: red; width: 50px; height: 50px;"></div>
            <div style="background: green; width: 50px; height: 30px;"></div>
            <div style="background: blue; width: 50px; height: 70px;"></div>
        </div>

        <h3>Flex Row: justify-content: space-between; align-items: flex-end;</h3>
        <div style="display: flex; justify-content: space-between; align-items: flex-end; background: #eee; height: 100px; border: 1px solid #ccc;">
            <div style="background: red; width: 50px; height: 50px;"></div>
            <div style="background: green; width: 50px; height: 30px;"></div>
            <div style="background: blue; width: 50px; height: 70px;"></div>
        </div>
    </body>
    </html>
    """
    output_path = "test_flex_alignment.pdf"
    HTML(string=html_content).write_pdf(output_path)
    print(f"Flex Alignment test saved to {output_path}")

if __name__ == "__main__":
    test_flex_row()
    test_flex_column()
    test_flex_alignment()
