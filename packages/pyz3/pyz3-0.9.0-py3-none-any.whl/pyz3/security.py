"""
Security utilities for Pydust.

Provides validation, sanitization, and security checks for various operations.

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

import keyword
import os
import platform
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class SecurityError(Exception):
    """Raised when a security violation is detected."""

    pass


class SecurityValidator:
    """Validates and sanitizes user input for security."""

    # Trusted Git hosting providers
    TRUSTED_GIT_HOSTS = {
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "git.sr.ht",  # sourcehut
        "codeberg.org",
    }

    # Maximum sizes
    MAX_PACKAGE_NAME_LENGTH = 100
    MAX_PATH_LENGTH = 250 if platform.system() == "Windows" else 4000
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_REPO_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_HEADERS = 20

    @staticmethod
    def validate_git_url(url: str) -> tuple[bool, Optional[str]]:
        """
        Validate a Git URL for security.

        Args:
            url: The Git URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Invalid URL format: {e}"

        # Only allow HTTPS
        if parsed.scheme != "https":
            return False, "Only HTTPS URLs are allowed for security reasons"

        # Check if hostname is in trusted list
        if parsed.hostname not in SecurityValidator.TRUSTED_GIT_HOSTS:
            return (
                False,
                f"Untrusted Git host: {parsed.hostname}. "
                f"Allowed hosts: {', '.join(SecurityValidator.TRUSTED_GIT_HOSTS)}",
            )

        # Check for suspicious characters
        if any(char in url for char in [";", "&", "|", "$", "`"]):
            return False, "URL contains suspicious characters"

        # Validate path doesn't contain directory traversal
        if ".." in parsed.path:
            return False, "URL path contains directory traversal"

        return True, None

    @staticmethod
    def validate_local_path(path: str, project_root: Path) -> tuple[bool, Optional[str], Optional[Path]]:
        """
        Validate a local filesystem path for security.

        Args:
            path: The path to validate
            project_root: The project root directory

        Returns:
            Tuple of (is_valid, error_message, resolved_path)
        """
        try:
            local_path = Path(path).resolve()
        except Exception as e:
            return False, f"Invalid path: {e}", None

        # Check path length
        if len(str(local_path)) > SecurityValidator.MAX_PATH_LENGTH:
            return False, f"Path exceeds maximum length of {SecurityValidator.MAX_PATH_LENGTH}", None

        # Check if path exists
        if not local_path.exists():
            return False, f"Path does not exist: {local_path.name}", None

        # Check if it's trying to escape reasonable bounds
        # Allow one level above project root (e.g., ../sibling-project)
        try:
            local_path.relative_to(project_root.parent)
        except ValueError:
            return False, "Path is outside allowed directory", None

        # Check for symbolic link attacks
        if local_path.is_symlink():
            try:
                target = local_path.readlink()
                # If absolute, verify it's in allowed area
                if target.is_absolute():
                    try:
                        target.relative_to(project_root.parent)
                    except ValueError:
                        return False, "Symbolic link points outside allowed directory", None
            except Exception as e:
                return False, f"Could not verify symbolic link: {e}", None

        return True, None, local_path

    @staticmethod
    def sanitize_package_name(name: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Sanitize and validate a package name.

        Args:
            name: The package name to sanitize

        Returns:
            Tuple of (is_valid, error_message, sanitized_name)
        """
        if not name:
            return False, "Package name cannot be empty", None

        # Check length before sanitization
        if len(name) > SecurityValidator.MAX_PACKAGE_NAME_LENGTH:
            return False, f"Package name too long (max {SecurityValidator.MAX_PACKAGE_NAME_LENGTH})", None

        # Sanitize: keep only alphanumeric and underscore
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in name)

        # Ensure it's not all underscores
        if sanitized.replace("_", "") == "":
            return False, "Package name must contain alphanumeric characters", None

        # Ensure starts with letter or underscore
        if sanitized[0].isdigit():
            sanitized = "_" + sanitized

        # Check against Python keywords
        if keyword.iskeyword(sanitized):
            sanitized = sanitized + "_pkg"

        # Check against common system modules (just the most dangerous ones)
        dangerous_names = {"os", "sys", "subprocess", "shutil", "pathlib"}
        if sanitized in dangerous_names:
            return False, f"Package name conflicts with system module: {sanitized}", None

        return True, None, sanitized

    @staticmethod
    def validate_file_write(path: Path, force: bool = False) -> tuple[bool, Optional[str]]:
        """
        Validate that a file can be safely written.

        Args:
            path: The file path to write
            force: Whether to allow overwriting existing files

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if it's a symbolic link
        if path.is_symlink():
            return False, "Refusing to write to symbolic link"

        # Check if file exists and we're not forcing
        if path.exists() and not force:
            return False, "File already exists (use --force to overwrite)"

        # Check parent directory is writable
        parent = path.parent
        if parent.exists():
            if not os.access(parent, os.W_OK):
                return False, "No write permission to parent directory"

            # Check parent directory ownership (warning only)
            if hasattr(os, "getuid"):  # Unix-like systems
                try:
                    parent_stat = parent.stat()
                    if parent_stat.st_uid != os.getuid():
                        # Just a warning, not blocking
                        pass
                except Exception:
                    pass

        return True, None

    @staticmethod
    def safe_write_text(path: Path, content: str, force: bool = False) -> bool:
        """
        Safely write text to a file with atomic operations.

        Args:
            path: The file path
            content: The content to write
            force: Whether to overwrite existing files

        Returns:
            True if successful

        Raises:
            SecurityError: If validation fails
            IOError: If write fails
        """
        # Validate
        is_valid, error = SecurityValidator.validate_file_write(path, force)
        if not is_valid:
            raise SecurityError(error)

        # Atomic write using temporary file
        temp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            temp_path.write_text(content, encoding="utf-8")
            # Atomic rename (on most systems)
            temp_path.replace(path)
            return True
        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise IOError(f"Failed to write file: {e}")

    @staticmethod
    def check_directory_size(path: Path, max_size: int = MAX_REPO_SIZE) -> tuple[bool, int]:
        """
        Check if a directory is under the size limit.

        Args:
            path: Directory to check
            max_size: Maximum size in bytes

        Returns:
            Tuple of (is_under_limit, total_size)
        """
        total_size = 0
        try:
            for item in path.rglob("*"):
                if item.is_file() and not item.is_symlink():
                    try:
                        total_size += item.stat().st_size
                        if total_size > max_size:
                            return False, total_size
                    except Exception:
                        # Skip files we can't stat
                        pass
        except Exception:
            # If we can't scan, assume it's okay
            pass

        return True, total_size

    @staticmethod
    def scan_for_git_hooks(repo_path: Path) -> list[str]:
        """
        Scan for potentially dangerous git hooks.

        Args:
            repo_path: Path to git repository

        Returns:
            List of found executable hooks
        """
        hooks = []
        hooks_dir = repo_path / ".git" / "hooks"

        if not hooks_dir.exists():
            return hooks

        try:
            for hook_file in hooks_dir.iterdir():
                if hook_file.is_file() and not hook_file.name.endswith(".sample"):
                    # Check if executable
                    if os.access(hook_file, os.X_OK):
                        hooks.append(hook_file.name)
        except Exception:
            pass

        return hooks

    @staticmethod
    def escape_toml_string(s: str) -> str:
        """
        Escape a string for safe inclusion in TOML.

        Args:
            s: String to escape

        Returns:
            Escaped string safe for TOML
        """
        # Basic escaping - in production, use tomli_w
        s = s.replace("\\", "\\\\")
        s = s.replace('"', '\\"')
        s = s.replace("\n", "\\n")
        s = s.replace("\r", "\\r")
        s = s.replace("\t", "\\t")
        return f'"{s}"'
