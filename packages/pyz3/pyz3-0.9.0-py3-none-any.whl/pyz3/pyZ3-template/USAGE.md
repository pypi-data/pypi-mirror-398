# Using the pyZ3 Cookiecutter Template

This document explains how to use this cookiecutter template to create new Zig Python extension projects.

## Prerequisites

1. **Python 3.11+** - Required for running cookiecutter and the generated project
2. **Cookiecutter** - Template generation tool
   ```bash
   pip install cookiecutter
   ```
3. **Dependency Manager** - Choose one (for the generated project):
   - **uv** (recommended - fastest)
     ```bash
     pip install uv
     ```
   - **Poetry** (full-featured)
     ```bash
     curl -sSL https://install.python-poetry.org | python3 -
     ```
   - **pip** (built-in, no installation needed)

## Using the Template

### Method 1: From GitHub (Recommended for published templates)

```bash
cookiecutter gh:your-org/pyZ3-template
```

### Method 2: From Local Directory

```bash
cookiecutter /path/to/pyZ3-template
```

### Method 3: Non-interactive Mode

Create a config file `my-config.yaml`:

```yaml
default_context:
  project_name: "My Awesome Extension"
  description: "A fast Fibonacci calculator"
  author_name: "Jane Developer"
  author_email: "jane@example.com"
  python_version: "3.11"
```

Then run:

```bash
cookiecutter /path/to/pyZ3-template --no-input --config-file my-config.yaml
```

## Template Variables

When you run cookiecutter, you'll be prompted for these values:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `project_name` | Human-readable project name | "My Zig Python Extension" | "Fast Image Processor" |
| `project_slug` | PyPI package name (auto-generated) | Derived from project_name | "fast-image-processor" |
| `package_name` | Python import name (auto-generated) | Derived from project_name | "fast_image_processor" |
| `zig_file_name` | Main Zig source filename (auto-generated) | Same as package_name | "fast_image_processor" |
| `module_name` | Compiled module name | "_lib" | "_lib" or "_core" |
| `description` | Short project description | "A Python extension module..." | "Fast image processing using Zig" |
| `author_name` | Your name | "Your Name" | "Jane Developer" |
| `author_email` | Your email | "you@example.com" | "jane@example.com" |
| `version` | Initial version | "0.1.0" | "0.1.0" |
| `python_version` | Minimum Python version | "3.11" | "3.11" or "3.12" |

## After Generation

Once the project is generated, follow these steps:

1. **Navigate to the project**:
   ```bash
   cd your-project-slug
   ```

2. **Set up environment and install dependencies**:

   **Option A: Using uv (recommended - fastest)**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

   **Option B: Using Poetry**
   ```bash
   poetry install
   ```

   **Option C: Using standard pip**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

   This will:
   - Create a virtual environment
   - Install Python dependencies
   - Install pyZ3 and Zig compiler
   - Build your extension module

3. **Run tests**:

   **With uv or pip:**
   ```bash
   pytest
   ```

   **With Poetry:**
   ```bash
   poetry run pytest
   ```

4. **Start developing**:
   - Edit `src/<your_module>.zig` to implement your extension
   - Update `test/test_<your_module>.py` to add tests
   - Modify `<your_package>/<module_name>.pyi` for type hints

## Project Structure

The generated project includes:

```
your-project-slug/
├── .github/workflows/     # CI/CD pipelines
│   ├── ci.yml            # Run tests on every push
│   └── publish.yml       # Publish to PyPI on tag
├── .vscode/              # VSCode configuration
│   ├── extensions.json   # Recommended extensions
│   └── launch.json       # Debugger setup
├── src/                  # Zig source code
│   └── <module>.zig     # Your Zig implementation
├── <package>/           # Python package
│   ├── __init__.py
│   └── <module>.pyi     # Type stubs
├── test/                # Tests
│   ├── __init__.py
│   └── test_<module>.py
├── build.py             # Build script (don't modify)
├── pyproject.toml       # Poetry configuration
└── README.md            # Project documentation
```

## Development Commands

### With uv (in activated venv)

```bash
# Run all tests (Python + Zig)
pytest

# Run only Zig tests
zig build test

# Build the package
python -m build

# Check code style
ruff check .

# Format code
ruff format .

# Generate type stubs
python -m ziglang build generate-stubs

# Sync dependencies
uv pip sync requirements.txt
```

### With Poetry

```bash
# Install dependencies
poetry install

# Run all tests (Python + Zig)
poetry run pytest

# Run only Zig tests
poetry run zig build test

# Build the package
poetry build

# Check code style
poetry run ruff check .

# Format code
poetry run ruff format .

# Generate type stubs
poetry run python -m ziglang build generate-stubs
```

### Debug in VSCode

Open a .zig file and press F5 (works with both uv and Poetry)

## Publishing Your Package

1. **Prepare for release**:
   - Update version in `pyproject.toml`
   - Update `README.md` with usage instructions
   - Ensure tests pass

2. **Create a git tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. **GitHub Actions automatically**:
   - Builds the package
   - Publishes to PyPI (requires PyPI token in GitHub secrets)

## Customization Tips

### Changing the Example Code

The template includes a Fibonacci example. To replace it:

1. Edit `src/<your_module>.zig` with your implementation
2. Update `<package>/<module>.pyi` with your function signatures
3. Modify `test/test_<module>.py` with your tests

### Adding Python Dependencies

Edit `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.11"
numpy = "^1.24.0"  # Add your dependencies here
```

Then run:
```bash
poetry lock
poetry install
```

### Configuring GitHub Actions

Edit `.github/workflows/ci.yml` and `.github/workflows/publish.yml` to customize:
- Python versions to test
- Operating systems
- Build matrix
- Deployment settings

## Troubleshooting

### Build Errors

If you encounter build errors:

```bash
# Clean and rebuild
rm -rf zig-out/ zig-cache/ .venv/
poetry install
```

### Zig Not Found

pyZ3 automatically installs Zig. If you see "zig not found":

```bash
poetry run python -m ziglang version
```

### Import Errors

Make sure you've built the module:

```bash
poetry install  # This runs the build
```

## Learning Resources

- [pyZ3 Documentation](https://github.com/amiyamandal-dev/pyz3/)
- [Zig Learn](https://ziglearn.org/)
- [Python C API](https://docs.python.org/3/c-api/)
- [Poetry Docs](https://python-poetry.org/docs/)

## Support

For issues with:
- **This template**: Open an issue in the template repository
- **pyZ3 framework**: Visit [pyZ3 GitHub](https://github.com/amiyamandal-dev/pyz3)
- **Zig language**: Check [Zig forums](https://github.com/ziglang/zig)
