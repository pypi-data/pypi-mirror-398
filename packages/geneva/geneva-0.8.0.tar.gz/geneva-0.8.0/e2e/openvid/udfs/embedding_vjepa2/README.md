# Video Embeddings UDF

GPU-accelerated video embeddings generation using torchcodec and V-JEPA2.

## Features

- **Efficient video decoding**: Uses torchcodec 0.8.1 to decode videos directly from GCS without downloading
- **Frame sampling**: Uniformly samples frames across the video (default: 64 frames)
- **V-JEPA2 embeddings**: Generates 2D tensor of 1024-dimensional embeddings using Facebook's V-JEPA2 ViT-L model
- **Flexible aggregation**: Returns raw frame/token embeddings for custom aggregation strategies
- **GPU acceleration**: Requires 1 GPU for processing

## Dependencies

- `torch 2.9.0+cu128`: PyTorch with CUDA 12.8 support
- `torchvision 0.24.0+cu128`: Vision utilities
- `transformers 4.57.1`: HuggingFace transformers for CLIP
- `torchcodec 0.8.1`: Efficient video decoding (requires torch 2.9+)
- `fsspec[gcs]`: GCS file access
- `numpy`: Frame sampling

## Configuration

Environment variables:
- `NUM_FRAMES`: Number of frames to sample (default: 64)
- `VJEPA_MODEL`: V-JEPA2 model name (default: "facebook/vjepa2-vitl-fpc64-256")
- `BLOCK_SIZE`: fsspec block size for GCS reads (default: 16MB)
- `VIDEO_EMBEDDING_COL`: Custom column name (default: "video_embedding")

## Usage

### Install Dependencies
```bash
cd e2e/openvid/udfs/video-embeddings
uv sync
```

### Upload Manifest
```bash
export GENEVA_TABLE_NAME=your_table_name
uv run python upload_manifest.py --bucket gs://your-bucket/path
```

### Backfill Embeddings
```python
# Requires GPU cluster
with conn.context(cluster="gpu-cluster", manifest="video-embeddings-v1"):
    tbl.backfill("video_embedding", batch_size=5)  # Small batches for GPU memory

# Query by similarity
results = tbl.search(query_embedding).limit(10).to_pandas()
```

## Output Format

Returns a 2D tensor as nested list: `[[emb1], [emb2], ..., [embN]]`
- Shape: `[num_tokens, 1024]`
- Example: 64 frames → `[64, 1024]` tensor
- Each inner list is a 1024-dimensional embedding for one frame/token

This allows flexible aggregation at search time:

```python
import numpy as np

# Load embeddings
df = tbl.to_pandas()
tensor = np.array(df['video_embedding'].iloc[0])  # Shape: [num_tokens, 1024]

# Mean pooling (standard averaging)
mean_emb = tensor.mean(axis=0)  # [1024]
mean_emb = mean_emb / np.linalg.norm(mean_emb)  # L2 normalize

# Max pooling
max_emb = tensor.max(axis=0)  # [1024]
max_emb = max_emb / np.linalg.norm(max_emb)

# Weighted aggregation (emphasize middle frames)
weights = np.exp(-0.5 * ((np.arange(len(tensor)) - len(tensor)/2) / (len(tensor)/4))**2)
weights = weights / weights.sum()
weighted_emb = np.average(tensor, axis=0, weights=weights)  # [1024]
weighted_emb = weighted_emb / np.linalg.norm(weighted_emb)

# Temporal segments (e.g., first third only)
early_emb = tensor[:len(tensor)//3].mean(axis=0)  # [1024]
early_emb = early_emb / np.linalg.norm(early_emb)
```

## Error Handling

If video processing fails (e.g., corrupted file, decoding error), returns a zero tensor: `[[0.0] * 1024]` (single token with zero embedding).

## Performance

- **GPU Memory**: Requires ~8GB GPU memory
- **Batch Size**: Recommended batch_size=5-10 for backfill operations
- **Frame Sampling**: Adjust NUM_FRAMES based on video length and GPU memory
