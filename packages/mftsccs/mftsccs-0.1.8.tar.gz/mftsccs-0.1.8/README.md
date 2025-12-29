# CCS

A Python library for CCS functionality.

## Installation

### From source (development mode)

```bash
# Clone the repository
git clone https://github.com/yourusername/ccs.git
cd ccs

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### From PyPI (once published)

```bash
pip install ccs
```

## Usage

```python
# Import the main functions and classes
from ccs import example_function, ExampleClass, helper_function

# Use example_function
result = example_function("hello")
print(result)  # Output: Processed: hello

# Use ExampleClass
obj = ExampleClass("my_instance")
obj.process("some data")
print(obj)  # Output: ExampleClass(name='my_instance', data=some data)

# Use helper_function
first_item = helper_function([1, 2, 3])
print(first_item)  # Output: 1
```

### Import specific modules

```python
from ccs.core import ExampleClass
from ccs.utils import flatten_list, validate_input

# Flatten nested lists
flat = flatten_list([[1, 2], [3, 4]])
print(flat)  # Output: [1, 2, 3, 4]

# Validate input types
is_valid = validate_input("hello", str)
print(is_valid)  # Output: True
```

## Project Structure

```
CCS-Python/
├── pyproject.toml          # Package configuration
├── README.md               # This file
├── src/
│   └── ccs/                # Main package
│       ├── __init__.py     # Package initialization & exports
│       ├── core.py         # Core functionality
│       └── utils.py        # Utility functions
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_core.py
│   └── test_utils.py
└── docs/                   # Documentation (optional)
```

## Development

### Running tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=ccs
```

### Code formatting

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/
```

### Type checking

```bash
mypy src/
```

## Building & Publishing

### Build the package

```bash
pip install build
python -m build
```

This creates distribution files in the `dist/` directory:
- `ccs-0.1.0.tar.gz` (source distribution)
- `ccs-0.1.0-py3-none-any.whl` (wheel distribution)

### Publish to PyPI

```bash
pip install twine

# Upload to TestPyPI first (recommended)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## License

MIT License - see LICENSE file for details.
