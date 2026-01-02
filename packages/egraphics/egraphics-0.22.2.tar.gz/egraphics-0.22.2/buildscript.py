from __future__ import annotations

__all__ = ()

import os
import shutil
import sys
from pathlib import Path
from platform import system

from setuptools import Distribution
from setuptools import Extension
from setuptools.command.build_ext import build_ext

_coverage_compile_args: list[str] = []
_coverage_links_args: list[str] = []
if os.environ.get("EGRAPHICS_BUILD_WITH_COVERAGE", "0") == "1":
    if system() == "Windows":
        print("Cannot build with coverage on windows.")
        sys.exit(1)
    _coverage_compile_args = ["-fprofile-arcs", "-ftest-coverage", "-O0"]
    _coverage_links_args = ["-fprofile-arcs"]

libraries: list[str] = []
extra_link_args: list[str] = []
define_macros: list[tuple[str, None]] = []
if system() == "Windows":
    libraries.extend(["opengl32", "glu32"])
elif system() == "Darwin":
    extra_link_args.extend(["-framework", "OpenGL"])
    define_macros.extend([("GL_SILENCE_DEPRECATION", None)])
else:
    libraries.extend(["GL", "GLU"])

_egraphics = Extension(
    "egraphics._egraphics",
    libraries=libraries,
    include_dirs=["src/egraphics", "vendor/glew/include", "vendor/emath/include"],
    sources=["src/egraphics/_egraphics.c", "vendor/glew/src/glew.c"],
    extra_compile_args=_coverage_compile_args,
    extra_link_args=_coverage_links_args + extra_link_args,
    define_macros=[("GLEW_STATIC", None)] + define_macros,
)


def _build() -> None:
    cmd = build_ext(Distribution({"name": "extended", "ext_modules": [_egraphics]}))
    cmd.ensure_finalized()
    cmd.run()
    for output in cmd.get_outputs():
        dest = str(Path("src/egraphics/") / Path(output).name)
        print(f"copying {output} to {dest}...")
        shutil.copyfile(output, dest)


if __name__ == "__main__":
    _build()
