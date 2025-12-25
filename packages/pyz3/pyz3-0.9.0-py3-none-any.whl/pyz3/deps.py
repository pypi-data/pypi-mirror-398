"""
C/C++ Dependency management for Pydust projects.

This module provides functionality to add C/C++ libraries to a Pydust project,
automatically generating Zig bindings and integrating them into the build system.

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

import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from pyz3.logging_config import get_logger
from pyz3.security import SecurityValidator, SecurityError

# Setup logging
logger = get_logger(__name__)


@dataclass
class Dependency:
    """Represents a C/C++ dependency."""

    name: str
    source: str  # URL or path
    version: Optional[str] = None
    include_dirs: list[str] = field(default_factory=list)
    lib_dirs: list[str] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)  # Library names to link
    headers: list[str] = field(default_factory=list)  # Main headers to expose
    cflags: list[str] = field(default_factory=list)
    ldflags: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)  # C/C++ source files
    is_header_only: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "source": self.source,
            "version": self.version,
            "include_dirs": self.include_dirs,
            "lib_dirs": self.lib_dirs,
            "libraries": self.libraries,
            "headers": self.headers,
            "cflags": self.cflags,
            "ldflags": self.ldflags,
            "source_files": self.source_files,
            "is_header_only": self.is_header_only,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Dependency":
        """Create from dictionary."""
        return cls(**data)


class DependencyManager:
    """Manages C/C++ dependencies for a Pydust project."""

    def __init__(self, project_root: Path = Path.cwd()):
        self.project_root = project_root
        self.deps_dir = project_root / "deps"
        self.bindings_dir = project_root / "bindings"
        self.deps_file = project_root / "pyz3_deps.json"

    def load_dependencies(self) -> dict[str, Dependency]:
        """Load existing dependencies from pyz3_deps.json."""
        if not self.deps_file.exists():
            return {}

        with open(self.deps_file, "r") as f:
            data = json.load(f)

        return {name: Dependency.from_dict(dep_data) for name, dep_data in data.items()}

    def save_dependencies(self, dependencies: dict[str, Dependency]) -> None:
        """Save dependencies to pyz3_deps.json."""
        data = {name: dep.to_dict() for name, dep in dependencies.items()}

        with open(self.deps_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  ✓ Updated {self.deps_file.name}")

    def add_dependency(
        self,
        source: str,
        name: Optional[str] = None,
        headers: Optional[list[str]] = None,
        verbose: bool = False,
    ) -> Dependency:
        """
        Add a C/C++ dependency to the project.

        Args:
            source: URL (GitHub, etc.) or local path
            name: Optional name override
            headers: Optional list of main headers to expose
            verbose: Enable verbose output

        Returns:
            The created Dependency object
        """
        print(f"Adding C/C++ dependency: {source}")

        # Determine if source is URL or local path
        parsed = urlparse(source)
        is_url = parsed.scheme in ("http", "https", "git")

        if is_url:
            dep = self._add_remote_dependency(source, name, verbose)
        else:
            dep = self._add_local_dependency(source, name, verbose)

        # Discover headers if not provided
        if headers:
            dep.headers = headers
        else:
            dep.headers = self._discover_headers(dep)

        # Load existing dependencies
        dependencies = self.load_dependencies()
        dependencies[dep.name] = dep

        # Save updated dependencies
        self.save_dependencies(dependencies)

        # Generate Zig bindings
        print(f"\n[2/4] Generating Zig bindings...")
        self._generate_bindings(dep, verbose)

        # Update build system
        print(f"\n[3/4] Updating build system...")
        self._update_build_system(dependencies)

        # Generate Python wrapper template
        print(f"\n[4/4] Generating Python wrapper template...")
        self._generate_python_wrapper(dep)

        print(f"\n✅ Successfully added dependency: {dep.name}")
        print(f"\nNext steps:")
        print(f"  1. Review generated bindings in: bindings/{dep.name}.zig")
        print(f"  2. Review Python wrapper in: src/{dep.name}_wrapper.zig")
        print(f"  3. Run: pyz3 develop")

        return dep

    def _add_remote_dependency(
        self, url: str, name: Optional[str], verbose: bool
    ) -> Dependency:
        """Add a dependency from a remote URL with security validation."""
        logger.info(f"Adding remote dependency from: {url}")

        # SECURITY: Validate Git URL
        is_valid, error = SecurityValidator.validate_git_url(url)
        if not is_valid:
            logger.error(f"Security validation failed: {error}")
            print(f"  ❌ Invalid URL: {error}")
            raise SecurityError(f"URL validation failed: {error}")

        print(f"  [1/4] Cloning from {url}...")

        # Extract name from URL if not provided
        if name is None:
            # Extract repo name from URL
            name = Path(urlparse(url).path).stem
            name = name.replace("-", "_").replace(".", "_")

        # SECURITY: Validate and sanitize package name
        is_valid, error, name = SecurityValidator.sanitize_package_name(name)
        if not is_valid:
            logger.error(f"Invalid package name: {error}")
            print(f"  ❌ Invalid package name: {error}")
            raise SecurityError(f"Package name validation failed: {error}")

        # Create deps directory
        try:
            self.deps_dir.mkdir(exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create deps directory: {e}")
            print(f"  ❌ Failed to create deps directory: {e}")
            raise

        dep_path = self.deps_dir / name

        # Clone the repository
        if dep_path.exists():
            logger.warning(f"Directory already exists: {name}")
            print(f"  ⚠️  Directory {dep_path} already exists, using existing...")
        else:
            try:
                # SECURITY: Safe git clone with disabled hooks and timeout
                logger.debug(f"Cloning to: {dep_path}")
                result = subprocess.run(
                    [
                        "git", "clone",
                        "--depth=1",  # Shallow clone
                        "--config", "core.hooksPath=/dev/null",  # Disable hooks
                        "--config", "core.fsmonitor=false",  # Disable fsmonitor
                        url,
                        str(dep_path)
                    ],
                    check=True,
                    capture_output=not verbose,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )
                logger.info(f"Successfully cloned to: {name}")
                print(f"  ✓ Cloned to deps/{name}")

                # SECURITY: Check for git hooks
                hooks = SecurityValidator.scan_for_git_hooks(dep_path)
                if hooks:
                    logger.warning(f"Git hooks found: {', '.join(hooks)}")
                    print(f"  ⚠️  Warning: Git hooks found: {', '.join(hooks)}")

                # SECURITY: Check repository size
                is_size_ok, size = SecurityValidator.check_directory_size(dep_path)
                if not is_size_ok:
                    logger.warning(f"Repository is large: {size // 1_000_000}MB")
                    print(f"  ⚠️  Warning: Repository is large ({size // 1_000_000}MB)")

            except subprocess.TimeoutExpired:
                logger.error("Git clone timeout after 5 minutes")
                print(f"  ❌ Clone timeout after 5 minutes")
                # Clean up partial clone
                if dep_path.exists():
                    try:
                        shutil.rmtree(dep_path)
                        logger.debug(f"Cleaned up partial clone: {dep_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up partial clone: {e}")
                raise SecurityError("Git clone timed out")

            except subprocess.CalledProcessError as e:
                logger.error(f"Git clone failed: {e}")
                print(f"  ❌ Failed to clone repository")
                if e.stderr and verbose:
                    logger.debug(f"Git stderr: {e.stderr}")
                    print(f"     {e.stderr}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error during clone: {e}")
                print(f"  ❌ Unexpected error: {e}")
                raise

        # Try to detect version from git
        version = None
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=dep_path,
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
                check=False,  # Don't raise on non-zero
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                # Sanitize version string
                if len(version) > 50:
                    version = version[:50]
                    logger.warning(f"Version string truncated to 50 chars")
                logger.debug(f"Detected version: {version}")
        except subprocess.TimeoutExpired:
            logger.debug("Git version detection timed out")
        except subprocess.SubprocessError as e:
            logger.debug(f"Could not detect git version: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error detecting version: {e}")

        # Discover include directories and source files
        include_dirs = self._discover_include_dirs(dep_path)
        source_files = self._discover_source_files(dep_path)

        dep = Dependency(
            name=name,
            source=url,
            version=version,
            include_dirs=include_dirs,
            source_files=source_files,
            is_header_only=len(source_files) == 0,
        )

        return dep

    def _add_local_dependency(
        self, path: str, name: Optional[str], verbose: bool
    ) -> Dependency:
        """Add a dependency from a local path with security validation."""
        logger.info(f"Adding local dependency from: {path}")

        # SECURITY: Validate local path
        is_valid, error, local_path = SecurityValidator.validate_local_path(
            path, self.project_root
        )
        if not is_valid:
            logger.error(f"Path validation failed: {error}")
            print(f"  ❌ Invalid path: {error}")
            raise SecurityError(f"Path validation failed: {error}")

        # Only show basename for security (don't leak full paths)
        print(f"  [1/4] Using local library at {local_path.name}...")

        if name is None:
            name = local_path.stem.replace("-", "_").replace(".", "_")

        # SECURITY: Validate and sanitize package name
        is_valid, error, name = SecurityValidator.sanitize_package_name(name)
        if not is_valid:
            logger.error(f"Invalid package name: {error}")
            print(f"  ❌ Invalid package name: {error}")
            raise SecurityError(f"Package name validation failed: {error}")

        # Discover include directories and source files
        try:
            include_dirs = self._discover_include_dirs(local_path)
            source_files = self._discover_source_files(local_path)
            logger.debug(f"Found {len(include_dirs)} include dirs, {len(source_files)} source files")
        except Exception as e:
            logger.error(f"Failed to discover library structure: {e}")
            print(f"  ❌ Failed to discover library structure: {e}")
            raise

        dep = Dependency(
            name=name,
            source=str(local_path),
            include_dirs=include_dirs,
            source_files=source_files,
            is_header_only=len(source_files) == 0,
        )

        logger.info(f"Successfully added local dependency: {name}")
        return dep

    def _discover_include_dirs(self, base_path: Path) -> list[str]:
        """Discover include directories in the dependency."""
        include_dirs = []

        # Common include directory names
        common_names = ["include", "inc", "src", "."]

        for name in common_names:
            inc_dir = base_path / name
            if not (inc_dir.exists() and inc_dir.is_dir()):
                continue

            # OPTIMIZATION: Use iterator to stop at first header found
            try:
                # Try .h files
                next(inc_dir.rglob("*.h"))
                include_dirs.append(str(inc_dir.relative_to(self.project_root)))
                continue
            except StopIteration:
                pass

            try:
                # Try .hpp files
                next(inc_dir.rglob("*.hpp"))
                include_dirs.append(str(inc_dir.relative_to(self.project_root)))
            except StopIteration:
                pass

        return include_dirs if include_dirs else [str(base_path.relative_to(self.project_root))]

    def _discover_source_files(self, base_path: Path) -> list[str]:
        """Discover C/C++ source files."""
        source_files = []

        # Look in common source directories
        for pattern in ["src/**/*.c", "src/**/*.cpp", "src/**/*.cc", "*.c", "*.cpp"]:
            for file in base_path.glob(pattern):
                if file.is_file():
                    rel_path = file.relative_to(self.project_root)
                    source_files.append(str(rel_path))

        return source_files

    def _discover_headers(self, dep: Dependency) -> list[str]:
        """Discover main headers to expose."""
        headers = []
        MAX_HEADERS = SecurityValidator.MAX_HEADERS

        for inc_dir in dep.include_dirs:
            inc_path = self.project_root / inc_dir
            # Look for headers in the root of include dir
            for ext in ["*.h", "*.hpp"]:
                for header in inc_path.glob(ext):
                    if header.is_file() and not header.is_symlink():  # SECURITY: Skip symlinks
                        headers.append(str(header.relative_to(self.project_root)))
                        if len(headers) >= MAX_HEADERS:
                            break
                if len(headers) >= MAX_HEADERS:
                    break
            if len(headers) >= MAX_HEADERS:
                break

        if len(headers) > MAX_HEADERS:
            logger.warning(f"Too many headers ({len(headers)}), limiting to {MAX_HEADERS}")
            headers = headers[:MAX_HEADERS]

        return headers

    def _generate_bindings(self, dep: Dependency, verbose: bool) -> None:
        """Generate Zig bindings using translate-c with security validation."""
        logger.debug(f"Generating bindings for {dep.name}")

        try:
            self.bindings_dir.mkdir(exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create bindings directory: {e}")
            print(f"  ❌ Failed to create bindings directory: {e}")
            raise

        binding_file = self.bindings_dir / f"{dep.name}.zig"

        if not dep.headers:
            logger.warning(f"No headers found for {dep.name}")
            print(f"  ⚠️  No headers found, creating minimal binding file...")
            content = (
                f"// Bindings for {dep.name}\n"
                f"// No headers were automatically discovered.\n"
                f"// Add C imports manually:\n\n"
                f'// const c = @cImport({{\n'
                f'//     @cInclude("your_header.h");\n'
                f'// }});\n\n'
                f"pub const c = struct {{}};\n"
            )
            try:
                SecurityValidator.safe_write_text(binding_file, content, force=True)
            except (SecurityError, IOError) as e:
                logger.error(f"Failed to write binding file: {e}")
                print(f"  ❌ Failed to write binding file: {e}")
                raise
            return

        # Create a temporary C file that includes all headers
        temp_c = self.bindings_dir / f"{dep.name}_temp.h"

        include_lines = []
        for header in dep.headers:
            # Get the header name relative to include dir
            header_path = Path(header)
            for inc_dir in dep.include_dirs:
                inc_path = Path(inc_dir)
                try:
                    rel_header = header_path.relative_to(inc_path)
                    include_lines.append(f'#include "{rel_header}"')
                    break
                except ValueError:
                    continue
            else:
                # If not in any include dir, use absolute path
                include_lines.append(f'#include "{header}"')

        temp_c.write_text("\n".join(include_lines))

        # Generate binding using @cImport style
        version_comment = f"// Version: {dep.version}" if dep.version else ""

        binding_content = f"""// Auto-generated Zig bindings for {dep.name}
// Source: {dep.source}
{version_comment}

// Import the C library
pub const c = @cImport({{
"""

        for header in dep.headers:
            header_path = Path(header)
            # Try to find the header name relative to include dirs
            for inc_dir in dep.include_dirs:
                inc_path = Path(inc_dir)
                try:
                    rel_header = header_path.relative_to(inc_path)
                    binding_content += f'    @cInclude("{rel_header}");\n'
                    break
                except ValueError:
                    continue

        binding_content += f"""}});

// Re-export commonly used types and functions
// TODO: Add convenience wrappers for common operations

// Example usage:
// const {dep.name} = @import("{dep.name}.zig");
// const value = {dep.name}.c.some_function();
"""

        # SECURITY: Use safe file write
        try:
            SecurityValidator.safe_write_text(binding_file, binding_content, force=True)
            logger.info(f"Generated bindings: {dep.name}.zig")
            print(f"  ✓ Generated bindings: {binding_file.relative_to(self.project_root)}")
        except (SecurityError, IOError) as e:
            logger.error(f"Failed to write binding file: {e}")
            print(f"  ❌ Failed to write binding file: {e}")
            raise

    def _update_build_system(self, dependencies: dict[str, Dependency]) -> None:
        """Update build.zig to include C/C++ dependencies."""
        build_zig = self.project_root / "build.zig"

        if not build_zig.exists():
            print(f"  ⚠️  build.zig not found, skipping build system update")
            return

        # Create a deps.zig file with build configuration
        deps_zig = self.bindings_dir / "deps.zig.inc"

        deps_content = """// Auto-generated dependency configuration
// Include this in your build.zig with: @import("bindings/deps.zig.inc")

const std = @import("std");

pub fn addDependencies(b: *std.Build, target: std.Build.ResolvedTarget, lib: anytype) void {
"""

        for name, dep in dependencies.items():
            deps_content += f"\n    // Dependency: {name}\n"

            # Add include paths
            for inc_dir in dep.include_dirs:
                deps_content += f'    lib.addIncludePath(b.path("{inc_dir}"));\n'

            # Add source files if not header-only
            if not dep.is_header_only and dep.source_files:
                deps_content += f"\n    // Add source files\n"
                for src_file in dep.source_files[:10]:  # Limit to avoid too many
                    deps_content += f'    lib.addCSourceFile(.{{ .file = b.path("{src_file}"), .flags = &.{{}} }});\n'

            # Link libraries
            for lib_name in dep.libraries:
                deps_content += f'    lib.linkSystemLibrary("{lib_name}");\n'

            deps_content += f"    lib.linkLibC();\n"

        deps_content += """
}
"""

        deps_zig.write_text(deps_content)
        print(f"  ✓ Generated build config: {deps_zig.relative_to(self.project_root)}")
        print(f"\n  📝 To use in build.zig, add:")
        print(f'     const deps = @import("bindings/deps.zig.inc");')
        print(f"     deps.addDependencies(b, target, lib);")

    def _generate_python_wrapper(self, dep: Dependency) -> None:
        """Generate a Python wrapper template."""
        wrapper_file = self.project_root / "src" / f"{dep.name}_wrapper.zig"

        if wrapper_file.exists():
            print(f"  ⚠️  Wrapper already exists: {wrapper_file.relative_to(self.project_root)}")
            return

        wrapper_content = f"""// Python wrapper for {dep.name}
// This is a template - customize it for your needs

const py = @import("pyz3");
const {dep.name} = @import("../bindings/{dep.name}.zig");

// Example: Expose a C function to Python
// pub fn example_function(args: struct {{ value: i32 }}) i32 {{
//     return {dep.name}.c.original_function(args.value);
// }}

// Example: Wrap a C struct
// pub const {dep.name.title()}Object = py.class(struct {{
//     const Self = @This();
//
//     pub fn __init__(self: *Self) !void {{
//         // Initialize C object
//     }}
//
//     pub fn method(self: *Self, args: struct {{}}) !i32 {{
//         // Call C method
//         return 0;
//     }}
// }});

// Register module functions
comptime {{
    // Uncomment to create a submodule for this library:
    // py.module(struct {{
    //     pub const __name__ = "{dep.name}";
    //     // Add your functions and classes here
    // }});
}}
"""

        self.project_root.joinpath("src").mkdir(exist_ok=True)
        wrapper_file.write_text(wrapper_content)
        print(f"  ✓ Generated wrapper: {wrapper_file.relative_to(self.project_root)}")

    def list_dependencies(self) -> None:
        """List all dependencies in the project."""
        dependencies = self.load_dependencies()

        if not dependencies:
            print("No dependencies installed.")
            return

        print(f"Dependencies ({len(dependencies)}):\n")

        for name, dep in dependencies.items():
            print(f"  • {name}")
            if dep.version:
                print(f"    Version: {dep.version}")
            print(f"    Source: {dep.source}")
            print(f"    Type: {'Header-only' if dep.is_header_only else 'Compiled'}")
            if dep.headers:
                print(f"    Headers: {', '.join(Path(h).name for h in dep.headers[:3])}")
            print()

    def remove_dependency(self, name: str) -> None:
        """Remove a dependency from the project."""
        dependencies = self.load_dependencies()

        if name not in dependencies:
            print(f"❌ Dependency not found: {name}")
            sys.exit(1)

        dep = dependencies[name]

        # Remove from tracking
        del dependencies[name]
        self.save_dependencies(dependencies)

        # Remove generated files
        binding_file = self.bindings_dir / f"{name}.zig"
        if binding_file.exists():
            binding_file.unlink()
            print(f"  ✓ Removed bindings: {binding_file.relative_to(self.project_root)}")

        wrapper_file = self.project_root / "src" / f"{name}_wrapper.zig"
        if wrapper_file.exists():
            print(f"  ⚠️  Wrapper file exists: {wrapper_file.relative_to(self.project_root)}")
            print(f"     Delete manually if no longer needed")

        # Update build system
        self._update_build_system(dependencies)

        print(f"\n✅ Removed dependency: {name}")


def add_dependency(
    source: str,
    name: Optional[str] = None,
    headers: Optional[list[str]] = None,
    verbose: bool = False,
) -> None:
    """Add a C/C++ dependency to the current project."""
    manager = DependencyManager()
    manager.add_dependency(source, name, headers, verbose)


def list_dependencies() -> None:
    """List all dependencies in the current project."""
    manager = DependencyManager()
    manager.list_dependencies()


def remove_dependency(name: str) -> None:
    """Remove a dependency from the current project."""
    manager = DependencyManager()
    manager.remove_dependency(name)
