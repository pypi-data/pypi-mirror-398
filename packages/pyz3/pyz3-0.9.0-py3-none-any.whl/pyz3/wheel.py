#!/usr/bin/env python3
"""
Wheel building and cross-compilation support for Pydust.

This module provides utilities for building Python wheels for multiple platforms,
including cross-compilation support.
"""

import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class Platform(Enum):
    """Supported target platforms."""

    LINUX_X86_64 = "linux-x86_64"
    LINUX_AARCH64 = "linux-aarch64"
    MACOS_X86_64 = "macos-x86_64"
    MACOS_ARM64 = "macos-arm64"
    WINDOWS_X64 = "windows-x64"

    @property
    def zig_target(self) -> str:
        """Get Zig target triple for this platform."""
        mapping = {
            Platform.LINUX_X86_64: "x86_64-linux-gnu",
            Platform.LINUX_AARCH64: "aarch64-linux-gnu",
            Platform.MACOS_X86_64: "x86_64-macos",
            Platform.MACOS_ARM64: "aarch64-macos",
            Platform.WINDOWS_X64: "x86_64-windows-gnu",
        }
        return mapping[self]

    @property
    def wheel_platform(self) -> str:
        """Get wheel platform tag."""
        mapping = {
            Platform.LINUX_X86_64: "manylinux_2_17_x86_64.manylinux2014_x86_64",
            Platform.LINUX_AARCH64: "manylinux_2_17_aarch64.manylinux2014_aarch64",
            Platform.MACOS_X86_64: "macosx_10_9_x86_64",
            Platform.MACOS_ARM64: "macosx_11_0_arm64",
            Platform.WINDOWS_X64: "win_amd64",
        }
        return mapping[self]

    @classmethod
    def current(cls) -> "Platform":
        """Detect current platform."""
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "linux":
            if machine in ("x86_64", "amd64"):
                return cls.LINUX_X86_64
            elif machine in ("aarch64", "arm64"):
                return cls.LINUX_AARCH64
        elif system == "darwin":
            if machine == "x86_64":
                return cls.MACOS_X86_64
            elif machine == "arm64":
                return cls.MACOS_ARM64
        elif system == "windows":
            if machine in ("amd64", "x86_64"):
                return cls.WINDOWS_X64

        raise RuntimeError(f"Unsupported platform: {system} {machine}")


@dataclass
class BuildConfig:
    """Configuration for building wheels."""

    target_platform: Platform
    optimize: str = "ReleaseFast"  # Debug, ReleaseSafe, ReleaseFast, ReleaseSmall
    python_version: Optional[str] = None  # e.g., "3.11", if None uses current
    output_dir: Path = Path("dist")

    def __post_init__(self):
        if self.python_version is None:
            self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"


class WheelBuilder:
    """Build wheels for Pydust projects."""

    def __init__(self, project_root: Path = Path.cwd()):
        self.project_root = project_root
        self.pyproject = project_root / "pyproject.toml"

        if not self.pyproject.exists():
            raise FileNotFoundError(f"pyproject.toml not found in {project_root}")

    def build(
        self,
        config: BuildConfig,
        *,
        clean: bool = True,
        verbose: bool = False,
    ) -> Path:
        """
        Build a wheel for the specified platform.

        Args:
            config: Build configuration
            clean: Whether to clean build artifacts first
            verbose: Enable verbose output

        Returns:
            Path to the built wheel file
        """
        print(f"Building wheel for {config.target_platform.value}...")

        # Clean if requested
        if clean:
            self._clean()

        # Set up environment for cross-compilation
        env = os.environ.copy()
        env["ZIG_TARGET"] = config.target_platform.zig_target
        env["PYDUST_OPTIMIZE"] = config.optimize

        # Build the extension modules
        cmd = [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--outdir",
            str(config.output_dir),
        ]

        if verbose:
            cmd.append("--verbose")

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            env=env,
            capture_output=not verbose,
            text=True,
        )

        if result.returncode != 0:
            print(f"Build failed with exit code {result.returncode}")
            if result.stderr:
                print(f"Error output:\n{result.stderr}")
            raise RuntimeError("Wheel build failed")

        # Find the built wheel
        wheels = list(config.output_dir.glob("*.whl"))
        if not wheels:
            raise RuntimeError("No wheel file found after build")

        wheel_path = max(wheels, key=lambda p: p.stat().st_mtime)
        print(f"✓ Built wheel: {wheel_path.name}")

        return wheel_path

    def build_all_platforms(
        self,
        platforms: Optional[List[Platform]] = None,
        **kwargs,
    ) -> List[Path]:
        """
        Build wheels for multiple platforms.

        Args:
            platforms: List of platforms to build for, or None for all
            **kwargs: Additional arguments passed to build()

        Returns:
            List of paths to built wheel files
        """
        if platforms is None:
            platforms = list(Platform)

        wheels = []
        for platform_enum in platforms:
            config = BuildConfig(target_platform=platform_enum)
            try:
                wheel_path = self.build(config, **kwargs)
                wheels.append(wheel_path)
            except Exception as e:
                print(f"✗ Failed to build for {platform_enum.value}: {e}")

        return wheels

    def _clean(self):
        """Clean build artifacts."""
        dirs_to_clean = ["build", "dist", ".zig-cache", "zig-out"]

        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                import shutil
                shutil.rmtree(dir_path)
                print(f"Cleaned {dir_name}/")


def build_wheel(
    platform: Optional[str] = None,
    optimize: str = "ReleaseFast",
    output_dir: str = "dist",
    clean: bool = True,
    verbose: bool = False,
) -> Path:
    """
    Convenience function to build a wheel.

    Args:
        platform: Target platform (e.g., "linux-x86_64"), or None for current
        optimize: Optimization level
        output_dir: Output directory for wheel
        clean: Clean before building
        verbose: Verbose output

    Returns:
        Path to the built wheel
    """
    if platform is None:
        target = Platform.current()
    else:
        target = Platform(platform)

    config = BuildConfig(
        target_platform=target,
        optimize=optimize,
        output_dir=Path(output_dir),
    )

    builder = WheelBuilder()
    return builder.build(config, clean=clean, verbose=verbose)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Python wheels for Pydust projects")
    parser.add_argument(
        "--platform",
        choices=[p.value for p in Platform],
        help="Target platform (default: current platform)",
    )
    parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Build for all supported platforms",
    )
    parser.add_argument(
        "--optimize",
        choices=["Debug", "ReleaseSafe", "ReleaseFast", "ReleaseSmall"],
        default="ReleaseFast",
        help="Optimization level",
    )
    parser.add_argument(
        "--output-dir",
        default="dist",
        help="Output directory",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't clean before building",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    builder = WheelBuilder()

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
        wheel_path = build_wheel(
            platform=args.platform,
            optimize=args.optimize,
            output_dir=args.output_dir,
            clean=not args.no_clean,
            verbose=args.verbose,
        )
        print(f"\n✓ Wheel built: {wheel_path}")
