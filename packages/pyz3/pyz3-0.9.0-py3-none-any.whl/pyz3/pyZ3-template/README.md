# pyZ3 Cookiecutter Template

A [Cookiecutter](https://github.com/cookiecutter/cookiecutter) template for creating Python extension modules in Zig using [pyZ3](https://github.com/amiyamandal-dev/pyz3).

## Features

This template generates a complete project structure including:

- **Python Poetry project** - Modern Python packaging and dependency management
- **Zig source files** - Example Fibonacci implementation showcasing pyZ3 features
- **Type stubs (.pyi)** - Full type hints for your Python IDE
- **Pytest setup** - Run both Python and Zig unit tests with a single command
- **GitHub Actions** - CI/CD workflows for testing and publishing to PyPI
- **VSCode configuration** - Recommended extensions and debugger setup
- **Git initialization** - Automatically creates initial git repository

## Requirements

- Python 3.11 or higher
- [Cookiecutter](https://github.com/cookiecutter/cookiecutter) (install with `pip install cookiecutter`)
- One of the following for dependency management:
  - [uv](https://github.com/astral-sh/uv) (recommended - `pip install uv`)
  - [Poetry](https://python-poetry.org/)
  - Standard pip with venv
- [Zig](https://ziglang.org/) (will be installed automatically by pyZ3)

## Quick Start

### 1. Install Cookiecutter

```bash
pip install cookiecutter
```

### 2. Generate Your Project

```bash
cookiecutter gh:yourusername/pyZ3-template
# Or if running locally:
# cookiecutter /path/to/pyZ3-template
```

You'll be prompted for:
- **project_name**: Human-readable project name (e.g., "My Zig Extension")
- **project_slug**: Package name for PyPI (auto-generated from project_name)
- **package_name**: Python import name (auto-generated)
- **zig_file_name**: Name of your main Zig source file (auto-generated)
- **module_name**: Name of the compiled module (default: "_lib")
- **description**: Short project description
- **author_name**: Your name
- **author_email**: Your email address
- **version**: Initial version (default: "0.1.0")
- **python_version**: Minimum Python version (default: "3.11")

### 3. Set Up Your Project

**Using uv (recommended - faster):**
```bash
cd your-project-slug
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
pytest
```

**Using Poetry:**
```bash
cd your-project-slug
poetry install
poetry run pytest
```

**Using pip:**
```bash
cd your-project-slug
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
pytest
```

### 4. Start Developing

Edit the generated Zig file in `src/` to implement your extension module. The template includes a complete Fibonacci example to get you started.

## Template Structure

After generation, your project will have this structure:

```
your-project-slug/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI workflow
│       └── publish.yml         # PyPI publishing workflow
├── .vscode/
│   ├── extensions.json         # Recommended extensions
│   └── launch.json             # Debug configuration
├── src/
│   └── your_module.zig         # Your Zig implementation
├── your_package/
│   ├── __init__.py
│   └── _lib.pyi                # Type stubs
├── test/
│   ├── __init__.py
│   └── test_your_module.py     # Python tests
├── .gitignore
├── build.py                    # Build script
├── LICENSE
├── pyproject.toml              # Poetry configuration
├── README.md                   # Project documentation
└── renovate.json               # Dependency updates
```

## Development Workflow

### Running Tests

**With uv:**
```bash
pytest                    # Run all tests (Python and Zig)
zig build test            # Run only Zig tests
```

**With Poetry:**
```bash
poetry run pytest         # Run all tests
poetry run zig build test # Run only Zig tests
```

### Building

**With Poetry:**
```bash
poetry build
```

**With pip/uv:**
```bash
python -m build
```

### Code Quality

**With uv:**
```bash
ruff check .              # Check code
ruff format .             # Format code
```

**With Poetry:**
```bash
poetry run ruff check .
poetry run ruff format .
```

### Generating Type Stubs

```bash
python -m ziglang build generate-stubs
```

## Publishing to PyPI

1. Tag your release:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. The GitHub Actions workflow will automatically build and publish to PyPI

## Customization

After generating your project, you can:

1. **Replace the example code**: Edit `src/your_module.zig` with your own implementation
2. **Update tests**: Modify `test/test_your_module.py` to test your code
3. **Adjust dependencies**: Edit `pyproject.toml` to add Python dependencies
4. **Configure CI/CD**: Modify `.github/workflows/` for your needs

## Learning Resources

- [pyZ3 Documentation](https://github.com/amiyamandal-dev/pyz3)
- [Zig Language Reference](https://ziglang.org/documentation/master/)
- [Poetry Documentation](https://python-poetry.org/docs/)

## Contributing

Found a bug or have a suggestion? Please open an issue or submit a pull request!

## License

This template is released under the Apache 2.0 License. Projects generated from this template can use any license you choose.
