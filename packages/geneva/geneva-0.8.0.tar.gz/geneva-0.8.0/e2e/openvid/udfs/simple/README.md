# Simple OpenVid UDFs

Simple CPU-only UDFs for checking video file existence in GCS.

## UDFs

### HasFile

Checks if a video file exists in GCS bucket.

**Configuration:**
- `VIDEO_BASE_PATH`: Full GCS path (e.g., `gs://bucket/path/to/videos`) - default: `gs://jon-geneva-demo/demo-data/openvid/videos`

Alternatively, configure separately:
- `VIDEO_BUCKET`: GCS bucket name (e.g., `jon-geneva-demo`)
- `VIDEO_PATH`: Path within bucket (e.g., `demo-data/openvid/videos`)

**Usage:**
```python
# Column is added automatically via upload_manifest.py
# Use in backfill:
with conn.context(cluster="my-cluster", manifest="openvid-simple-udfs-v1"):
    tbl.backfill("has_file", batch_size=10)

# Filter to existing videos:
existing = tbl.search().where("has_file = true").to_pandas()
```

## Development

### Install Dependencies
```bash
cd e2e/openvid/udfs/simple
uv sync
```

### Upload Manifest
```bash
export GENEVA_TABLE_NAME=your_table_name
uv run python upload_manifest.py --bucket gs://your-bucket/path
```

### Test
```bash
cd ../../..  # back to workspace root
make test-e2e-openvid-gcp SLUG=mytest NUM_VIDEOS=100 BATCH_SIZE=10
```

## Files

- `simple_udfs.py`: UDF definitions
- `manifest.py`: Manifest factory (reads from pyproject.toml)
- `upload_manifest.py`: Upload script (runs in UDF environment)
- `pyproject.toml`: Dependencies (single source of truth)
