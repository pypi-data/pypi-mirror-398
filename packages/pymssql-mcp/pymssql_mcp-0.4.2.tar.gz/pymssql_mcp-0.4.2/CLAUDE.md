# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mssql-mcp is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with Microsoft SQL Server databases. It uses the `pymssql` library for database connectivity and provides tools for querying, CRUD operations, and stored procedure execution.

## Development Commands

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest                                      # All tests
pytest tests/test_connection.py             # Single file
pytest --cov=mssql_mcp --cov-report=html    # With coverage
pytest tests/integration/ --run-integration # Integration tests (requires DB)

# Linting and type checking
ruff check .
ruff format .
mypy src/
```

## Tech Stack

- **Language**: Python 3.10+
- **MCP Framework**: `mcp` (FastMCP)
- **Database Connectivity**: `pymssql` (pure Python SQL Server driver)
- **Build System**: hatchling with pyproject.toml
- **Testing**: pytest, pytest-cov, pytest-mock
- **Linting/Formatting**: ruff
- **Type Checking**: mypy
- **Settings**: pydantic-settings (environment variable binding)

## Architecture

```
src/mssql_mcp/
├── server.py           # FastMCP server entry point
├── connection.py       # Connection management
├── config.py           # Pydantic settings, environment config
├── tools/              # MCP tool implementations
│   ├── query.py        # execute_query, validate_query
│   ├── tables.py       # list_tables, describe_table
│   ├── crud.py         # read/insert/update/delete rows
│   ├── stored_procs.py # Stored procedure execution
│   └── export.py       # JSON/CSV export
├── utils/
│   ├── safety.py       # SQL validation, command blocklist
│   └── audit.py        # Audit logging
└── resources/
    └── syntax_help.py  # T-SQL syntax reference
```

## Environment Variables

Required: `MSSQL_HOST`, `MSSQL_USER`, `MSSQL_PASSWORD`, `MSSQL_DATABASE`
Optional: `MSSQL_PORT`, `MSSQL_TIMEOUT`, `MSSQL_READ_ONLY`, `MSSQL_MAX_ROWS`, `MSSQL_QUERY_TIMEOUT`, `MSSQL_BLOCKED_COMMANDS`

## Coding Standards

- Follow PEP 8; use ruff for linting/formatting
- Maximum line length: 100 characters
- Type hints required for all function signatures
- Google-style docstrings for public APIs

## Key Patterns

**Connection Pattern**: Use `pymssql.connect()` with `cursor(as_dict=True)` for dictionary-style row access.

**Safety Controls**: SQL validation via blocklist, parameterized queries for all user input, optional read-only mode.

**Schema Discovery**: Use `INFORMATION_SCHEMA.TABLES` and `INFORMATION_SCHEMA.COLUMNS` for metadata.
