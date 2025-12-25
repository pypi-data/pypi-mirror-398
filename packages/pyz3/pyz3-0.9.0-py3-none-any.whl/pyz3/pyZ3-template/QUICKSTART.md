# Quick Start Guide

Get up and running with the pyZ3 Cookiecutter Template in 5 minutes.

## Prerequisites

Install these tools (choose one dependency manager):

```bash
# Required
pip install cookiecutter

# Choose ONE of these for dependency management:
pip install uv          # Option 1: uv (recommended - fastest)
# OR
# Install Poetry         # Option 2: Poetry (full-featured)
# OR
# Use built-in pip       # Option 3: Standard pip (no install needed)
```

## Create Your Project

### 1. Generate from template

**From local directory:**
```bash
cookiecutter /path/to/pyZ3-template
```

**From GitHub (when published):**
```bash
cookiecutter gh:yourusername/pyZ3-template
```

### 2. Answer the prompts

```
project_name [My Zig Python Extension]: Fast Math Library
project_slug [fast-math-library]:
package_name [fast_math_library]:
zig_file_name [fast_math_library]:
module_name [_lib]:
description [A Python extension module written in Zig using pyZ3]: Fast mathematical operations using Zig
author_name [Your Name]: Jane Developer
author_email [you@example.com]: jane@example.com
version [0.1.0]:
python_version [3.11]:
```

### 3. Set up your development environment

Navigate to your project:
```bash
cd fast-math-library
```

Choose your setup method:

#### Option A: uv (recommended)
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
pytest
```

#### Option B: Poetry
```bash
poetry install
poetry run pytest
```

#### Option C: pip
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
pytest
```

## What You Get

Your generated project includes:

```
fast-math-library/
├── src/
│   └── fast_math_library.zig    # Your Zig code (example included)
├── fast_math_library/
│   ├── __init__.py
│   └── _lib.pyi                 # Type stubs for IDE
├── test/
│   └── test_fast_math_library.py # Tests
├── .github/workflows/           # CI/CD ready
├── pyproject.toml               # Project config
└── README.md                    # Documentation
```

## Next Steps

### 1. Verify it works

The template includes a working Fibonacci example. Test it:

**With uv/pip (in venv):**
```bash
pytest -v
```

**With Poetry:**
```bash
poetry run pytest -v
```

### 2. Replace the example code

Edit `src/fast_math_library.zig`:

```zig
const std = @import("std");
const py = @import("pyz3");

// Your new function
pub fn add(args: struct { a: i64, b: i64 }) i64 {
    return args.a + args.b;
}

comptime {
    py.rootmodule(@This());
}
```

Update `fast_math_library/_lib.pyi`:

```python
def add(a: int, b: int) -> int: ...
```

Update `test/test_fast_math_library.py`:

```python
from fast_math_library import _lib

def test_add():
    assert _lib.add(2, 3) == 5
```

### 3. Rebuild and test

**With uv/pip:**
```bash
pip install -e .  # Rebuild after Zig changes
pytest
```

**With Poetry:**
```bash
poetry install    # Rebuild
poetry run pytest
```

### 4. Use your extension

```python
from fast_math_library import _lib

result = _lib.add(10, 20)
print(f"Result: {result}")  # Output: Result: 30
```

## Development Workflow

### Daily development

**With uv/pip (in activated venv):**
```bash
# Edit Zig code in src/
# Rebuild when Zig changes
pip install -e .

# Run tests
pytest

# Check style
ruff check .
ruff format .
```

**With Poetry:**
```bash
# Edit Zig code in src/
# Rebuild when Zig changes
poetry install

# Run tests
poetry run pytest

# Check style
poetry run ruff check .
poetry run ruff format .
```

### VSCode debugging

1. Open a `.zig` file
2. Press F5 to start debugging
3. Set breakpoints and step through

## Publishing

When ready to publish:

1. Update version in `pyproject.toml`
2. Create and push a git tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. GitHub Actions automatically publishes to PyPI

## Common Issues

### "Module not found" error

Rebuild the extension:
```bash
pip install -e .  # or: poetry install
```

### Zig build errors

Clean and rebuild:
```bash
rm -rf zig-out zig-cache .venv
# Then reinstall dependencies
```

### Type stubs not working

Regenerate stubs:
```bash
python -m ziglang build generate-stubs
```

## Resources

- [pyZ3 Documentation](https://github.com/amiyamandal-dev/pyz3)
- [Zig Language](https://ziglang.org/documentation/master/)
- [Example Zig file]({{cookiecutter.project_slug}}/src/{{cookiecutter.zig_file_name}}.zig)
- [Full USAGE guide](USAGE.md)

## Getting Help

- Template issues: Open an issue in the template repo
- pyZ3 questions: [pyZ3 GitHub](https://github.com/amiyamandal-dev/pyz3)
- Zig questions: [Zig Forums](https://github.com/ziglang/zig/discussions)

Happy coding!
