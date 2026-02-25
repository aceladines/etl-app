# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate venv (required first)
source .venv/bin/activate

# Install project (editable + dev deps)
pip install -e ".[dev]"

# Start dev server (auto-reload)
./scripts/run_dev.sh
# or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
pytest test/unit/ -v

# Run a single test file
pytest test/unit/api/test_health.py -v

# Run a specific test
pytest test/unit/workflows/test_workflow_run.py::test_workflow_run_success -v
```

## Architecture

**Oracle → MSSQL ETL pipeline** built on FastAPI. Sync DB drivers (`oracledb`, `pyodbc`) run in the thread pool via `asyncio.to_thread()`.

### Data flow

```
POST /api/v1/workflows/trigger
  → executor.execute_workflow_async()    # returns run_id, launches background task
    → asyncio.to_thread(workflow.run())  # sync ETL in thread pool
      → extract_batches()               # generator yielding list[dict] batches
        → transform_batch()             # per-batch transformation
          → load_batch()                # executemany insert into MSSQL
      → WorkflowResult                  # tracked in-memory by run_id
```

Memory is `O(batch_size)` — batches stream one at a time, never buffered.

### Layer responsibilities

- **`app/infrastructure/db/`** — `BaseConnector` ABC handles `extract_batches()` (stream_results + partitions) and `load_batch()` (executemany). `OracleConnector` and `SqlServerConnector` only override `_create_engine()`. `OracleLdapConnector` resolves Oracle addresses via LDAP using SQLAlchemy's `creator` hook — use `db_type="oracle_ldap"` with the factory. New DB types: subclass `BaseConnector`, add to `connector_factory._CONNECTOR_MAP`.
- **`app/steps/`** — Modular ETL operations. Each step has `execute(context: dict)`. Transform steps subclass `BaseTransformStep` and implement `transform_batch()`.
- **`app/workflows/`** — `BaseWorkflow` defines `get_extract_step()`, `get_transform_step()`, `get_load_step()` and the `run()` loop. Workflows register via `@register_workflow` decorator and must be explicitly imported in `app/main.py`.
- **`app/api/v1/`** — Routes aggregated in `router.py` under `/api/v1`. Workflow endpoints: trigger (POST), status (GET by run_id), list.

### Adding a new workflow

1. Create `app/workflows/definitions/my_workflow.py`
2. Subclass `BaseWorkflow`, set `name`, implement the three `get_*_step()` methods
3. Decorate with `@register_workflow`
4. Add `import app.workflows.definitions.my_workflow` to `app/main.py`

See `app/workflows/definitions/example_reference.py` for a fully-commented template with a custom transform step and LDAP connector instructions.

### Key conventions

- No ORM models — ETL moves `list[dict]` row data; schema defined by SQL queries
- Config via env vars loaded through `pydantic-settings` (`app/core/config.py`)
- Logging via `loguru` with stdlib intercept (`app/core/logging_config.py`)
- API tests use `httpx.AsyncClient` with `ASGITransport` (fixture in `test/conftest.py`)
- Tests marked with `@pytest.mark.anyio` for async; `asyncio_mode = "auto"` in pyproject.toml
