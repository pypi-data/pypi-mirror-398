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

import hashlib
import sys
import time
from collections.abc import Callable
from pathlib import Path

from pyz3 import buildzig, config


class FileWatcher:
    """Watch files for changes and trigger callbacks."""

    def __init__(self, paths: list[Path], callback: Callable[[], None], debounce_ms: int = 500):
        self.paths = paths
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.file_hashes: dict[Path, str] = {}
        self._initialize_hashes()

    def _initialize_hashes(self):
        """Calculate initial hashes for all watched files."""
        for path in self.paths:
            if path.exists() and path.is_file():
                self.file_hashes[path] = self._hash_file(path)

    @staticmethod
    def _hash_file(path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hasher = hashlib.md5()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError):
            return ""

    def check_changes(self) -> list[Path]:
        """Check for file changes and return list of changed files."""
        changed = []
        for path in self.paths:
            if not path.exists():
                continue

            current_hash = self._hash_file(path)
            if path not in self.file_hashes or self.file_hashes[path] != current_hash:
                self.file_hashes[path] = current_hash
                changed.append(path)

        return changed

    def watch(self):
        """Start watching files and trigger callback on changes."""
        print(f"👀 Watching {len(self.paths)} files for changes...")
        print("   Press Ctrl+C to stop")
        print()

        last_trigger = 0

        try:
            while True:
                changed = self.check_changes()
                if changed:
                    # Debounce - don't trigger too frequently
                    now = time.time() * 1000
                    if now - last_trigger > self.debounce_ms:
                        last_trigger = now
                        print(f"\n🔄 Changes detected in {len(changed)} file(s):")
                        for path in changed:
                            print(f"   - {path}")
                        print()
                        self.callback()

                time.sleep(0.5)  # Check every 500ms
        except KeyboardInterrupt:
            print("\n👋 Stopping file watcher")


def watch_and_rebuild(optimize: str = "Debug", test_mode: bool = False):
    """Watch Zig source files and rebuild on changes.

    Args:
        optimize: Optimization level (Debug, ReleaseSafe, ReleaseFast, ReleaseSmall)
        test_mode: If True, also run tests after rebuild
    """
    conf = config.load()

    # Collect all Zig source files to watch
    watch_paths = []

    # Watch extension module roots
    for ext_module in conf.ext_modules:
        if ext_module.root.exists():
            watch_paths.append(ext_module.root)

    # Watch pyz3 source files if in dev mode
    pyz3_src = Path(__file__).parent / "src"
    if pyz3_src.exists():
        for zig_file in pyz3_src.rglob("*.zig"):
            watch_paths.append(zig_file)

    if not watch_paths:
        print("❌ No Zig files found to watch")
        sys.exit(1)

    print(f"🚀 pyz3 Watch Mode")
    print(f"   Optimize: {optimize}")
    print(f"   Test mode: {test_mode}")
    print()

    def rebuild():
        """Rebuild the project."""
        print("🔨 Rebuilding...")
        start = time.time()

        try:
            buildzig.zig_build(
                [
                    "install",
                    f"-Doptimize={optimize}",
                    f"-Dpython-exe={sys.executable}",
                ],
                conf=conf,
            )

            if test_mode:
                print("🧪 Running tests...")
                buildzig.zig_build(
                    [
                        "test",
                        f"-Doptimize={optimize}",
                        f"-Dpython-exe={sys.executable}",
                    ],
                    conf=conf,
                )

            elapsed = time.time() - start
            print(f"✅ Build completed in {elapsed:.2f}s")
        except Exception as e:
            print(f"❌ Build failed: {e}")

    # Initial build
    rebuild()

    # Start watching
    watcher = FileWatcher(watch_paths, rebuild)
    watcher.watch()


def watch_pytest(optimize: str = "Debug", pytest_args: list[str] | None = None):
    """Watch mode that runs pytest on changes.

    Args:
        optimize: Optimization level
        pytest_args: Additional arguments to pass to pytest
    """
    import subprocess

    conf = config.load()

    # Collect all source files to watch (both Zig and Python)
    watch_paths = []

    # Watch extension module roots
    for ext_module in conf.ext_modules:
        if ext_module.root.exists():
            watch_paths.append(ext_module.root)

    # Watch Python test files
    if conf.root:
        root_path = Path(conf.root)
        for py_file in root_path.rglob("test_*.py"):
            watch_paths.append(py_file)

    if not watch_paths:
        print("❌ No files found to watch")
        sys.exit(1)

    print(f"🚀 pyz3 Pytest Watch Mode")
    print(f"   Optimize: {optimize}")
    print()

    def run_tests():
        """Run pytest."""
        print("🧪 Running pytest...")
        start = time.time()

        try:
            cmd = [sys.executable, "-m", "pytest", f"--zig-optimize={optimize}"]
            if pytest_args:
                cmd.extend(pytest_args)

            result = subprocess.run(cmd)

            elapsed = time.time() - start
            if result.returncode == 0:
                print(f"✅ Tests passed in {elapsed:.2f}s")
            else:
                print(f"❌ Tests failed in {elapsed:.2f}s")
        except Exception as e:
            print(f"❌ Test run failed: {e}")

    # Initial test run
    run_tests()

    # Start watching
    watcher = FileWatcher(watch_paths, run_tests)
    watcher.watch()
