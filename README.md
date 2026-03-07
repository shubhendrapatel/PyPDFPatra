# 📄 PyPDFPatra

**PyPDFPatra** is a high-performance, standards-compliant HTML-to-PDF layout engine for Python. 

Heavily inspired by the excellent [WeasyPrint](https://weasyprint.org/) project, PyPDFPatra aims to build upon its foundational concepts by strictly following W3C HTML/CSS layout specifications as closely as possible, while moving the heavy "Layout Box" calculations from the Python interpreter into a **Cython-powered C-core**. This hybrid architecture allows for high-speed rendering of large documents while maintaining the accessibility and ease of a pure Python API.

---

## 🚀 Key Features

*   **Speed:** A compiled Cython engine that handles millions of layout calculations at the hardware level.
*   **Memory Efficient:** Uses low-level C-structs to process 1,000+ page documents with a minimal RAM footprint.
*   **Modern CSS:** Built-in support for Flexbox, CSS Grid, and Paged Media (Headers, Footers, Page Numbering).

---

## 🛠️ Architecture: The Double-Tree System

PyPDFPatra uses a unique dual-layered architecture to separate content from geometry:

1.  **The Node Tree (DOM):** A Python-accessible structure representing your HTML.
2.  **The Box Tree (The Engine):** A hidden, compiled Cython layer where coordinates ($x, y, w, h$) are calculated using raw C-math.

This allows you to manipulate document structure in Python while the **"Yantra" (Machine)** handles the heavy lifting in the background.

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
