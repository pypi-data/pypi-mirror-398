# Contributing to hola-graph

Thank you for your interest in contributing to hola-graph! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.7+
- C++14 compatible compiler
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/shakfu/hola-graph.git
   cd hola-graph
   ```

2. Build and install in development mode:

   ```bash
   make build
   ```

   This will automatically download and build the adaptagrams dependency.

3. Run tests:

   ```bash
   make test
   ```

## Development Workflow

### Building

```bash
make build     # Build/reinstall the package
make rebuild   # Clean and rebuild from scratch
make cmake     # Build using CMake (alternative)
```

### Testing

```bash
make test                                    # Run all tests
uv run pytest -v                             # Verbose output
uv run pytest tests/test_hola_graph.py::TestGraph  # Run specific test class
uv run pytest -k "test_node"                 # Run tests matching pattern
```

### Code Quality

```bash
make lint      # Run ruff linter
make format    # Format code with ruff
```

## Project Structure

```
hola-graph/
├── src/
│   ├── hola_graph.cpp       # C++ pybind11 bindings
│   ├── hola_graph.pyi       # Type stubs
│   └── hola_graph_utils.py  # Python utilities
├── tests/
│   └── test_hola_graph.py   # Test suite
├── scripts/
│   ├── setup.sh         # Dependency setup
│   └── gen.py           # Code generation (litgen)
├── setup.py             # Build configuration
└── pyproject.toml       # Project metadata
```

## Making Changes

### C++ Bindings (`src/hola_graph.cpp`)

When modifying C++ bindings:

1. Follow existing naming conventions (snake_case for Python methods)
2. Add docstrings to all new methods
3. Update type stubs in `src/hola_graph.pyi`
4. Add tests for new functionality

Example:

```cpp
.def("my_method", &Graph::myMethod,
     "Description of what the method does.",
     py::arg("param1"), py::arg("param2"))
```

### Python Utilities (`src/hola_graph_utils.py`)

When adding Python utilities:

1. Add type hints to all functions
2. Include docstrings with Args, Returns, and Example sections
3. Add corresponding tests

### Tests

- Use pytest-style tests
- Group related tests in classes (e.g., `TestGraph`, `TestNode`)
- Include both positive and negative test cases
- Test edge cases

## Pull Request Process

1. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure:
   - All tests pass (`make test`)
   - Code is formatted (`make format`)
   - No linting errors (`make lint`)

3. Commit with a descriptive message:

   ```bash
   git commit -m "Add feature: description of changes"
   ```

4. Push and create a pull request:

   ```bash
   git push origin feature/your-feature-name
   ```

5. In the PR description:
   - Describe what the change does
   - Reference any related issues
   - Include test plan if applicable

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (ruff default)

### C++

- Use C++14 features
- Follow existing code style in `hola_graph.cpp`
- Use `py::arg()` for all function parameters

## Reporting Issues

When reporting issues, please include:

1. Python version (`python --version`)
2. Operating system and version
3. Steps to reproduce
4. Expected vs actual behavior
5. Error messages or stack traces

## Questions?

Feel free to open an issue for questions or discussions about the project.
