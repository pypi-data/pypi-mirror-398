# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

This project uses [pyZ3](https://github.com/amiyamandal-dev/pyz3) to create a Python extension module written in Zig.

## Installation

### Using uv (recommended)

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Using Poetry

```bash
poetry install
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Development

### Running Tests

**With uv/pip (in activated venv):**
```bash
pytest
```

**With Poetry:**
```bash
poetry run pytest
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

**With uv/pip (in activated venv):**
```bash
ruff check .
ruff format .
```

**With Poetry:**
```bash
poetry run ruff check .
poetry run ruff format .
```

## Usage

```python
from {{ cookiecutter.package_name }} import {{ cookiecutter.module_name }}

# Example: Using the Fibonacci functions
result = {{ cookiecutter.module_name }}.nth_fibonacci_iterative(10)
print(f"10th Fibonacci number: {result}")

# Using the iterator
fib_sequence = {{ cookiecutter.module_name }}.Fibonacci(10)
for num in fib_sequence:
    print(num)
```

## About

This project was generated from the [pyZ3 Template](https://github.com/amiyamandal-dev/pyz3-template).

For more information, visit the [pyZ3 documentation](https://github.com/amiyamandal-dev/pyz3).
