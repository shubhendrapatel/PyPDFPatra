from pypdfpatra.html import HTML


def test_fixed_repetition():
    html_content = """
    <html>
    <body style="font-family: helvetica;">
        <div style="position: fixed; top: 10px; left: 10px; width: 100%; background: #ffcccc; padding: 10px;">
            GLOBAL HEADER (Fixed)
        </div>

        <div style="height: 1000pt;">
            PAGE 1 CONTENT
        </div>

        <div style="height: 1000pt;">
            PAGE 2 CONTENT
        </div>

        <div style="height: 200pt;">
            PAGE 3 CONTENT
        </div>

        <div style="position: fixed; bottom: 10px; right: 10px; background: #ccffcc; padding: 5px;">
            GLOBAL FOOTER (Fixed)
        </div>
    </body>
    </html>
    """

    output_path = "test_fixed_repeat.pdf"
    HTML(string=html_content).write_pdf(output_path)
    print(f"Fixed repetition test saved to {output_path}")


if __name__ == "__main__":
    test_fixed_repetition()
