# Oxford Pets E2E Test Suite

End-to-end tests for Geneva using the Oxford-IIIT Pet Dataset (3680 images).

## Architecture

This test suite demonstrates the **separation of UDF environments from test drivers**:

- **Test Drivers** (`test_drivers/`) - Minimal dependencies, just run backfills
- **UDF Packages** (`udfs/`) - Isolated environments with ML dependencies

### Two-Stage Process

1. **Manifest Upload** (automatic via pytest fixture):
   - Runs `upload_manifest.py` in each UDF's environment via `uv run --directory`
   - Creates manifest from UDF's `pyproject.toml` dependencies
   - Uploads manifest to Geneva and adds columns to table
   - Uses `GENEVA_TABLE_NAME` environment variable

2. **Test Execution**:
   - Tests run with minimal dependencies (no torch, transformers, etc.)
   - Load pre-uploaded manifests by name
   - Ray workers execute UDFs in isolated environments defined by manifests

## Structure

```
oxford-pets/
├── pyproject.toml          # Test driver dependencies (minimal)
├── conftest.py             # Fixtures: table creation, manifest upload
├── test_drivers/           # Test drivers (no UDF imports)
│   ├── test_cpu_simple.py                      # file_size, dimensions
│   ├── test_embeddings_openclip.py             # OpenCLIP embeddings
│   ├── test_embeddings_sentence_transformers.py # Sentence transformers embeddings
│   ├── test_captions_blip.py                   # BLIP captions (GPU)
│   └── test_incremental.py                     # Incremental/async backfills
└── udfs/                   # UDF packages (separate environments)
    ├── simple/
    │   ├── pyproject.toml       # pillow
    │   ├── simple_udfs.py       # UDF implementations
    │   ├── manifest.py          # Manifest factory
    │   └── upload_manifest.py   # Upload + add columns
    ├── openclip/
    │   ├── pyproject.toml           # open-clip-torch, torch>=2.1
    │   ├── openclip_embedding_udf.py # UDF implementation
    │   ├── manifest.py              # Manifest factory
    │   └── upload_manifest.py       # Upload + add columns
    ├── sentence-transformers/
    │   ├── pyproject.toml       # sentence-transformers>=2.2.0, torch>=2.1
    │   ├── embedding_udf.py     # UDF implementation
    │   ├── manifest.py          # Manifest factory
    │   └── upload_manifest.py   # Upload + add columns
    └── blip/
    │   ├── pyproject.toml       # transformers, torch>=2.1
    │   ├── blip_caption_udf.py  # UDF implementation
    │   ├── manifest.py          # Manifest factory
    │   └── upload_manifest.py   # Upload + add columns
```

## Running Tests

### Prerequisites

Install test driver dependencies from workspace root:
```bash
uv sync --all-groups --all-extras --locked
```

### From Workspace Root (Recommended)

```bash
# Run all oxford-pets tests (manifest upload is automatic)
make test-e2e-oxford-pets-gcp SLUG=mytest NUM_IMAGES=100 BATCH_SIZE=10

# Or directly with pytest
cd e2e/oxford-pets
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest test_drivers --csp=gcp --test-slug=mytest --num-images=100 --batch-size=10 -v

# Run specific test
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest test_drivers/test_cpu_simple.py -v
```

### Manual Manifest Upload (Optional)

If you need to upload manifests manually (e.g., for debugging):

```bash
# Export table name
export GENEVA_TABLE_NAME=oxford_pets_shared_abc123

# Upload from each UDF directory
cd udfs/simple
uv run python upload_manifest.py --bucket gs://your-bucket/path

cd ../openclip
uv run python upload_manifest.py --bucket gs://your-bucket/path

cd ../sentence-transformers
uv run python upload_manifest.py --bucket gs://your-bucket/path

cd ../blip
uv run python upload_manifest.py --bucket gs://your-bucket/path
```

**Note**: Normally manifests are uploaded automatically by the `oxford_pets_table` pytest fixture.

## Key Concepts

### Environment Variables

- `GENEVA_TABLE_NAME`: Table name for column addition (set by pytest fixture)
- `FILE_SIZE_COL`, `DIMENSIONS_COL`, `EMBEDDING_COL`, `CAPTION_COL`: Custom column names (optional)
- `RAY_ENABLE_UV_RUN_RUNTIME_ENV=0`: Required to prevent conflicts between uv and Ray dependency management

### Manifest Upload Scripts

Each UDF package has an `upload_manifest.py` that:
1. Creates manifest from `pyproject.toml` dependencies using `manifest.py` factory
2. Packages all site-packages dependencies (via `skip_site_packages=False`)
3. Uploads manifest and zipped dependencies to GCS/S3 via `conn.define_manifest()`
4. Adds columns to table via `tbl.add_columns()`

**Important**: `skip_site_packages=False` ensures all transitive dependencies (including Geneva, lance, lancedb, more_itertools, attrs, etc.) are packaged and uploaded to Ray workers. This avoids "ModuleNotFoundError" for any dependencies not explicitly listed in the manifest's pip requirements.

#### Understanding How Dependencies Are Packaged

The manifest upload uses `uv run --directory <udf_dir> python upload_manifest.py`. Here's what happens:

**When `uv run` executes:**
1. Read the UDF's `pyproject.toml`
2. Create/sync `.venv` in the UDF directory
3. Install dependencies from `[project] dependencies = [...]` into `.venv/lib/python3.x/site-packages/`
4. Install the UDF package itself in editable mode
   - Triggers `[build-system]` backend (hatchling)
   - Requires `[tool.hatch.build.targets.wheel] packages = ["."]` configuration
   - Requires `[tool.hatch.metadata] allow-direct-references = true` for git dependencies
5. Run the upload script

**What gets packaged:**
- The `.venv/lib/python3.x/site-packages/` directory contains all resolved dependencies (torch, transformers, open-clip-torch, etc.)
- Geneva's `get_paths_to_package()` captures this via `site.getsitepackages()`
- Each UDF has its own isolated `.venv` with unique dependencies
- The UDF Python files (e.g., `blip_caption_udf.py`) are packaged separately via `py_modules=["."]`

**Result:** When manifests are uploaded, Ray workers receive complete, pre-resolved dependency bundles (~1.5GB for BLIP, ~19MB for Simple).

### How Dependencies Reach Ray Workers

Ray workers receive dependencies through two mechanisms:

1. **Packaged site-packages** (via `skip_site_packages=False`):
   - All UDF dependencies resolved by uv (torch, transformers, open-clip-torch, etc.)
   - Geneva and all its transitive dependencies (lance, lancedb, more_itertools, attrs, etc.)
   - Zipped and uploaded to object storage during manifest upload
   - Downloaded and extracted by Ray workers at runtime
   - **Note**: Each UDF has its own unique dependency bundle

2. **py_modules** (UDF code and Geneva modules):
   - `py_modules=["."]`: UDF directory containing Python files (e.g., `blip_caption_udf.py`)
   - Default modules: `geneva` and `pyarrow` (automatically added by Geneva)
   - Enables unpickling of UDF objects on Ray workers

**Key difference from runtime installation**: Dependencies are **pre-resolved and packaged** by uv during manifest upload (`pip=[]`), not installed via pip on Ray workers. This ensures consistent dependency resolution and faster worker startup.

### Test Drivers

Test drivers are simple and decoupled:
- No UDF imports (no ML dependencies)
- Use `conn.context(cluster="name", manifest="name")` pattern
- Just call `tbl.backfill()` on pre-added columns
- Validate results

## Pytest Fixtures

- `geneva_test_bucket`: Returns GCS/S3 bucket path based on `--csp` flag
- `oxford_pets_table`: Creates shared table, uploads manifests, returns (conn, tbl, name)
- `standard_cluster`: Defines CPU cluster with Ray 2.44.0, returns cluster name
- `gpu_cluster`: Defines GPU cluster with Ray 2.44.0, returns cluster name
- `num_images`: Number of images to test (default: 500)
- `batch_size`: Backfill batch size (default: 10)
- `skip_gpu`: Skip GPU tests flag (default: False)

**Note**: Ray is pinned to version 2.44.0 to match live cluster environments (GKE/EKS). When live clusters upgrade, update both `pyproject.toml` dependencies and cluster image versions in `conftest.py`.
