"""
Deploy/publish module for Pydust projects.

Handles uploading wheels to PyPI and other package repositories.

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

import subprocess
import sys
from pathlib import Path
from typing import Optional

from pyz3.logging_config import get_logger

logger = get_logger(__name__)


def check_twine_available() -> bool:
    """Check if twine is installed."""
    try:
        import twine
        return True
    except ImportError:
        return False


def deploy_to_pypi(
    dist_dir: str = "dist",
    repository: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    skip_existing: bool = True,
    verbose: bool = False,
) -> None:
    """
    Deploy/upload built wheels to PyPI or another repository.

    Args:
        dist_dir: Directory containing built wheels
        repository: Repository URL (defaults to PyPI)
        username: PyPI username (can also use __token__ for API tokens)
        password: PyPI password or API token
        skip_existing: Skip files that already exist on the repository
        verbose: Enable verbose output

    Raises:
        SystemExit: If twine is not installed or upload fails
    """
    logger.info(f"Deploying packages from {dist_dir}")

    # Check if twine is installed
    if not check_twine_available():
        logger.error("twine is not installed")
        print("❌ Error: twine is required for publishing to PyPI.")
        print("\nTo install twine:")
        print("  pip install twine")
        sys.exit(1)

    # Check if dist directory exists and has wheels
    dist_path = Path(dist_dir)
    if not dist_path.exists():
        logger.error(f"Distribution directory not found: {dist_dir}")
        print(f"❌ Error: Distribution directory '{dist_dir}' does not exist.")
        print("\nBuild wheels first using:")
        print("  pyz3 build-wheel")
        sys.exit(1)

    wheel_files = list(dist_path.glob("*.whl"))
    tar_files = list(dist_path.glob("*.tar.gz"))
    all_files = wheel_files + tar_files

    if not all_files:
        logger.error(f"No distribution files found in {dist_dir}")
        print(f"❌ Error: No wheel (.whl) or source (.tar.gz) files found in '{dist_dir}'.")
        print("\nBuild wheels first using:")
        print("  pyz3 build-wheel")
        sys.exit(1)

    print(f"\nFound {len(all_files)} file(s) to upload:")
    for f in all_files:
        print(f"  - {f.name}")

    # Build twine command
    cmd = ["python", "-m", "twine", "upload"]

    if repository:
        cmd.extend(["--repository-url", repository])

    if username:
        cmd.extend(["--username", username])

    if password:
        cmd.extend(["--password", password])

    if skip_existing:
        cmd.append("--skip-existing")

    if verbose:
        cmd.append("--verbose")

    # Add all distribution files
    cmd.extend([str(f) for f in all_files])

    print("\n" + "=" * 60)
    print("Uploading to PyPI...")
    print("=" * 60)

    try:
        logger.debug(f"Running command: {' '.join(cmd[:3])} [credentials hidden]")
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=not verbose,
            text=True,
        )

        if verbose and result.stdout:
            print(result.stdout)

        print("\n✅ Successfully uploaded packages to PyPI!")
        logger.info("Successfully deployed packages")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upload packages: {e}")
        print(f"\n❌ Error: Failed to upload packages.")

        if e.stderr:
            print("\nError details:")
            print(e.stderr)

        print("\nCommon issues:")
        print("  1. Invalid credentials - check your PyPI username/token")
        print("  2. Version already exists - increment version in pyproject.toml")
        print("  3. Network issues - check your internet connection")
        print("\nFor PyPI API tokens, use:")
        print("  --username __token__")
        print("  --password <your-token>")

        sys.exit(1)


def check_package(
    dist_dir: str = "dist",
    strict: bool = False,
) -> bool:
    """
    Check distribution files for common errors using twine check.

    Args:
        dist_dir: Directory containing built wheels
        strict: Enable strict checking

    Returns:
        True if check passes, False otherwise
    """
    logger.info(f"Checking packages in {dist_dir}")

    if not check_twine_available():
        logger.warning("twine is not installed, skipping package check")
        print("⚠️  Warning: twine is not installed. Install with: pip install twine")
        return True

    dist_path = Path(dist_dir)
    if not dist_path.exists():
        logger.error(f"Distribution directory not found: {dist_dir}")
        print(f"❌ Error: Distribution directory '{dist_dir}' does not exist.")
        return False

    all_files = list(dist_path.glob("*.whl")) + list(dist_path.glob("*.tar.gz"))

    if not all_files:
        logger.error(f"No distribution files found in {dist_dir}")
        print(f"❌ Error: No distribution files found in '{dist_dir}'.")
        return False

    print(f"\nChecking {len(all_files)} package(s)...")

    cmd = ["python", "-m", "twine", "check"]
    if strict:
        cmd.append("--strict")
    cmd.extend([str(f) for f in all_files])

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)

        print("✅ All packages passed validation!")
        logger.info("Package check passed")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Package check failed: {e}")
        print("❌ Package check failed!")

        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)

        return False
