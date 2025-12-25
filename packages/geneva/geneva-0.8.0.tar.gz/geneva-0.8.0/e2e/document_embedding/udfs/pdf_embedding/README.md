# Document Embedding UDF Package

This package contains the heavy dependencies and UDF implementations for the
document embedding pipeline. Columns exposed by this manifest:

- `pdf_bytes`: download PDF from `uploaded_pdf_path`
- `pages`: extract page text (PyMuPDF, max 100 pages)
- `chunks`: chunk page text (size 2048, overlap 200)
- `chunk_embeddings`: `all-MiniLM-L6-v2` embeddings for each chunk

Use `upload_manifest.py` to create/upload the manifest and add columns to the
target table. The test suite calls this automatically via `conftest.py`.
