# E2E Test Suites

This directory contains end-to-end test suites that are part of the UV workspace.

## Structure

```
e2e/
├── oxford-pets/          # Oxford Pets pipeline tests
├── openvid/              # OpenVid video pipeline tests
└── document_embedding/   # PDF document embedding tests
    ├── pyproject.toml    # Test driver dependencies
    ├── conftest.py       # Test fixtures
    ├── test_drivers/     # Test drivers (load pre-uploaded manifests)
    └── udfs/             # UDF packages (separate environments)
```

## Workspace Architecture

E2E suites are **workspace members** that share dependency resolution with the main Geneva package:
- Single `uv.lock` at workspace root ensures consistent versions
- Each suite specifies: `geneva = { workspace = true }` in `[tool.uv.sources]`
- Prevents version conflicts between main package and e2e tests
- All dependencies must be compatible across workspace members

### Key Version Constraints

The following constraints exist to maintain compatibility:

**attrs (`>=23,<25`)** (workspace-wide via `override-dependencies`):
- Ray 2.44+ containers bundle attrs 23.x but don't declare it as a pip dependency
- Different attrs versions use incompatible pickle formats causing deserialization failures
- Enforced workspace-wide via `[tool.uv] override-dependencies = ["attrs>=23,<25"]`
- Applies to all workspace members without explicit per-package declarations

**pyarrow (`>=16,<21`)** (e2e tests only):
- HuggingFace `datasets` library is incompatible with pyarrow 21.x
- pyarrow 21.0.0 removed `PyExtensionType` that datasets depends on
- Constraint prevents import errors in e2e tests that use datasets
- Main Geneva package has no upper bound on pyarrow

## Running Tests Locally

### From Workspace Root (Recommended)
```bash
# Install all workspace dependencies including e2e suites (pin to lockfile)
uv sync --all-groups --all-extras --locked

# Run Oxford Pets e2e tests
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest e2e/oxford-pets -v

# Run Document Embedding e2e tests
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest e2e/document_embedding -v

# Or via Makefile
make test-e2e-oxford-pets-gcp SLUG=12345 NUM_IMAGES=100 BATCH_SIZE=10
make test-e2e-document-embedding-gcp SLUG=12345 NUM_DOCS=20 BATCH_SIZE=4
```

### From E2E Suite Directory
```bash
cd e2e/oxford-pets
uv sync --locked
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest . -v
```

**Note**: `RAY_ENABLE_UV_RUN_RUNTIME_ENV=0` is required to prevent conflicts between uv's runtime environment management and Ray's dependency handling.

## Adding a New E2E Suite

1. Create directory: `e2e/new-suite/`
2. Copy `e2e/oxford-pets/pyproject.toml` as template
3. Update package name to `geneva-e2e-new-suite`
4. Customize dependencies (respecting version constraints above)
5. Add `[tool.uv.sources]` line: `geneva = { workspace = true }`
6. Append the new path under `[tool.uv.workspace].members` in the root `pyproject.toml`
7. Add `conftest.py` with fixtures
8. Add `test_*.py` files
9. Run `uv lock` from workspace root to update lock file
10. Add Makefile targets for the new suite
11. Optionally create a GitHub workflow

## CI/CD

- Oxford Pets: `.github/workflows/e2e.yml`

## Key Files

Each suite's `pyproject.toml` specifies:
- `name`: Unique package name (`geneva-e2e-{suite-name}`)
- `requires-python`: Python version range
- `dependencies`: All deps including ML libraries (must be compatible with main package constraints)
- `[tool.uv.sources]`: `geneva = { workspace = true }` to use workspace resolution

Root `pyproject.toml` workspace configuration:
- `[tool.uv.workspace]`: Lists all workspace members
- Single `uv.lock` at root ensures consistent dependency resolution

## Notes

- Single workspace lock file (`uv.lock`) at root ensures reproducible builds
- Installation takes ~10 minutes due to large ML libraries (PyTorch ~850MB)
- Shared virtual environment (`.venv/`) at workspace root
- Tests import `geneva` as if it were an external package
- All workspace members must have compatible dependency versions
