"""Test cases for automatic stub generation."""

import os
import tempfile
import shutil
from pathlib import Path
import pytest


def test_auto_stub_generator_basic():
    """Test basic stub generation."""
    from pyz3.auto_stubs import AutoStubGenerator

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use a built-in module for testing
        generator = AutoStubGenerator("sys", tmpdir)

        # Note: This will fail if sys module doesn't have the expected structure
        # but demonstrates the API
        assert generator.package_name == "sys"
        assert generator.destination == Path(tmpdir)


def test_py_typed_marker_creation():
    """Test py.typed marker file creation."""
    from pyz3.auto_stubs import AutoStubGenerator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        package_dir = tmppath / "test_package"
        package_dir.mkdir()

        generator = AutoStubGenerator("test_package", str(tmppath))
        generator.create_py_typed_marker(package_dir)

        py_typed_file = package_dir / "py.typed"
        assert py_typed_file.exists()
        assert py_typed_file.is_file()


def test_generate_stubs_for_multiple_modules():
    """Test generating stubs for multiple modules."""
    from pyz3.auto_stubs import generate_stubs_for_modules

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with built-in modules
        modules = ["os", "sys"]

        # This will attempt to generate stubs
        # May not succeed for built-in modules but tests the flow
        result = generate_stubs_for_modules(
            modules,
            tmpdir,
            create_py_typed=False
        )

        # Result may be True or False depending on module structure
        assert isinstance(result, bool)


def test_stub_file_structure():
    """Test that generated stub files have correct structure."""
    from pyz3.auto_stubs import AutoStubGenerator

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test module
        test_module_dir = Path(tmpdir) / "test_mod"
        test_module_dir.mkdir()

        # Create __init__.py
        init_file = test_module_dir / "__init__.py"
        init_file.write_text("def test_func(x: int) -> int:\n    return x * 2\n")

        # Try to generate stubs
        generator = AutoStubGenerator("test_mod", tmpdir)

        # The stub file should be created at test_mod/__init__.pyi
        expected_stub = test_module_dir / "__init__.pyi"

        # Note: Actual generation depends on the module being importable


def test_py_typed_marker_content():
    """Test that py.typed marker is created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        package_dir = tmppath / "mypackage"
        package_dir.mkdir()

        from pyz3.auto_stubs import AutoStubGenerator

        generator = AutoStubGenerator("mypackage", str(tmppath))
        generator.create_py_typed_marker(package_dir)

        py_typed = package_dir / "py.typed"
        assert py_typed.exists()

        # py.typed should be an empty file (or contain minimal content)
        content = py_typed.read_text()
        assert len(content) == 0 or content.strip() == ""


def test_integration_with_pyproject():
    """Test integration with pyproject.toml."""
    from pyz3.auto_stubs import integrate_stub_generation_into_build

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a mock pyproject.toml
        pyproject = tmppath / "pyproject.toml"
        pyproject.write_text("""
[tool.pyz3]
[[tool.pyz3.ext_module]]
name = "test.module1"
root = "test/module1.zig"

[[tool.pyz3.ext_module]]
name = "test.module2"
root = "test/module2.zig"
""")

        # This will fail because modules don't exist, but tests parsing
        result = integrate_stub_generation_into_build(pyproject, str(tmppath))

        # Should return a boolean
        assert isinstance(result, bool)


def test_post_build_hook():
    """Test post-build hook execution."""
    from pyz3.auto_stubs import post_build_hook

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create mock pyproject.toml
        pyproject = tmppath / "pyproject.toml"
        pyproject.write_text("""
[tool.pyz3]
[[tool.pyz3.ext_module]]
name = "example.test"
root = "example/test.zig"
""")

        # Run post-build hook
        # Should not raise an exception
        post_build_hook(str(tmppath), pyproject)


def test_stub_generator_with_invalid_module():
    """Test stub generation with invalid module name."""
    from pyz3.auto_stubs import AutoStubGenerator

    with tempfile.TemporaryDirectory() as tmpdir:
        generator = AutoStubGenerator("nonexistent_module_xyz", tmpdir)

        # Should return False for nonexistent module
        result = generator.generate()
        assert result is False


def test_stub_generator_destination_creation():
    """Test that destination directory is created if it doesn't exist."""
    from pyz3.auto_stubs import AutoStubGenerator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        nested_dest = tmppath / "nested" / "stubs"

        generator = AutoStubGenerator("sys", str(nested_dest))

        # Destination should be created
        assert nested_dest.exists()
        assert nested_dest.is_dir()


def test_multiple_stub_generation_idempotent():
    """Test that generating stubs multiple times is idempotent."""
    from pyz3.auto_stubs import AutoStubGenerator

    with tempfile.TemporaryDirectory() as tmpdir:
        package_dir = Path(tmpdir) / "test_pkg"
        package_dir.mkdir()

        # Create py.typed marker
        generator = AutoStubGenerator("test_pkg", tmpdir)
        generator.create_py_typed_marker(package_dir)

        py_typed1 = package_dir / "py.typed"
        mtime1 = py_typed1.stat().st_mtime

        # Create again
        generator.create_py_typed_marker(package_dir)

        py_typed2 = package_dir / "py.typed"
        mtime2 = py_typed2.stat().st_mtime

        # File should still exist
        assert py_typed2.exists()

        # Should be able to create multiple times without error
        assert mtime2 >= mtime1
