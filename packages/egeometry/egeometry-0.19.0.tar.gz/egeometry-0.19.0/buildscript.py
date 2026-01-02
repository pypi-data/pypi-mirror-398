__all__ = ()

import os
import shutil
import sys
from pathlib import Path
from platform import system

from setuptools import Distribution
from setuptools import Extension
from setuptools.command.build_ext import build_ext

try:
    from codegen import generate_geometry_files
except ImportError as ex:
    generate_geometry_files = None  # type: ignore


_coverage_compile_args: list[str] = []
_coverage_links_args: list[str] = []
if os.environ.get("EGEOMETRY_BUILD_WITH_COVERAGE", "0") == "1":
    if system() == "Windows":
        print("Cannot build with coverage on windows.")
        sys.exit(1)
    _coverage_compile_args = ["-fprofile-arcs", "-ftest-coverage", "-O0"]
    _coverage_links_args = ["-fprofile-arcs"]

_egeometry = Extension(
    "egeometry._egeometry",
    include_dirs=["vendor/glm", "vendor/emath/include", "src/egeometry"],
    sources=["src/egeometry/_egeometry.cpp"],
    language="c++11",
    extra_compile_args=_coverage_compile_args + ([] if os.name == "nt" else ["-std=c++11", "-w"]),
    extra_link_args=_coverage_links_args + ([] if os.name == "nt" else ["-lstdc++"]),
)


def _build() -> None:
    if (
        os.environ.get("EGEOMETRY_GENERATE_GEOMETRY_FILES", "0") == "1"
        and generate_geometry_files is not None
    ):
        generate_geometry_files(Path("src/egeometry"))
    if os.environ.get("EGEOMETRY_BUILD_EXTENSION", "1") == "1":
        cmd = build_ext(Distribution({"name": "extended", "ext_modules": [_egeometry]}))
        cmd.ensure_finalized()
        cmd.run()
        for output in cmd.get_outputs():
            dest = str(Path("src/egeometry/") / Path(output).name)
            print(f"copying {output} to {dest}...")
            shutil.copyfile(output, dest)


if __name__ == "__main__":
    _build()
