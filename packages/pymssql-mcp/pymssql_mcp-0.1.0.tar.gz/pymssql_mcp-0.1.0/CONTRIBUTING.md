# Contributing to mssql-mcp

Thank you for your interest in contributing to mssql-mcp! This document provides guidelines and information for contributors.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (Python version, OS, SQL Server version)
- Any relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- A clear description of the proposed feature
- The motivation and use case
- Any implementation ideas you might have

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Make your changes** following our coding standards
4. **Add tests** for any new functionality
5. **Run the test suite** to ensure nothing is broken:
   ```bash
   pytest
   ```
6. **Run linting and type checks**:
   ```bash
   ruff check .
   ruff format --check .
   mypy src/
   ```
7. **Update documentation** if needed
8. **Submit your pull request**

## Development Setup

### Prerequisites

- Python 3.10+
- A Microsoft SQL Server instance for integration testing (optional)

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mssql-mcp.git
cd mssql-mcp

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mssql_mcp --cov-report=html

# Run specific test file
pytest tests/test_connection.py

# Run integration tests (requires database connection)
pytest tests/integration/ --run-integration
```

## Coding Standards

### Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Maximum line length: 100 characters
- Use type hints for all function signatures

### Code Quality

- Write docstrings for public modules, classes, and functions (Google style)
- Keep functions focused and single-purpose
- Prefer explicit over implicit
- Handle errors gracefully with meaningful messages

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Reference related issues when applicable

Example:
```
Add connection pooling support

- Implement ConnectionPool class with configurable size
- Add pool_size configuration option
- Update documentation with pooling examples

Fixes #42
```

## Project Structure

```
mssql-mcp/
├── src/mssql_mcp/        # Main package source
│   ├── __init__.py       # Package init with version
│   ├── app.py            # FastMCP instance
│   ├── server.py         # MCP server entry point
│   ├── connection.py     # Database connection manager
│   ├── config.py         # Pydantic settings configuration
│   ├── tools/            # MCP tool implementations
│   │   ├── query.py      # Query execution tools
│   │   ├── tables.py     # Schema discovery tools
│   │   ├── crud.py       # CRUD operations
│   │   ├── databases.py  # Database management
│   │   ├── stored_procs.py # Stored procedure tools
│   │   └── export.py     # Data export tools
│   ├── resources/        # MCP resources
│   │   └── syntax_help.py # T-SQL syntax reference
│   └── utils/            # Utility functions
│       ├── safety.py     # SQL validation
│       └── audit.py      # Audit logging
├── tests/                # Test suite
│   ├── conftest.py       # Pytest fixtures
│   └── test_*.py         # Unit tests
└── pyproject.toml        # Project configuration
```

## Adding New Tools

MCP tools are defined using the `@mcp.tool()` decorator. To add a new tool:

1. **Choose the appropriate module** in `src/mssql_mcp/tools/`
2. **Define the tool function** with the decorator:

```python
from ..app import mcp
from ..server import get_connection_manager

@mcp.tool()
def my_new_tool(param1: str, param2: int = 10) -> dict[str, Any]:
    """Short description of what the tool does.

    Longer description with more details about the tool's behavior.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: 10)

    Returns:
        Dictionary containing the result fields.
    """
    manager = get_connection_manager()

    try:
        # Tool implementation
        result = ...
        return {"status": "success", "data": result}
    except Exception as e:
        return {"error": str(e)}
```

3. **Follow these conventions:**
   - Return dictionaries (JSON-serializable)
   - Include `status` or `error` in responses
   - Use type hints for all parameters
   - Write comprehensive docstrings (shown to AI assistants)
   - Handle errors gracefully

4. **Add tests** in `tests/test_tools/`

5. **Update documentation** if needed

## Testing Guidelines

- Write unit tests for all new functionality
- Use pytest fixtures for common setup
- Mock external dependencies (database connections)
- Aim for meaningful test coverage, not just high percentages

### Test Naming Convention

```python
def test_connect_with_valid_credentials_succeeds():
    """Test that connection succeeds with valid credentials."""
    ...

def test_connect_with_invalid_host_raises_connection_error():
    """Test that connection fails gracefully with invalid host."""
    ...
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings following Google style
- Include code examples where helpful

## Questions?

Feel free to open an issue for any questions about contributing. We're happy to help!

## License

By contributing to mssql-mcp, you agree that your contributions will be licensed under the Apache License 2.0.
