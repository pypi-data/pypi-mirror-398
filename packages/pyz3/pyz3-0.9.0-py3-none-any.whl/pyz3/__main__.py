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

import argparse
import sys
from pathlib import Path

from pyz3 import buildzig, config, deps, deploy, develop, init, watch
from pyz3 import wheel as wheel_module
from pyz3.logging_config import get_logger

logger = get_logger(__name__)

parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="command", required=True)

debug_sp = sub.add_parser(
    "debug",
    help="Compile a Zig file with debug symbols. Useful for running from an IDE.",
)
debug_sp.add_argument("entrypoint")

build_sp = sub.add_parser(
    "build",
    help="Build a zig-based python extension.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
build_sp.add_argument("-z", "--zig-exe", help="zig executable path")
build_sp.add_argument("-b", "--build-zig", default="build.zig", help="build.zig file")
build_sp.add_argument("-m", "--self-managed", default=False, action="store_true", help="self-managed mode")
build_sp.add_argument(
    "-a",
    "--limited-api",
    default=True,
    action="store_true",
    help="use limited python c-api",
)
build_sp.add_argument("-p", "--prefix", default="", help="prefix of built extension")
build_sp.add_argument(
    "extensions",
    nargs="+",
    help="space separated list of extension '<path>' or '<name>=<path>' entries",
)

watch_sp = sub.add_parser(
    "watch",
    help="Watch Zig files and rebuild on changes",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
watch_sp.add_argument(
    "-o",
    "--optimize",
    default="Debug",
    choices=["Debug", "ReleaseSafe", "ReleaseFast", "ReleaseSmall"],
    help="optimization level",
)
watch_sp.add_argument(
    "-t",
    "--test",
    action="store_true",
    help="run tests after rebuild",
)
watch_sp.add_argument(
    "--pytest",
    action="store_true",
    help="run pytest instead of zig test",
)
watch_sp.add_argument(
    "pytest_args",
    nargs="*",
    help="additional arguments to pass to pytest (only with --pytest)",
)

# Maturin-like commands
init_sp = sub.add_parser(
    "init",
    help="Initialize a new pyz3 project in the current directory",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
init_sp.add_argument(
    "-n",
    "--name",
    help="package name (defaults to directory name)",
)
init_sp.add_argument(
    "-a",
    "--author",
    help="author name (defaults to git config)",
)
init_sp.add_argument(
    "--description",
    help="project description",
)
init_sp.add_argument(
    "--email",
    help="author email",
)
init_sp.add_argument(
    "--no-interactive",
    action="store_true",
    help="non-interactive mode",
)

new_sp = sub.add_parser(
    "new",
    help="Create a new pyz3 project directory",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
new_sp.add_argument(
    "name",
    help="name of the project",
)
new_sp.add_argument(
    "-p",
    "--path",
    type=Path,
    help="parent directory (defaults to current directory)",
)

develop_sp = sub.add_parser(
    "develop",
    help="Build and install the project in development mode (like pip install -e .)",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
develop_sp.add_argument(
    "-o",
    "--optimize",
    default="Debug",
    choices=["Debug", "ReleaseSafe", "ReleaseFast", "ReleaseSmall"],
    help="optimization level",
)
develop_sp.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="verbose output",
)
develop_sp.add_argument(
    "-e",
    "--extras",
    nargs="+",
    help="optional extras to install (e.g., dev, test)",
)
develop_sp.add_argument(
    "--build-only",
    action="store_true",
    help="only build extension modules without installing",
)

build_wheel_sp = sub.add_parser(
    "build-wheel",
    help="Build Python wheels for distribution (alias for python -m pyz3.wheel)",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
build_wheel_sp.add_argument(
    "--platform",
    choices=[p.value for p in wheel_module.Platform],
    help="target platform (default: current platform)",
)
build_wheel_sp.add_argument(
    "--all-platforms",
    action="store_true",
    help="build for all supported platforms",
)
build_wheel_sp.add_argument(
    "--optimize",
    choices=["Debug", "ReleaseSafe", "ReleaseFast", "ReleaseSmall"],
    default="ReleaseFast",
    help="optimization level",
)
build_wheel_sp.add_argument(
    "--output-dir",
    default="dist",
    help="output directory",
)
build_wheel_sp.add_argument(
    "--no-clean",
    action="store_true",
    help="don't clean before building",
)
build_wheel_sp.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="verbose output",
)

# Dependency management commands
add_sp = sub.add_parser(
    "add",
    help="Add a C/C++ library dependency to the project",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
add_sp.add_argument(
    "source",
    help="GitHub URL, Git URL, or local path to the C/C++ library",
)
add_sp.add_argument(
    "-n",
    "--name",
    help="override dependency name (defaults to repo name)",
)
add_sp.add_argument(
    "--headers",
    nargs="+",
    help="main headers to expose (auto-detected if not specified)",
)
add_sp.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="verbose output",
)

list_deps_sp = sub.add_parser(
    "list",
    help="List all C/C++ dependencies in the project",
)

remove_sp = sub.add_parser(
    "remove",
    help="Remove a C/C++ dependency from the project",
)
remove_sp.add_argument(
    "name",
    help="name of the dependency to remove",
)

# Deploy command
deploy_sp = sub.add_parser(
    "deploy",
    help="Upload built wheels to PyPI or another repository",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
deploy_sp.add_argument(
    "--dist-dir",
    default="dist",
    help="directory containing built wheels",
)
deploy_sp.add_argument(
    "--repository",
    help="repository URL (defaults to PyPI)",
)
deploy_sp.add_argument(
    "--username",
    help="repository username (use __token__ for PyPI tokens)",
)
deploy_sp.add_argument(
    "--password",
    help="repository password or API token",
)
deploy_sp.add_argument(
    "--no-skip-existing",
    action="store_true",
    help="don't skip files that already exist",
)
deploy_sp.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="verbose output",
)

# Check command
check_sp = sub.add_parser(
    "check",
    help="Check built wheels for common errors",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
check_sp.add_argument(
    "--dist-dir",
    default="dist",
    help="directory containing built wheels",
)
check_sp.add_argument(
    "--strict",
    action="store_true",
    help="enable strict checking",
)


def main():
    args = parser.parse_args()

    if args.command == "debug":
        debug(args)

    elif args.command == "build":
        build(args)

    elif args.command == "watch":
        watch_mode(args)

    elif args.command == "init":
        init_project(args)

    elif args.command == "new":
        new_project(args)

    elif args.command == "develop":
        develop_mode(args)

    elif args.command == "build-wheel":
        build_wheel(args)

    elif args.command == "add":
        add_dependency(args)

    elif args.command == "list":
        list_deps(args)

    elif args.command == "remove":
        remove_dependency(args)

    elif args.command == "deploy":
        deploy_packages(args)

    elif args.command == "check":
        check_packages(args)


def _parse_exts(exts: list[str], limited_api: bool = True, prefix: str = "") -> list[config.ExtModule]:
    """parses extensions entries, accepts '<name>=<path>' or <path>"""
    _exts = []

    def _add_ext(name, path: Path):
        _exts.append(config.ExtModule(name=name, root=str(path), limited_api=limited_api, prefix=prefix))

    def _check_path(path: Path):
        assert path.exists(), f"path does not exist: {path}"
        assert path.suffix == ".zig" and path.is_file(), f"path must be a zig file: {path}"

    for elem in exts:
        if "=" in elem:
            name, path = elem.split("=")
            path = Path(path)
            _check_path(path)
            _add_ext(name, path)
        else:  # assume elem is a <path>
            path = Path(elem)
            _check_path(path)
            if len(path.parts) > 1:  # >1 part
                parts = (path.parent / (prefix + path.stem)).parts
                name = ".".join(parts)
                _add_ext(name, path)
            else:  # 1 part
                name = prefix + path.stem
                _add_ext(name, path)
    return _exts


def build(args):
    """Given a list of '<name>=<path>' or '<path>' entries, builds zig-based python extensions"""
    _extensions = _parse_exts(exts=args.extensions, limited_api=args.limited_api, prefix=args.prefix)
    buildzig.zig_build(
        argv=["install", f"-Dpython-exe={sys.executable}", "-Doptimize=ReleaseSafe"],
        conf=config.ToolPydust(
            zig_exe=args.zig_exe,
            build_zig=args.build_zig,
            self_managed=args.self_managed,
            ext_module=_extensions,
        ),
    )


def debug(args):
    """Given an entrypoint file, compile it for test debugging. Placing it in a well-known location."""
    entrypoint = args.entrypoint
    buildzig.zig_build(["install", f"-Ddebug-root={entrypoint}"])


def watch_mode(args):
    """Watch Zig files and rebuild on changes."""
    if args.pytest:
        watch.watch_pytest(optimize=args.optimize, pytest_args=args.pytest_args or [])
    else:
        watch.watch_and_rebuild(optimize=args.optimize, test_mode=args.test)


def init_project(args):
    """Initialize a new pyz3 project in the current directory."""
    author_name = None
    author_email = args.email if hasattr(args, "email") else None

    if args.author and "<" in args.author:
        parts = args.author.split("<")
        author_name = parts[0].strip()
        if len(parts) > 1 and not author_email:
            author_email = parts[1].rstrip(">").strip()
    elif args.author:
        author_name = args.author

    init.init_project_cookiecutter(
        path=Path.cwd(),
        package_name=args.name,
        author_name=author_name,
        author_email=author_email,
        description=args.description if hasattr(args, "description") else None,
        use_interactive=not args.no_interactive if hasattr(args, "no_interactive") else True,
    )


def new_project(args):
    """Create a new pyz3 project directory."""
    init.new_project(
        name=args.name,
        path=args.path,
    )


def develop_mode(args):
    """Build and install the project in development mode."""
    if args.build_only:
        develop.develop_build_only(
            optimize=args.optimize,
            verbose=args.verbose,
        )
    else:
        develop.develop_install(
            optimize=args.optimize,
            verbose=args.verbose,
            extras=args.extras,
        )


def build_wheel(args):
    """Build Python wheels for distribution."""
    builder = wheel_module.WheelBuilder()

    if args.all_platforms:
        print("Building wheels for all platforms...")
        wheels = builder.build_all_platforms(
            clean=not args.no_clean,
            verbose=args.verbose,
        )
        print(f"\n✓ Built {len(wheels)} wheels:")
        for wheel in wheels:
            print(f"  - {wheel.name}")
    else:
        wheel_path = wheel_module.build_wheel(
            platform=args.platform,
            optimize=args.optimize,
            output_dir=args.output_dir,
            clean=not args.no_clean,
            verbose=args.verbose,
        )
        print(f"\n✓ Wheel built: {wheel_path}")


def add_dependency(args):
    """Add a C/C++ dependency to the project."""
    deps.add_dependency(
        source=args.source,
        name=args.name,
        headers=args.headers,
        verbose=args.verbose,
    )


def list_deps(args):
    """List all dependencies in the project."""
    deps.list_dependencies()


def remove_dependency(args):
    """Remove a dependency from the project."""
    deps.remove_dependency(args.name)


def deploy_packages(args):
    """Deploy/upload built wheels to PyPI."""
    deploy.deploy_to_pypi(
        dist_dir=args.dist_dir,
        repository=args.repository,
        username=args.username,
        password=args.password,
        skip_existing=not args.no_skip_existing,
        verbose=args.verbose,
    )


def check_packages(args):
    """Check built wheels for common errors."""
    if not deploy.check_package(
        dist_dir=args.dist_dir,
        strict=args.strict,
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()
