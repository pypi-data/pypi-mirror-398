#!/usr/bin/env python3
"""
Validate the cookiecutter template structure.
This script checks that all required files and directories exist.
"""

import json
import sys
from pathlib import Path


def validate_template():
    """Validate the template structure."""
    errors = []
    warnings = []

    # Check cookiecutter.json exists and is valid
    cookiecutter_json = Path("cookiecutter.json")
    if not cookiecutter_json.exists():
        errors.append("cookiecutter.json not found")
    else:
        try:
            with open(cookiecutter_json) as f:
                config = json.load(f)
                print(f"✓ cookiecutter.json is valid JSON")
                print(f"  Variables: {', '.join(config.keys())}")
        except json.JSONDecodeError as e:
            errors.append(f"cookiecutter.json is invalid JSON: {e}")

    # Check template directory exists
    template_dir = Path("{{cookiecutter.project_slug}}")
    if not template_dir.exists():
        errors.append("Template directory {{cookiecutter.project_slug}} not found")
        return errors, warnings

    print(f"✓ Template directory exists: {template_dir}")

    # Check required files in template
    required_files = [
        "pyproject.toml",
        "README.md",
        "build.py",
        "LICENSE",
        ".gitignore",
        "{{cookiecutter.package_name}}/__init__.py",
        "{{cookiecutter.package_name}}/{{cookiecutter.module_name}}.pyi",
        "src/{{cookiecutter.zig_file_name}}.zig",
        "test/__init__.py",
        "test/test_{{cookiecutter.zig_file_name}}.py",
        ".github/workflows/ci.yml",
        ".github/workflows/publish.yml",
        ".vscode/extensions.json",
        ".vscode/launch.json",
    ]

    print("\nChecking required files:")
    for file in required_files:
        file_path = template_dir / file
        if file_path.exists():
            print(f"  ✓ {file}")
        else:
            errors.append(f"Missing required file: {file}")
            print(f"  ✗ {file} (MISSING)")

    # Check for cookiecutter variables in files
    print("\nChecking for cookiecutter variables in key files:")
    files_to_check = [
        "pyproject.toml",
        "README.md",
        "test/test_{{cookiecutter.zig_file_name}}.py",
    ]

    for file in files_to_check:
        file_path = template_dir / file
        if file_path.exists():
            content = file_path.read_text()
            if "{{" in content and "}}" in content:
                print(f"  ✓ {file} contains cookiecutter variables")
            else:
                warnings.append(f"{file} doesn't contain cookiecutter variables")
                print(f"  ⚠ {file} doesn't contain cookiecutter variables")

    # Check hooks directory
    hooks_dir = Path("hooks")
    if hooks_dir.exists():
        print(f"\n✓ Hooks directory exists")
        post_gen = hooks_dir / "post_gen_project.py"
        if post_gen.exists():
            print(f"  ✓ post_gen_project.py exists")
            if post_gen.stat().st_mode & 0o111:
                print(f"  ✓ post_gen_project.py is executable")
            else:
                warnings.append("post_gen_project.py is not executable")
                print(f"  ⚠ post_gen_project.py is not executable")
        else:
            warnings.append("post_gen_project.py not found")
    else:
        warnings.append("hooks directory not found")

    return errors, warnings


def main():
    """Run validation and report results."""
    print("=" * 60)
    print("pyZ3 Template Validator")
    print("=" * 60)
    print()

    errors, warnings = validate_template()

    print("\n" + "=" * 60)
    print("Validation Results")
    print("=" * 60)

    if errors:
        print(f"\n❌ Found {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ No errors found!")

    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✅ No warnings!")

    print()

    if errors:
        print("❌ Template validation FAILED")
        return 1
    elif warnings:
        print("⚠️  Template validation PASSED with warnings")
        return 0
    else:
        print("✅ Template validation PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
