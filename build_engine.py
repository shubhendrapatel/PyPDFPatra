"""
build_engine.py
~~~~~~~~~~~~~~~
Direct Cython build script for the PyPDFPatra engine.
Run:  python build_engine.py build_ext --inplace
"""

from Cython.Build import cythonize
from setuptools import Extension, setup

ext_modules = cythonize(
    [
        Extension(
            "pypdfpatra.engine.tree",
            sources=["src/pypdfpatra/engine/tree.pyx"],
            extra_compile_args=["/O2"]
            if __import__("sys").platform == "win32"
            else ["-O3"],
        ),
    ],
    compiler_directives={
        "boundscheck": False,
        "wraparound": False,
        "language_level": "3",
    },
    force=True,  # Always recompile, don't use cached .c files
)

setup(
    name="pypdfpatra-engine",
    ext_modules=ext_modules,
    package_dir={"": "src"},
)
