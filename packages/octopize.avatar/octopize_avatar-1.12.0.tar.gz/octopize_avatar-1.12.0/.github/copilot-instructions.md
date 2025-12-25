# Avatar Python Client - AI Coding Agent Instructions

> **📦 Part of Avatar Monorepo** - [Back to root instructions](../../../.github/copilot-instructions.md)

## Project Overview

This is a Python SDK for Octopize's Avatar API, a data avatarization service that creates synthetic datasets. The client is auto-generated from OpenAPI specs and provides three main abstractions:

- **`ApiClient`** - Low-level HTTP client with authentication (auto-generated from `../../services/api/schema.json`)
- **`Manager`** - High-level facade for authentication and creating runners
- **`Runner`** - Stateful workflow orchestrator for avatarization jobs (add tables → configure → run → retrieve results)

## Critical Architecture Decisions

### Auto-Generated Code Pattern

**NEVER manually edit** files with `# This file has been generated - DO NOT MODIFY`:

- `src/avatars/api.py` - API method wrappers
- `src/avatars/client.py` - ApiClient with auth handling
- `src/avatars/models.py` - Pydantic models

To regenerate: `just generate-python` (runs `make -C ../../client generate-python`, which executes `client/generator-config/python/generate.py` against the API schema).

### Runner State Machine

The `Runner` class maintains complex internal state across a multi-step workflow:

1. **Configuration Phase**: `add_table()` → `set_parameters()` → `get_yaml()` builds an `avatar_yaml.Config` object
2. **Execution Phase**: `run(jobs_to_run=[JobKind.standard, JobKind.privacy_metrics, ...])` submits jobs with dependency chains
3. **Retrieval Phase**: Results lazy-loaded via `ResultsOrganizer` on first access (e.g., `shuffled()`, `privacy_metrics()`)

**Key insight**: The `set_name` (UUID) is only assigned server-side after first `put_resources()` call. Until then, config is local-only.

### Job Dependency Order

Jobs must run in specific order (see `constants.py::JOB_EXECUTION_ORDER`):

```python
[JobKind.standard, JobKind.privacy_metrics, JobKind.signal_metrics, JobKind.report]
```

Privacy/signal metrics depend on `standard` (avatarization) completing first. Report depends on both metrics.

## Development Workflows

### Testing

```bash
just test              # Unit tests with pytest
just test-tutorials    # Integration tests (runs notebooks as tests)
just lci               # "Local CI" - format, lint, typecheck, test, test-integration
```

**Tutorial notebooks as tests**: `tests/integration/test_tutorials.py` executes notebooks using `nbconvert`. Changes to notebooks require `just generate-py` to sync `.py` versions.

### Documentation

```bash
just doc-build  # Sphinx multiversion build (REQUIRES committed changes!)
just doc-fast   # Single-version build for current branch
```

**Critical gotcha**: `sphinx-multiversion` only builds committed changes due to git checkout mechanism. Uncommitted edits won't appear.

### Notebook Development

```bash
just notebook  # Sets up venv, installs deps, launches Jupyter
```

Notebooks are the primary user-facing artifacts. After editing:

1. `just format-notebooks` - Clears output, strips metadata, runs ruff
2. `just generate-py` - Syncs to `.py` format via jupytext

## Project-Specific Conventions

### Environment Variables

```bash
AVATAR_BASE_API_URL=http://localhost:8080/api  # API endpoint
AVATAR_USERNAME=user_integration               # Test credentials
AVATAR_PASSWORD=password_integration
```

Set in `justfile` with `env_var_or_default()`. Required for integration tests.

### Dual Parameter Systems

The `Runner.set_parameters()` method handles two mutually exclusive modes:

- **Standard avatarization**: `k=N` (number of neighbors)
- **Differential privacy**: `dp_epsilon=E` (privacy budget)

**Never set both** - raises ValueError. This creates separate config sections (`config.avatarization` vs `config.avatarization_dp`).

### Processor Pattern

`src/avatars/processors/` contains client-side data transformations (e.g., `GeolocationNormalizationProcessor`, `PerturbationProcessor`). These run BEFORE uploading to server. See Tutorial 5 for usage patterns.

### Test Fixtures

`tests/unit/conftest.py` provides `FakeApiClient` that mocks S3 downloads with in-memory data. When adding endpoints, update `FakeResults.get_results()` to return expected URLs for new result types.

## Package Management

Uses `uv` (not pip/poetry directly). Dependencies in `pyproject.toml`:

- Main: `httpx`, `pydantic`, `pandas`, `avatar-yaml` (separate parsing library)
- Dev: `ruff`, `mypy`, `pytest`
- Notebook: `jupyter`, `matplotlib`, `seaborn`

**Pinned versions**: `aiobotocore <=2.22.0` and `botocore <=1.40.17` due to [compatibility issue](https://github.com/aio-libs/aiobotocore/issues/1414).

## Common Patterns

### Creating an Avatarization

```python
from avatars import Manager

manager = Manager(base_url="https://api.octopize.io")
manager.authenticate("user", "password")

runner = manager.create_runner(set_name="my_project")
runner.add_table("patients", data="patients.csv", primary_key="patient_id")
runner.set_parameters("patients", k=20, ncp=30)
runner.run()
results_df = runner.shuffled("patients")
```

### Handling Results

Results are cached in `ResultsOrganizer` after first download. Access patterns:

- `runner.shuffled(table_name)` → pandas DataFrame
- `runner.privacy_metrics(table_name)` → list[dict]
- `runner.render_plot(table_name, PlotKind.PROJECTION_2D)` → HTML visualization

### Multi-Table Workflows

Link tables via foreign keys:

```python
runner.add_table("visits", "visits.csv", foreign_keys=["patient_id"])
runner.add_link(
    parent_table_name="patients", parent_field="patient_id",
    child_table_name="visits", child_field="patient_id"
)
```

## Things AI Should Know

1. **Don't add/remove methods to ApiClient/api.py** - These are code-generated. Change the OpenAPI schema instead.
2. **Job status polling** - `Runner._retrieve_job_result_urls()` polls with `DEFAULT_RETRY_INTERVAL` (5s). Jobs are async on server.
3. **YAML config format** - Uses `avatar-yaml` library (external dep). Runner builds config, server interprets it.
4. **SSL verification** - Can disable with `ApiClient(base_url=url, should_verify_ssl=False)` for on-premise deployments.
5. **File uploads** - Handled via pre-signed S3 URLs from `/results/upload-url` endpoint. `DataUploader` manages this.

## When Modifying Code

- **Adding API endpoints**: Regenerate from schema, don't hand-write
- **Adding result types**: Update `constants.py::Results` enum and `RESULTS_TO_STORE`
- **Adding job types**: Add to `models.py::JobKind` and `constants.py::JOB_EXECUTION_ORDER`
- **Changing Runner state**: Ensure `_extract_current_parameters()` and `update_parameters()` stay in sync
- **New processors**: Follow naming `*Processor` and add to `processors/__init__.py`

## Integration Points

- **Server API**: FastAPI backend at `../../services/api/` (OpenAPI source of truth)
- **Client generator**: `../../client/generator-config/python/generate.py` (Jinja2 templates + datamodel-codegen)
- **Shared justfiles**: `../../justfiles/python.just` (imports common Python tasks like `lint`, `test`)
- **S3 storage**: Results stored in object storage, accessed via pre-signed URLs
