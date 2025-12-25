"""
Project initialization utilities for Pydust.

Similar to Maturin's init functionality, this module provides templates
and utilities for bootstrapping new Pydust projects.

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

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from pyz3.logging_config import get_logger
from pyz3.security import SecurityError, SecurityValidator

logger = get_logger(__name__)


def init_project_cookiecutter(
    path: Path,
    package_name: Optional[str] = None,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    description: Optional[str] = None,
    use_interactive: bool = True,
) -> None:
    """
    Initialize a new Pydust project using the cookiecutter template.

    Args:
        path: Directory to initialize the project in
        package_name: Name of the package (defaults to directory name)
        author_name: Author name (defaults to git config)
        author_email: Author email (defaults to git config)
        description: Project description
        use_interactive: Use interactive mode for cookiecutter
    """
    try:
        from cookiecutter.main import cookiecutter
    except ImportError:
        logger.error("cookiecutter is not installed")
        print("❌ Error: cookiecutter is required to initialize projects.")
        print("\nTo install cookiecutter:")
        print("  pip install cookiecutter")
        print("  # or")
        print("  uv pip install cookiecutter")
        sys.exit(1)

    logger.info(f"Initializing Pydust project with cookiecutter in {path}")

    # Find the template directory
    pyz3_package = Path(__file__).parent
    template_path = pyz3_package / "pyZ3-template"

    if not template_path.exists():
        logger.error(f"Template not found at {template_path}")
        print(f"❌ Error: Template directory not found at {template_path}")
        print("\nPlease ensure pyZ3-template is in the repository root.")
        sys.exit(1)

    # Prepare cookiecutter context
    extra_context = {}

    if package_name:
        extra_context["project_name"] = package_name.replace("_", " ").title()
    else:
        extra_context["project_name"] = path.name.replace("-", " ").replace("_", " ").title()

    if author_name:
        extra_context["author_name"] = author_name

    if author_email:
        extra_context["author_email"] = author_email

    if description:
        extra_context["description"] = description

    # Get git user info if not provided
    if not author_name or not author_email:
        git_name, git_email_full = get_git_user_info()
        if not author_name and "<" in git_email_full:
            # Parse "Name <email>" format
            parts = git_email_full.split("<")
            extra_context["author_name"] = parts[0].strip()
            if len(parts) > 1:
                extra_context["author_email"] = parts[1].rstrip(">").strip()

    try:
        # Run cookiecutter
        # Determine output directory - if initializing in current directory,
        # we need to let cookiecutter create the project folder
        output_dir = path.parent if path != Path.cwd() else Path.cwd()

        # Build cookiecutter kwargs
        cookiecutter_kwargs = {
            "no_input": not use_interactive,
            "extra_context": extra_context,
        }

        # Only specify output_dir if not current directory
        # to let cookiecutter create the project folder
        if path != Path.cwd():
            cookiecutter_kwargs["output_dir"] = str(output_dir)

        cookiecutter(
            str(template_path),
            **cookiecutter_kwargs,
        )

        print("\n✅ Project initialized successfully!")
        logger.info("Project initialized successfully with cookiecutter")

    except Exception as e:
        logger.error(f"Failed to initialize project with cookiecutter: {e}")
        print(f"❌ Error: Failed to initialize project: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Alias for backward compatibility
init_project = init_project_cookiecutter


def get_git_user_info() -> tuple[str, str]:
    """Get git user name and email if available."""
    name = "Your Name <your.email@example.com>"
    try:
        git_name = subprocess.check_output(
            ["git", "config", "user.name"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        git_email = subprocess.check_output(
            ["git", "config", "user.email"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if git_name and git_email:
            name = f"{git_name} <{git_email}>"
            logger.debug(f"Detected git user: {name}")
    except subprocess.TimeoutExpired:
        logger.warning("Git config command timed out")
    except subprocess.CalledProcessError as e:
        logger.debug(f"Git config not available: {e}")
    except FileNotFoundError:
        logger.debug("Git not found in PATH")
    except Exception as e:
        logger.warning(f"Unexpected error getting git info: {e}")
    return name, name


def new_project(name: str, path: Optional[Path] = None) -> None:
    """
    Create a new Pydust project in a new directory.

    Args:
        name: Name of the project
        path: Parent directory (defaults to current directory)
    """
    logger.info(f"Creating new project: {name}")

    if path is None:
        path = Path.cwd()

    is_valid, error, sanitized_name = SecurityValidator.sanitize_package_name(name)
    if not is_valid:
        logger.error(f"Invalid project name: {error}")
        print(f"❌ Error: {error}")
        sys.exit(1)

    project_path = path / sanitized_name

    if project_path.exists():
        logger.error(f"Directory already exists: {sanitized_name}")
        print(f"❌ Error: Directory '{sanitized_name}' already exists!")
        sys.exit(1)

    logger.debug(f"Creating project at {project_path}")
    init_project_cookiecutter(project_path, package_name=sanitized_name)
