# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project summary
`mcp-database-manager` is an MCP server that exposes database introspection + SQL execution over stdio, using SQLAlchemy under the hood. Connections are configured via a local YAML config file.

## Common commands

### Run the MCP server (local source checkout)
From the repo root:

- Run with all optional DB drivers enabled:
  - `uv run --extra all mcp-database-manager`
- Run with only the base dependencies:
  - `uv run mcp-database-manager`

The executable name (`mcp-database-manager`) is defined as a project script in `pyproject.toml`.

### Run the MCP server (published PyPI package)
- `uvx --from "mcp-database-manager[all]" mcp-database-manager`

### Configuration
- Default config path (all platforms): `~/.mcp-database-manager/config.yaml`
- Example config: `config.yaml.example`

### Linting / formatting
No linter/formatter is configured in this repo (no `ruff`, `black`, `flake8`, etc. settings found in `pyproject.toml`).

### Tests / verification
There is no `pytest`/`unittest` harness configured. The repo includes a manual verification script:

- Run verification:
  - `uv run python tests/verify.py`

Notes:
- `tests/verify.py` creates a local `test_env/` directory and, when run as a script, writes logs to `verify_output.txt`.

## High-level architecture

### Entry point + MCP wiring
- `mcp_database_manager/server.py`
  - Defines `main()` (the CLI entrypoint).
  - Creates an `mcp.server.Server` named `mcp-database-manager` and serves it over stdio via `mcp.server.stdio.stdio_server()`.
  - Registers 4 MCP tools:
    - `list_connections`
    - `get_schema`
    - `read_sql`
    - `write_sql`
  - On Windows, sets `asyncio.WindowsSelectorEventLoopPolicy()` before running.

### Config layer
- `mcp_database_manager/config.py`
  - `ConfigManager` is responsible for:
    - ensuring the config file exists (creates a commented template on first run)
    - loading YAML into a Pydantic `AppConfig` model (`connections: List[ConnectionConfig]`)
  - `ConnectionConfig` fields:
    - `name`: logical connection name used by MCP tool calls
    - `url`: SQLAlchemy engine URL
    - `readonly`: defaults to `true`

### Database layer
- `mcp_database_manager/db_manager.py`
  - `DatabaseManager` is the primary “service” used by the MCP tool handlers.
  - Lazily creates + caches a SQLAlchemy `Engine` per `connection_name`.
  - Introspection:
    - `get_schema(connection_name, table_names=None)` uses SQLAlchemy’s inspector.
    - When `table_names` is omitted, returns a markdown summary of all tables.
    - When `table_names` is provided, returns per-table column detail in markdown.
  - Query execution:
    - `execute_read()` rejects obvious write operations by checking the query prefix (basic keyword guard).
    - `execute_write()` enforces `readonly: false` for the target connection and executes inside a transaction (`engine.begin()`).

### Data/formatting boundary
- The MCP server layer (`server.py`) is responsible for:
  - parsing tool arguments
  - calling `ConfigManager`/`DatabaseManager`
  - serializing results back to MCP clients as `TextContent` (JSON for query results; markdown for schema output)

## Repo-specific agent rules
This repo includes always-on agent rules in `.agent/rules/common-rules.md`:
- If the user doesn’t request otherwise, respond in Chinese.
