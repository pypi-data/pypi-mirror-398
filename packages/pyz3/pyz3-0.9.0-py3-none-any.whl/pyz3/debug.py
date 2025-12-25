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

import os
import subprocess
import sys
import tempfile
import traceback
from enum import Enum
from pathlib import Path
from typing import Any


class LogLevel(Enum):
    """Debug log levels matching Zig implementation."""
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


def enableDebug():
    """Enable debug mode (placeholder for Zig-level functionality)."""
    pass


def disableDebug():
    """Disable debug mode (placeholder for Zig-level functionality)."""
    pass


class DebugHelper:
    """Helper for debugging Pydust extensions."""

    @staticmethod
    def get_extension_path(module_name: str) -> Path | None:
        """Get the path to a loaded extension module."""
        try:
            mod = sys.modules.get(module_name)
            if mod and hasattr(mod, "__file__"):
                return Path(mod.__file__)
        except Exception:
            pass
        return None

    @staticmethod
    def get_debug_symbols_info(module_name: str) -> dict[str, Any]:
        """Check if debug symbols are available for a module."""
        ext_path = DebugHelper.get_extension_path(module_name)
        if not ext_path or not ext_path.exists():
            return {"has_symbols": False, "reason": "Module not found"}

        # Check for debug symbols using file command
        try:
            result = subprocess.run(
                ["file", str(ext_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = result.stdout.lower()

            has_symbols = "not stripped" in output or "debug" in output

            return {
                "has_symbols": has_symbols,
                "path": str(ext_path),
                "file_info": result.stdout.strip(),
            }
        except Exception as e:
            return {"has_symbols": False, "reason": str(e)}

    @staticmethod
    def attach_debugger(module_name: str, debugger: str = "lldb") -> str:
        """Generate command to attach debugger to Python process with module loaded.

        Args:
            module_name: Name of the extension module
            debugger: Either 'lldb' or 'gdb'

        Returns:
            Command string to run in a terminal
        """
        ext_path = DebugHelper.get_extension_path(module_name)
        if not ext_path:
            return f"# Error: Module {module_name} not found"

        pid = os.getpid()

        if debugger == "lldb":
            return f"""# Attach LLDB to current process:
lldb -p {pid}

# Then in LLDB, run:
# (lldb) image add {ext_path}
# (lldb) breakpoint set --name your_function_name
# (lldb) continue
"""
        elif debugger == "gdb":
            return f"""# Attach GDB to current process:
gdb -p {pid}

# Then in GDB, run:
# (gdb) add-symbol-file {ext_path}
# (gdb) break your_function_name
# (gdb) continue
"""
        else:
            return f"# Unknown debugger: {debugger}"

    @staticmethod
    def print_mixed_traceback():
        """Print a traceback showing both Python and Zig frames."""
        print("\n" + "=" * 70)
        print("MIXED PYTHON/ZIG TRACEBACK")
        print("=" * 70)

        # Python traceback
        print("\n--- Python Stack ---")
        traceback.print_stack()

        print("\n" + "=" * 70 + "\n")

    @staticmethod
    def enable_core_dumps():
        """Enable core dumps for debugging crashes."""
        try:
            import resource

            # Set unlimited core dump size
            resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            print("✅ Core dumps enabled. Core files will be saved on crashes.")
            print(f"   Current directory: {os.getcwd()}")
        except Exception as e:
            print(f"❌ Failed to enable core dumps: {e}")

    @staticmethod
    def run_with_debugger(script: str, debugger: str = "lldb") -> int:
        """Run a Python script under a debugger.

        Args:
            script: Path to Python script
            debugger: Either 'lldb' or 'gdb'

        Returns:
            Exit code
        """
        script_path = Path(script)
        if not script_path.exists():
            print(f"❌ Script not found: {script}")
            return 1

        if debugger == "lldb":
            cmd = ["lldb", "--", sys.executable, str(script_path)]
        elif debugger == "gdb":
            cmd = ["gdb", "--args", sys.executable, str(script_path)]
        else:
            print(f"❌ Unknown debugger: {debugger}")
            return 1

        print(f"🐛 Starting {debugger}...")
        print(f"   Command: {' '.join(cmd)}")
        print("\nTip: Set breakpoints before running. In lldb/gdb:")
        print("  (lldb) breakpoint set --name function_name")
        print("  (gdb) break function_name")
        print("")

        return subprocess.call(cmd)


class BreakpointContext:
    """Context manager that pauses execution for debugger attachment."""

    def __init__(self, message: str = "Breakpoint hit"):
        self.message = message

    def __enter__(self):
        print(f"\n🔴 {self.message}")
        print(f"   PID: {os.getpid()}")
        print("   Attach debugger or press Enter to continue...")
        input()
        return self

    def __exit__(self, *args):
        print("   Continuing...\n")


def breakpoint_here(message: str = "Debug breakpoint"):
    """Pause execution and wait for debugger or user input.

    Usage:
        from pyz3.debug import breakpoint_here

        # In your code:
        breakpoint_here("About to call problematic function")
    """
    with BreakpointContext(message):
        pass


def inspect_extension(module_name: str):
    """Print detailed information about an extension module."""
    print(f"\n{'=' * 70}")
    print(f"Extension Module: {module_name}")
    print('=' * 70)

    # Module path
    path = DebugHelper.get_extension_path(module_name)
    if path:
        print(f"\n📁 Path: {path}")
        print(f"   Size: {path.stat().st_size:,} bytes")
    else:
        print("\n❌ Module not loaded or path not found")
        return

    # Debug symbols
    print("\n🔍 Debug Symbols:")
    symbols = DebugHelper.get_debug_symbols_info(module_name)
    if symbols.get("has_symbols"):
        print("   ✅ Debug symbols present")
    else:
        print("   ❌ No debug symbols found")
        if "reason" in symbols:
            print(f"   Reason: {symbols['reason']}")

    # File info
    if "file_info" in symbols:
        print(f"\n📄 File Info:")
        print(f"   {symbols['file_info']}")

    # Debugger commands
    print(f"\n🐛 Debugger Commands:")
    print("   LLDB:")
    print(f"   $ lldb -p {os.getpid()}")
    print(f"   (lldb) image add {path}")
    print("")
    print("   GDB:")
    print(f"   $ gdb -p {os.getpid()}")
    print(f"   (gdb) add-symbol-file {path}")

    print("\n" + "=" * 70 + "\n")


def create_debug_session_script(module_name: str, output_path: str | None = None) -> Path:
    """Create a script that starts a debug session for a module.

    Args:
        module_name: Name of the extension module
        output_path: Where to save the script (default: temp file)

    Returns:
        Path to the created script
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".py", prefix="debug_session_")
        os.close(fd)

    script_content = f'''#!/usr/bin/env python3
"""
Debug session for {module_name}
Generated by Pydust Debug Helper
"""

import sys
from pyz3.debug import DebugHelper, breakpoint_here, inspect_extension

# Enable core dumps
DebugHelper.enable_core_dumps()

# Import the module
try:
    import {module_name}
    print(f"✅ Module {{module_name!r}} loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import {{module_name!r}}: {{e}}")
    sys.exit(1)

# Inspect the module
inspect_extension("{module_name}")

# Pause here to attach debugger
print("\\n🔴 Pausing for debugger attachment...")
print(f"   PID: {{os.getpid()}}")
print("   Press Enter to continue or attach debugger now...")
input()

# Your debug code here
print("\\n✅ Starting debug session...")

# Example: Call functions, test code, etc.
# {module_name}.your_function()

print("\\n✅ Debug session complete")
'''

    script_path = Path(output_path)
    script_path.write_text(script_content)
    script_path.chmod(0o755)

    print(f"✅ Debug session script created: {script_path}")
    print(f"   Run with: python {script_path}")

    return script_path


# Convenience function aliases
dbg_break = breakpoint_here
dbg_inspect = inspect_extension
