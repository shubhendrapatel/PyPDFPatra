from pypdfpatra.html import HTML


def test_absolute_positioning():
    html_content = """
    <html>
    <head>
        <style>
            .container {
                width: 500px;
                height: 300px;
                border: 2px solid black;
                position: relative;
                margin: 20px;
            }
            .abs-box {
                position: absolute;
                top: 50px;
                left: 100px;
                width: 100px;
                height: 50px;
                background-color: red;
                color: white;
            }
            .rel-box {
                position: relative;
                top: 20px;
                left: 30px;
                background-color: blue;
                color: white;
                padding: 10px;
            }
            .stack-bottom {
                position: absolute;
                bottom: 10px;
                right: 10px;
                width: 150px;
                height: 30px;
                background-color: green;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="abs-box">Absolute box</div>
            <div class="rel-box">Relative box shifted</div>
            <div class="stack-bottom">Bottom right box</div>
            <p>Normal flow content should not be affected by absolute boxes.</p>
        </div>
    </body>
    </html>
    """

    output_path = "test_positioning.pdf"
    HTML(string=html_content).write_pdf(output_path)
    print(f"PDF saved to {output_path}")


if __name__ == "__main__":
    test_absolute_positioning()
