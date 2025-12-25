"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import contextlib
import hashlib
import os
import shutil
import subprocess
import sys
import sysconfig
import textwrap
from pathlib import Path
from typing import TextIO

import pyz3
from pyz3 import config

PYVER_MINOR = ".".join(str(v) for v in sys.version_info[:2])
PYVER_HEX = f"{sys.hexversion:#010x}"
PYLDLIB = sysconfig.get_config_var("LDLIBRARY")

# Handle None case (Windows) and process library name
if PYLDLIB is None:
    # On Windows, LDLIBRARY may be None, fall back to default naming
    PYLDLIB = f"python{PYVER_MINOR.replace('.', '')}"
elif ".framework/" in PYLDLIB:
    # Handle macOS Framework Python (e.g., "Python.framework/Versions/3.11/Python")
    # Extract just the library name from framework path
    # Python.framework/Versions/3.11/Python => Python
    PYLDLIB = os.path.basename(PYLDLIB)
    PYLDLIB = os.path.splitext(PYLDLIB)[0]
else:
    # Strip libpython3.11.a.so => python3.11.a
    PYLDLIB = PYLDLIB[3:] if PYLDLIB.startswith("lib") else PYLDLIB
    PYLDLIB = os.path.splitext(PYLDLIB)[0]


def _file_hash(path: Path) -> str:
    """Compute MD5 hash of file contents for change detection."""
    if not path.exists():
        return ""
    return hashlib.md5(path.read_bytes()).hexdigest()


def _needs_copy(source: Path, dest: Path) -> bool:
    """Check if source file needs to be copied to dest based on content hash."""
    if not dest.exists():
        return True
    return _file_hash(source) != _file_hash(dest)


def zig_build(argv: list[str], conf: config.ToolPydust | None = None):
    conf = conf or config.load()

    # Generate the supporting pyz3.build.zig (only if changed)
    source_build_zig = Path(pyz3.__file__).parent.joinpath("src/pyz3.build.zig")
    if _needs_copy(source_build_zig, conf.pyz3_build_zig):
        print(f"📝 Updating build script: {conf.pyz3_build_zig}")
        shutil.copy(source_build_zig, conf.pyz3_build_zig)
    else:
        print(f"✓ Build script up-to-date: {conf.pyz3_build_zig}")

    if not conf.self_managed:
        # Generate the build.zig if we're managing the ext_modules ourselves
        with conf.build_zig.open(mode="w") as f:
            generate_build_zig(f, conf)

    zig_exe = [os.path.expanduser(conf.zig_exe)] if conf.zig_exe else [sys.executable, "-m", "ziglang"]

    cmds = zig_exe + ["build", "--build-file", conf.build_zig] + argv

    subprocess.run(cmds, check=True)


def _format_zig_array(items: list[str]) -> str:
    """Format a Python list as a Zig array literal."""
    if not items:
        return "&.{}"
    formatted_items = ", ".join(f'"{item}"' for item in items)
    return f"&.{{ {formatted_items} }}"


def generate_build_zig(fileobj: TextIO, conf=None):
    """Generate the build.zig file for the current pyproject.toml.

    Initially we were calling `zig build-lib` directly, and this worked fine except it meant we
    would need to roll our own caching and figure out how to convince ZLS to pick up our dependencies.

    It's therefore easier, at least for now, to generate a build.zig in the project root and add it
    to the .gitignore. This means ZLS works as expected, we can leverage zig build caching, and the user
    can inspect the generated file to assist with debugging.
    """
    conf = conf or config.load()

    b = Writer(fileobj)

    b.writeln('const std = @import("std");')
    b.writeln('const py = @import("./pyz3.build.zig");')
    b.writeln()

    with b.block("pub fn build(b: *std.Build) void"):
        b.write(
            """
            const target = b.standardTargetOptionsQueryOnly(.{});
            const optimize = b.standardOptimizeOption(.{});

            const test_step = b.step("test", "Run library tests");

            const pyz3 = py.addPyZ3(b, .{
                .test_step = test_step,
            });
            """
        )

        for ext_module in conf.ext_modules:
            # TODO(ngates): fix the out filename for non-limited modules
            assert ext_module.limited_api, "Only limited_api is supported for now"

            # Convert Windows backslashes to forward slashes for Zig compatibility
            root_path = str(ext_module.root).replace("\\", "/")

            # Format C/C++ configuration
            c_sources = _format_zig_array(ext_module.c_sources)
            c_include_dirs = _format_zig_array(ext_module.c_include_dirs)
            c_libraries = _format_zig_array(ext_module.c_libraries)
            c_flags = _format_zig_array(ext_module.c_flags)
            ld_flags = _format_zig_array(ext_module.ld_flags)

            module_config = f"""
                _ = pyz3.addPythonModule(.{{
                    .name = "{ext_module.name}",
                    .root_source_file = b.path("{root_path}"),
                    .limited_api = {str(ext_module.limited_api).lower()},
                    .target = target,
                    .optimize = optimize,
                    .c_sources = {c_sources},
                    .c_include_dirs = {c_include_dirs},
                    .c_libraries = {c_libraries},
                    .c_flags = {c_flags},
                    .ld_flags = {ld_flags},
                }});
                """

            b.write(module_config)


class Writer:
    def __init__(self, fileobj: TextIO) -> None:
        self.f = fileobj
        self._indent = 0

    @contextlib.contextmanager
    def indent(self):
        self._indent += 4
        yield
        self._indent -= 4

    @contextlib.contextmanager
    def block(self, text: str = ""):
        self.write(text)
        self.writeln(" {")
        with self.indent():
            yield
        self.writeln()
        self.writeln("}")
        self.writeln()

    def write(self, text: str):
        if "\n" in text:
            text = textwrap.dedent(text).strip() + "\n\n"
        self.f.write(textwrap.indent(text, self._indent * " "))

    def writeln(self, text: str = ""):
        self.write(text)
        self.f.write("\n")
