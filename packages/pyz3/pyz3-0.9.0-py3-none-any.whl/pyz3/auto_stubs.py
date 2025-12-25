"""
Automatic stub generation integration for pyz3.

This module integrates stub generation into the build process,
ensuring type stubs are always up-to-date with the compiled modules.
"""

import hashlib
import os
import sys
import importlib
import subprocess
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def _file_hash(path: Path) -> str:
    """Compute MD5 hash of file contents for change detection."""
    if not path.exists():
        return ""
    return hashlib.md5(path.read_bytes()).hexdigest()


def _get_stub_cache_file(package_name: str, destination: Path) -> Path:
    """Get the cache file path for stub generation metadata."""
    return destination / f".{package_name}.stub_cache"


def _needs_stub_regeneration(module_path: Path, stub_file: Path, cache_file: Path) -> bool:
    """Check if stubs need to be regenerated based on file hashes."""
    if not stub_file.exists():
        return True

    if not cache_file.exists():
        return True

    try:
        # Read cached hash
        cached_hash = cache_file.read_text().strip()
        current_hash = _file_hash(module_path)

        return cached_hash != current_hash
    except Exception:
        # If anything goes wrong, regenerate to be safe
        return True


def _update_stub_cache(module_path: Path, cache_file: Path) -> None:
    """Update the stub cache with current module hash."""
    try:
        current_hash = _file_hash(module_path)
        cache_file.write_text(current_hash)
    except Exception as e:
        logger.warning(f"Failed to update stub cache: {e}")


class AutoStubGenerator:
    """Automatic stub file generator for pyz3 modules."""

    def __init__(self, package_name: str, destination: str = "."):
        self.package_name = package_name
        self.destination = Path(destination)
        self.destination.mkdir(parents=True, exist_ok=True)

    def generate(self, force: bool = False) -> bool:
        """Generate stub files for the package.

        Args:
            force: If True, regenerate stubs even if cache indicates they're up-to-date

        Returns:
            bool: True if generation succeeded, False otherwise
        """
        try:
            # Try to find the compiled module file
            try:
                module = importlib.import_module(self.package_name)
                if hasattr(module, '__file__') and module.__file__:
                    module_path = Path(module.__file__)
                else:
                    module_path = None
            except ImportError:
                module_path = None
                logger.warning(f"Could not import {self.package_name} to check cache")

            # Check if we need to regenerate
            stub_file = self.destination / f"{self.package_name.replace('.', '/')}.pyi"
            cache_file = _get_stub_cache_file(self.package_name, self.destination)

            if not force and module_path:
                if not _needs_stub_regeneration(module_path, stub_file, cache_file):
                    logger.info(f"✓ Stubs for {self.package_name} are up-to-date (cached)")
                    return True

            logger.info(f"📝 Generating stubs for {self.package_name}")

            # Import the generate_stubs module
            from pyz3.generate_stubs import generate_stubs

            # Generate stubs
            generate_stubs(self.package_name, str(self.destination), check=False)

            # Update cache
            if module_path:
                _update_stub_cache(module_path, cache_file)

            logger.info(f"✓ Stubs generated successfully in {self.destination}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate stubs: {e}")
            return False

    def create_py_typed_marker(self, package_path: Optional[Path] = None) -> None:
        """Create py.typed marker file for PEP 561 compliance.

        Args:
            package_path: Path to the package directory. If None, uses package_name
        """
        if package_path is None:
            # Try to find the package path
            try:
                module = importlib.import_module(self.package_name.split('.')[0])
                if hasattr(module, '__path__'):
                    package_path = Path(module.__path__[0])
                elif hasattr(module, '__file__'):
                    package_path = Path(module.__file__).parent
                else:
                    logger.warning("Could not determine package path for py.typed marker")
                    return
            except ImportError:
                logger.warning(f"Could not import {self.package_name} to create py.typed marker")
                return

        if package_path:
            py_typed_file = package_path / "py.typed"
            py_typed_file.touch(exist_ok=True)
            logger.info(f"Created py.typed marker at {py_typed_file}")


def generate_stubs_for_modules(
    modules: List[str],
    destination: str = ".",
    create_py_typed: bool = True
) -> bool:
    """Generate stubs for multiple modules.

    Args:
        modules: List of module names to generate stubs for
        destination: Destination directory for stub files
        create_py_typed: Whether to create py.typed marker files

    Returns:
        bool: True if all stubs generated successfully
    """
    success = True

    for module_name in modules:
        generator = AutoStubGenerator(module_name, destination)

        if not generator.generate():
            success = False
            logger.error(f"Failed to generate stubs for {module_name}")
            continue

        if create_py_typed:
            generator.create_py_typed_marker()

    return success


def integrate_stub_generation_into_build(
    pyproject_path: Path,
    destination: str = "."
) -> bool:
    """Integrate stub generation into the build process.

    Reads pyproject.toml to find all ext_modules and generates stubs for them.

    Args:
        pyproject_path: Path to pyproject.toml
        destination: Destination directory for stub files

    Returns:
        bool: True if all stubs generated successfully
    """
    try:
        import tomli
    except ImportError:
        try:
            import tomllib as tomli
        except ImportError:
            logger.error("Neither tomli nor tomllib available. Install tomli for Python < 3.11")
            return False

    try:
        with open(pyproject_path, 'rb') as f:
            config = tomli.load(f)

        # Get list of extension modules
        ext_modules = config.get('tool', {}).get('pyz3', {}).get('ext_module', [])

        if not ext_modules:
            logger.warning("No extension modules found in pyproject.toml")
            return True

        module_names = [mod['name'] for mod in ext_modules if 'name' in mod]

        logger.info(f"Found {len(module_names)} modules to generate stubs for")

        return generate_stubs_for_modules(module_names, destination)

    except Exception as e:
        logger.error(f"Error reading pyproject.toml: {e}")
        return False


def post_build_hook(build_lib: str, pyproject_path: Optional[Path] = None) -> None:
    """Post-build hook to automatically generate stubs.

    This function should be called after building extension modules.

    Args:
        build_lib: Path to the build library directory
        pyproject_path: Path to pyproject.toml (defaults to current directory)
    """
    if pyproject_path is None:
        pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        logger.warning(f"pyproject.toml not found at {pyproject_path}")
        return

    logger.info("Running post-build stub generation...")
    success = integrate_stub_generation_into_build(pyproject_path, build_lib)

    if success:
        logger.info("Stub generation completed successfully")
    else:
        logger.warning("Some stub files may not have been generated")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python -m pyz3.auto_stubs <package_name> [destination]")
        sys.exit(1)

    package_name = sys.argv[1]
    destination = sys.argv[2] if len(sys.argv) > 2 else "."

    generator = AutoStubGenerator(package_name, destination)
    if generator.generate():
        generator.create_py_typed_marker()
        sys.exit(0)
    else:
        sys.exit(1)
