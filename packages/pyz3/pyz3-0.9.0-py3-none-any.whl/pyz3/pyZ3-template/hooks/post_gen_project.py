#!/usr/bin/env python3
"""Post-generation hook for cookiecutter template."""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command and print the result."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def check_uv_installed():
    """Check if uv is installed."""
    return shutil.which("uv") is not None


def main():
    """Initialize the generated project."""
    project_dir = Path.cwd()

    print("\n" + "="*60)
    print("Initializing your Zig Python extension project...")
    print("="*60)

    # Initialize git repository
    if not (project_dir / ".git").exists():
        run_command("git init", "Initializing git repository")
        run_command("git add .", "Adding files to git")
        run_command(
            'git commit -m "Initial commit from pyz3-template"',
            "Creating initial commit"
        )

    # Check for uv and optionally initialize environment
    has_uv = check_uv_installed()
    has_poetry = shutil.which("poetry") is not None

    print("\n" + "="*60)
    print("Project setup complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. cd {{ cookiecutter.project_slug }}")

    if has_uv:
        print("\n  Using uv (recommended):")
        print("    uv venv")
        print("    source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
        print("    uv pip install -e .")
        print("    pytest")

    if has_poetry:
        print("\n  Using Poetry:")
        print("    poetry install")
        print("    poetry run pytest")

    if not has_uv and not has_poetry:
        print("\n  Using pip:")
        print("    python -m venv .venv")
        print("    source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
        print("    pip install -e .")
        print("    pytest")
        print("\n  💡 Tip: Install uv for faster dependency management:")
        print("    pip install uv")

    print("\nFor more information, visit:")
    print("  https://pyz3.fulcrum.so/latest/getting_started/")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
