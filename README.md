# 📄 PyPDFPatra

**PyPDFPatra** is a high-performance, standards-compliant HTML-to-PDF layout engine for Python. 

Heavily inspired by the excellent [WeasyPrint](https://weasyprint.org/) project, PyPDFPatra aims to build upon its foundational concepts by strictly following W3C HTML/CSS layout specifications as closely as possible, while moving the heavy "Layout Box" calculations from the Python interpreter into a **Cython-powered C-core**. This hybrid architecture allows for high-speed rendering of large documents while maintaining the accessibility and ease of a pure Python API.

---

## 🚀 Key Features

*   **Speed:** A compiled Cython engine that handles millions of layout calculations at the hardware level.
*   **W3C Standards:** Implements Block, Inline, and Table Formatting Contexts correctly.
*   **Memory Efficient:** Uses low-level C-structs to process large documents with a minimal RAM footprint.
*   **Modern CSS:** Support for complex selectors, cascading styles, and expanding shorthands.

---

## 🛠️ Architecture

PyPDFPatra uses a separation of concerns between its Python interface and its Cython layout engine. It follows a 5-step pipeline:

1.  **Parsing:** HTML is turned into a DOM Node Tree.
2.  **Styling:** CSS is matched and resolved (CSSOM).
3.  **Box Generation:** Nodes are converted into a Render Tree of Boxes.
4.  **Layout:** Geometry (x, y, width, height) is calculated.
5.  **Rendering:** Drawing commands are sent to the PDF backend.

For a detailed breakdown of the library structure and development status, see the documents in the `docs/` directory:

- [**Architecture Overview**](docs/ARCHITECTURE.md) - Deep dive into the engine design.
- [**Development Status**](docs/STATUS.md) - What features are currently implemented.
- [**Design Decisions**](docs/DECISIONS.md) - Historical context on technical choices.
- [**Supported CSS**](docs/SUPPORTED_CSS.md) - Detailed list of supported properties.
- [**Contributing Guide**](docs/CONTRIBUTING.md) - How to help build the engine.
- [**Extending Guide**](docs/EXTENDING.md) - How to add new CSS or Box types.

---

## 📦 Installation & Setup

### Prerequisites
Because PyPDFPatra uses a compiled engine, you must have a C++ compiler installed on your system:
*   **Windows:** Visual Studio Build Tools (Select "Desktop development with C++").
*   **Linux:** `gcc` or `clang` and Python development headers.
*   **macOS:** Xcode Command Line Tools.

### Development Install
```bash
# Clone the repository
git clone https://github.com
cd PyPDFPatra

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install in editable mode (This triggers the Cython compilation)
pip install -e .
```

---

## ⚖️ License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details. This permissive license means you are free to use, modify, distribute, and even sell your applications that use PyPDFPatra, as long as you include the original copyright notice.
