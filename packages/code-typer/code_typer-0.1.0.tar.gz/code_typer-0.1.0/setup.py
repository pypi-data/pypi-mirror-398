"""Setup script for building Cython extensions.

This file is required for building the Cython extensions during wheel creation.
The actual package metadata is defined in pyproject.toml.
"""

import os
import sys

from setuptools import Extension, setup

# Check if Cython is available
try:
    from Cython.Build import cythonize

    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False


def get_extensions():
    """Get the list of extensions to build."""
    extensions = []

    # Define the Cython extension modules
    cython_modules = [
        "code_typer._fast_human",
    ]

    for module in cython_modules:
        module_path = module.replace(".", os.sep)

        if USE_CYTHON:
            # Build from .pyx source
            pyx_file = f"{module_path}.pyx"
            if os.path.exists(pyx_file):
                ext = Extension(
                    module,
                    sources=[pyx_file],
                    extra_compile_args=["-O3"] if sys.platform != "win32" else [],
                )
                extensions.append(ext)
        else:
            # Build from pre-generated .c source
            c_file = f"{module_path}.c"
            if os.path.exists(c_file):
                ext = Extension(
                    module,
                    sources=[c_file],
                    extra_compile_args=["-O3"] if sys.platform != "win32" else [],
                )
                extensions.append(ext)

    if USE_CYTHON and extensions:
        extensions = cythonize(
            extensions,
            compiler_directives={
                "language_level": "3",
                "boundscheck": False,
                "wraparound": False,
                "cdivision": True,
            },
            annotate=False,
        )

    return extensions


# Only run setup if extensions are available
ext_modules = get_extensions()

if ext_modules:
    setup(ext_modules=ext_modules)
else:
    # Pure Python fallback - no extensions to build
    setup()
