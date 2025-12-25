# Cookiecutter Template Structure

This document describes the structure of the pyZ3-template cookiecutter template after cleanup.

## Repository Root Files

```
pyZ3-template/
├── .cookiecutterrc              # Example cookiecutter configuration
├── .gitignore                   # Git ignore patterns
├── .github/                     # GitHub Actions for template repo
├── .vscode/                     # VSCode settings for template development
├── cookiecutter.json            # Template variables and defaults
├── hooks/                       # Post-generation hooks
│   └── post_gen_project.py     # Initializes git, detects tools
├── {{cookiecutter.project_slug}}/  # The actual template directory
│   ├── .github/
│   ├── .vscode/
│   ├── src/
│   ├── {{cookiecutter.package_name}}/
│   ├── test/
│   └── ... (all project files)
├── CONVERSION_SUMMARY.md        # Details of the conversion process
├── LICENSE                      # Apache 2.0 License
├── QUICKSTART.md               # 5-minute quick start guide
├── README.md                   # Template overview and usage
├── USAGE.md                    # Detailed usage instructions
└── validate_template.py        # Template validation script
```

## Template Directory Contents

The `{{cookiecutter.project_slug}}/` directory contains all files that will be generated:

```
{{cookiecutter.project_slug}}/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Continuous integration
│       └── publish.yml         # PyPI publishing
├── .vscode/
│   ├── extensions.json         # Recommended VS Code extensions
│   └── launch.json             # Debug configuration
├── src/
│   └── {{cookiecutter.zig_file_name}}.zig  # Zig source code
├── {{cookiecutter.package_name}}/
│   ├── __init__.py            # Python package init
│   └── {{cookiecutter.module_name}}.pyi   # Type stubs
├── test/
│   ├── __init__.py
│   └── test_{{cookiecutter.zig_file_name}}.py  # Tests
├── .gitignore                  # Standard Python/Zig gitignore
├── build.py                    # pyZ3 build script
├── LICENSE                     # Apache 2.0 License
├── pyproject.toml             # Project configuration
├── README.md                  # Project documentation
└── renovate.json              # Dependency updates config
```

## Cookiecutter Variables

Defined in `cookiecutter.json`:

| Variable | Usage | Default |
|----------|-------|---------|
| `project_name` | Human-readable name | "My Zig Python Extension" |
| `project_slug` | Directory name, PyPI package | Auto-generated |
| `package_name` | Python import name | Auto-generated |
| `zig_file_name` | Zig source filename | Auto-generated |
| `module_name` | Compiled module name | "_lib" |
| `description` | Project description | Default text |
| `author_name` | Author name | "Your Name" |
| `author_email` | Author email | "you@example.com" |
| `version` | Initial version | "0.1.0" |
| `python_version` | Min Python version | "3.11" |

## Usage Flow

1. **User runs**: `cookiecutter /path/to/pyZ3-template`
2. **Cookiecutter prompts** for variable values
3. **Cookiecutter generates** project from template directory
4. **Post-gen hook runs**: 
   - Initializes git repository
   - Creates initial commit
   - Detects available tools (uv/Poetry/pip)
   - Shows next steps
5. **User sets up** environment with their preferred tool

## Template Features

### Multi-Tool Support

The template supports three installation methods:

- **uv**: Fast, modern package manager
- **Poetry**: Full-featured dependency management  
- **pip**: Standard Python tooling

All documentation includes instructions for each method.

### Complete Example

Includes a working Fibonacci implementation in Zig showing:
- Function exports
- Python class wrapping
- Iterator protocol
- Type stubs
- Unit tests (both Python and Zig)

### CI/CD Ready

GitHub Actions workflows for:
- Running tests on every push
- Publishing to PyPI on tag creation
- Code quality checks (Ruff)
- Stub validation

### Developer Experience

- Type stubs for IDE autocomplete
- VSCode debugger configuration
- Recommended extensions
- Pre-configured linters/formatters

## Files Removed from Original

The following files from the original template were removed as they're not needed for cookiecutter:

- `fibonacci/` - Original example package
- `src/` - Original Zig source
- `test/` - Original tests
- `build.py` - Original build script (now in template dir)
- `poetry.lock` - Lock file
- `pyproject.toml` - Original config (now in template dir)
- `renovate.json` - Original config (now in template dir)

These files are now only in the `{{cookiecutter.project_slug}}/` directory with template variables.

## Validation

Run `python3 validate_template.py` to check:

- ✓ cookiecutter.json is valid JSON
- ✓ All required files exist
- ✓ Template variables are properly used
- ✓ Hooks are executable

## Generated Project Structure

When you run `cookiecutter .` with project name "My Project", it generates:

```
my-project/
├── .git/                      # Initialized by post-gen hook
├── .github/workflows/
├── .vscode/
├── src/
│   └── my_project.zig
├── my_project/
│   ├── __init__.py
│   └── _lib.pyi
├── test/
│   └── test_my_project.py
├── pyproject.toml            # Name: "my-project"
├── README.md                 # Title: "My Project"
└── ... (other files)
```

## Next Steps

1. **Test the template**: `cookiecutter . --no-input`
2. **Validate**: `python3 validate_template.py`
3. **Try generated project**: Follow README.md instructions
4. **Customize**: Edit `cookiecutter.json` for your defaults

---

This template is ready to use for creating new Zig Python extension projects with minimal setup!
