# Contributing to PyPDFPatra

Thank you for your interest in contributing to PyPDFPatra! This document provides guidelines for setting up your development environment and contributing to the core Cython engine.

## Development Setup

### 1. Prerequisites
- **Python 3.8+**
- **C/C++ Compiler:**
  - Windows: Visual Studio Build Tools with C++ workload.
  - Linux: `gcc` or `clang`.
  - macOS: Xcode Command Line Tools.

### 2. Environment Setup
```bash
git clone https://github.com/shubhendrapatel/PyPDFPatra.git
cd PyPDFPatra
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e .
```

## Working with the Cython Engine

The core layout logic is implemented in `src/pypdfpatra/engine/tree.pyx`. 

### Building the Engine
Whenever you modify `.pyx` or `.pxd` files, you must rebuild the extension:
```bash
python build_engine.py build_ext --inplace
```

### Best Practices
- **Minimize Python Interop:** Keep performance-critical loops inside Cython using `cdef` and C types.
- **Type Safety:** Always use `.pxd` files to share type definitions between Cython modules.
- **Memory Management:** Be careful with manual memory management if using raw C pointers.

## Quality Control

### Linting and Formatting
We use **Ruff** for linting and formatting. Before submitting code, please run:
```bash
# Check for linting errors
ruff check .
# Fix linting errors automatically where possible
ruff check --fix .
# Format code
ruff format .
```

## Submitting Changes
1. Fork the repository.
2. Create a feature branch.
3. Ensure all tests pass: `pytest` and `python example/test_coverage.py`.
4. Run Ruff to ensure code style consistency.
5. Submit a Pull Request with a clear description of the changes.
