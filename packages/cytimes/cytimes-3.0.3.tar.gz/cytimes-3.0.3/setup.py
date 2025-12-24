import os, numpy as np, platform
from setuptools import setup, Extension
from Cython.Build import cythonize

# Package name
__package__ = "cytimes"


# Create Extension
def extension(src: str, include_np: bool, *extra_compile_args: str) -> Extension:
    # Prep name
    if "/" in src:
        folders: list[str] = src.split("/")
        file: str = folders.pop(-1)
    else:
        folders: list[str] = []
        file: str = src
    if "." in file:  # . remove extension
        file = file.split(".")[0]
    name = ".".join([__package__, *folders, file])

    # Prep source
    if "/" in src:
        file = src.split("/")[-1]
    else:
        file = src
    source = os.path.join("src", __package__, *folders, file)

    # Extra arguments
    extra_args = list(extra_compile_args) if extra_compile_args else None

    # Create extension
    if include_np:
        return Extension(
            name,
            [source],
            extra_compile_args=extra_args,
            include_dirs=[np.get_include()],
            define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        )
    else:
        return Extension(name, [source], extra_compile_args=extra_args)


# Build Extensions
if platform.system() == "Windows":
    extensions = [
        extension("delta.py", True),
        extension("errors.py", True),
        extension("parser.py", True),
        extension("pddt.py", True),
        extension("pydt.py", True),
        extension("utils.py", True),
    ]
else:
    extensions = [
        extension("delta.py", True, "-Wno-unreachable-code"),
        extension("errors.py", True, "-Wno-unreachable-code"),
        extension("parser.py", True, "-Wno-unreachable-code"),
        extension("pddt.py", True, "-Wno-unreachable-code"),
        extension("pydt.py", True, "-Wno-unreachable-code"),
        extension("utils.py", True, "-Wno-unreachable-code"),
    ]

# Build
setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
        annotate=True,
    ),
)
