# OpenVid E2E Test Suite

End-to-end tests for Geneva using the OpenVid-1M video dataset.

## Architecture

This test suite follows the same **separation of UDF environments from test drivers** pattern as Oxford Pets:

- **Test Drivers** (`test_drivers/`) - Minimal dependencies, just run backfills
- **UDF Packages** (`udfs/`) - Isolated environments with ML dependencies for video processing

### Data Source

The test suite downloads video metadata from the OpenVid-1M dataset on HuggingFace:
```
https://huggingface.co/datasets/nkp37/OpenVid-1M/resolve/main/data/train/OpenVid-1M.csv
```

Videos are stored in GCS at: `gs://jon-geneva-demo/demo-data/openvid/videos`

The CSV is downloaded and parsed to create a Geneva table preserving all CSV columns:
- `video`: Video filename
- `caption`: Video caption/description
- `frame`: Number of frames
- `fps`: Frames per second
- `seconds`: Video duration
- Plus any other columns in the CSV

Optionally, a `video_path` column is added with full GCS paths combining the source bucket + video filename.

### Two-Stage Process

1. **Manifest Upload** (automatic via pytest fixture):
   - Runs `upload_manifest.py` in each UDF's environment via `uv run`
   - Creates manifest from UDF's `pyproject.toml` dependencies
   - Uploads manifest to Geneva and adds columns to table
   - Uses `GENEVA_TABLE_NAME` environment variable

2. **Test Execution**:
   - Tests run with minimal dependencies
   - Load pre-uploaded manifests by name
   - Ray workers execute UDFs in isolated environments defined by manifests

## Structure

```
openvid/
├── pyproject.toml          # Test driver dependencies (minimal)
├── conftest.py             # Fixtures: table creation, manifest upload
├── test_drivers/           # Test drivers (no UDF imports)
│   └── test_table_creation.py  # Basic table validation
└── udfs/                   # UDF packages (separate environments)
    └── (to be added)       # Video embedding and processing UDFs
```

## Running Tests

### Prerequisites

Install test driver dependencies from workspace root:
```bash
uv sync --all-groups --all-extras --locked
```

### From Workspace Root (Recommended)

```bash
# Run all openvid tests (manifest upload is automatic)
make test-e2e-openvid-gcp SLUG=mytest NUM_VIDEOS=100 BATCH_SIZE=10

# Or directly with pytest
cd e2e/openvid
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest test_drivers --csp=gcp --test-slug=mytest --num-videos=100 --batch-size=10 -v

# Run specific test
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest test_drivers/test_table_creation.py -v
```

### Command-line Options

- `--csp`: Cloud service provider (gcp or aws), default: gcp
- `--test-slug`: Test slug for identifying runs, default: random
- `--bucket-path`: Override default test bucket path
- `--num-videos`: Number of videos to process, default: 100
- `--batch-size`: Backfill batch size, default: 10
- `--skip-gpu`: Skip GPU tests, default: false
- `--source-bucket`: Source GCS bucket with videos, default: gs://jon-geneva-demo/demo-data/openvid/videos

## Key Concepts

### Environment Variables

- `GENEVA_TABLE_NAME`: Table name for column addition (set by pytest fixture)
- `RAY_ENABLE_UV_RUN_RUNTIME_ENV=0`: Required to prevent conflicts between uv and Ray

### Test Fixtures

- `geneva_test_bucket`: Returns GCS/S3 bucket path based on `--csp` flag
- `openvid_table`: Creates shared table with video paths, uploads manifests, returns (conn, tbl, name)
- `standard_cluster`: Defines CPU cluster with Ray 2.44.0, returns cluster name
- `gpu_cluster`: Defines GPU cluster with Ray 2.44.0, returns cluster name
- `num_videos`: Number of videos to test (default: 100)
- `batch_size`: Backfill batch size (default: 10)
- `skip_gpu`: Skip GPU tests flag (default: False)
- `source_bucket`: Source GCS bucket with videos

## Adding UDF Packages

When adding new UDF packages:

1. Create directory under `udfs/` (e.g., `udfs/video-embeddings/`)
2. Add `pyproject.toml` with dependencies
3. Implement UDF in Python module
4. Create `manifest.py` factory function
5. Create `upload_manifest.py` script
6. Update `conftest.py` to include the package in `_upload_all_manifests()`
7. Add test driver in `test_drivers/`

See Oxford Pets suite for examples of UDF package structure.

## Next Steps

1. Add video embedding UDF packages
2. Add video processing UDF packages
3. Implement test drivers for each UDF
4. Add to CI/CD pipeline
