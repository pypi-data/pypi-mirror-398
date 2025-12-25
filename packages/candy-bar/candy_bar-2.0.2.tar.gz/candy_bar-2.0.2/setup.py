from setuptools import setup, Extension
from Cython.Build import cythonize
import sys
import os
import re

# Read version from __init__.py
def get_version():
    init_file = os.path.join("pysrc", "candy_bar", "__init__.py")
    with open(init_file, "r") as f:
        content = f.read()
        match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
        if match:
            return match.group(1)
        raise RuntimeError("Unable to find version string.")

# Compiler flags
extra_compile_args = []
extra_link_args = []

if sys.platform == "darwin":
    extra_compile_args += ["-std=c++23", "-stdlib=libc++"]
    extra_link_args += ["-stdlib=libc++"]
elif sys.platform == "linux":
    extra_compile_args += ["-std=c++23"]
elif sys.platform == "win32":
    extra_compile_args += ["/std:c++23"]

extensions = [
    Extension(
        "candy_bar.core",
        sources=[
            "pysrc/candy_bar/core.pyx",
            "src/candybar.cpp",
        ],
        include_dirs=[
            "include",
        ],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
]

setup(
    version=get_version(),
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "embedsignature": True,
            "binding": True,
        },
        annotate=True,  # Generate HTML annotation files
    ),
)