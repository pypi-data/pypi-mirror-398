# Document Embedding E2E Suite

End-to-end tests for running a PDF document embedding pipeline on Geneva using the
public DigitalCorpora sample set. The suite mirrors the structure used by the
`e2e/openvid` and `e2e/oxford-pets` suites: lightweight test drivers plus isolated
UDF environments for heavy ML dependencies.

## Dataset

- Source metadata: `s3://ray-example-data/digitalcorpora/metadata/`
- Columns: `file_name`, `uploaded_pdf_path`
- Each `uploaded_pdf_path` points to a publicly readable PDF in the same bucket.

## Pipeline (Geneva)

1. Download PDF bytes from S3 (`pdf_bytes`)
2. Extract page text with PyMuPDF (limit 100 pages) → `pages`
3. Chunk text with `RecursiveCharacterTextSplitter` (size 2048, overlap 200) → `chunks`
4. Embed chunks with `sentence-transformers/all-MiniLM-L6-v2` → `chunk_embeddings`

All UDFs live in `udfs/pdf_embedding` and are uploaded as a manifest
`document-embedding-udfs-v1`.

## Structure

```
document_embedding/
├── README.md
├── conftest.py            # Fixtures, cluster definitions, manifest upload
├── dataset.py             # Helpers to load DigitalCorpora metadata
├── pyproject.toml         # Test-driver dependencies
├── test_drivers/          # Tests (no ML deps)
└── udfs/
    └── pdf_embedding/     # UDF package + manifest uploader
```

Benchmark scripts for comparison live in `benchmarks/`:
- `ray_data_main.py` (original Ray Data benchmark)
- `geneva_main.py` (Geneva version)
- `daft_main.py` (Daft variant)

### Running the Geneva benchmark

Uses the same cluster shape as the e2e fixtures (no manual cluster name needed):
```bash
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m e2e.document_embedding.benchmarks.geneva_main \
  --csp gcp \
  --slug bench1 \
  --num-docs 200 \
  --batch-size 8 \
  --manifest-name document-embedding-udfs-v1
```
What it does:
- loads DigitalCorpora metadata, creates a table in the derived bucket
- uploads the document-embedding manifest and adds columns
- auto-defines `e2e-document-embedding-cluster` (Ray 2.44 CPU) and backfills `pdf_bytes`, `pages`, `chunks`, `chunk_embeddings`

## Running Tests

From the workspace root:

```bash
uv sync --all-groups --all-extras --locked
make test-e2e-document-embedding-gcp SLUG=myrun NUM_DOCS=20 BATCH_SIZE=4
```

Or directly from the suite directory:

```bash
cd e2e/document_embedding
RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run -m pytest test_drivers \
  --csp=gcp --num-docs=20 --batch-size=4 -v
```

### Useful Options

- `--csp` (`gcp`|`aws`): Cloud to target (default `gcp`)
- `--test-slug`: Slug for isolating buckets (default random)
- `--bucket-path`: Override the test bucket root
- `--num-docs`: Number of PDFs to process (default 20)
- `--batch-size`: Backfill batch size (default 4)

### Notes

- Set `RAY_ENABLE_UV_RUN_RUNTIME_ENV=0` when invoking pytest to avoid uv/Ray
  runtime conflicts.
- The suite uploads manifests automatically during the first test run and
  reuses them for the session.
