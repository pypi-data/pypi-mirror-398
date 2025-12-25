# Fragment Writers and Commit Process

This document describes the fragment writer infrastructure and commit/versioning mechanisms used by both materialized views and backfill operations.

**Audience:** Contributors working on data processing pipelines

**See also:** `materialized_views.md` for materialized view-specific architecture

---

## CheckpointStore Interface

Geneva uses an abstract checkpoint store for intermediate results, shared by both materialized views and backfill operations:

```python
class CheckpointStore(ABC):
    @abstractmethod
    def __setitem__(self, key: str, value: pa.RecordBatch) -> None: ...

    @abstractmethod
    def __getitem__(self, key: str) -> pa.RecordBatch: ...

    @abstractmethod
    def __contains__(self, key: str) -> bool: ...

    @abstractmethod
    def list_keys(self, prefix: str | None = None) -> list[str]: ...
```

**Implementations:**
1. **InMemoryCheckpointStore:** Dictionary-based, for testing
2. **LanceCheckpointStore:** Lance files with session API for production use

**Purpose:**
- Store intermediate processing results for fault tolerance
- Enable deduplication across workers
- Allow resumption from last checkpoint after failures

---

## Fragment Writer and Physical Layout Alignment


### FragmentWriter Class

Ray remote actor responsible for writing a single fragment.

**Initialization:**
```python
@ray.remote
class FragmentWriter:
    def __init__(self, uri: str, fragment_id: int, column_names: list[str]):
        self.uri = uri
        self.fragment_id = fragment_id
        self.column_names = column_names
        self._store = InMemoryCheckpointStore()  # Local cache
```

### Write Process

#### Step 1: Fragment Metadata Extraction

```python
dataset = lance.dataset(self.uri)
frag = dataset.get_fragment(self.fragment_id)

num_physical_rows = frag.physical_rows  # Total rows before filters
num_logical_rows = frag.count_rows()     # Rows after filters/deletions
```

**Why both counts?**
- Physical rows: How many rows to write (with NULLs)
- Logical rows: How many batches to expect from checkpoint store

#### Step 2: Batch Buffering and Sorting

```python
it = _buffer_and_sort_batches(
    num_logical_rows,
    self._store,
    self.checkpoint_keys  # Queue of (offset, checkpoint_key) tuples
)
```

**Purpose:**
- Retrieve batches from checkpoint store
- Sort by offset within fragment
- Ensure sequential row address order

**Implementation uses `SequenceQueue`** to maintain order even if batches arrive out of sequence.

#### Step 3: Physical Layout Alignment

**This is the critical step for materialized views with filters.**

```python
it = _align_batches_to_physical_layout(
    num_physical_rows,
    num_logical_rows,
    self.fragment_id,
    it,
)
```


**Why necessary?**

Lance fragments must have **dense physical layout** with contiguous row addresses. Materialized views can have:
- **Filtered rows** (excluded by `where()`)
- **Sparse logical rows** (only some source rows selected)

These must be represented as **NULL-filled rows** in the physical layout.

**Algorithm:**

1. **Compute expected row addresses:**
   ```python
   frag_mod = fragment_id << 32
   expected_addrs = [frag_mod + i for i in range(num_physical_rows)]
   # Fragment 0: [0, 1, 2, ..., 999]
   # Fragment 1: [4294967296, 4294967297, ..., 4294968295]
   ```

2. **Iterate through batches and fill gaps:**
   ```python
   for batch in batches:
       actual_addrs = batch["_rowaddr"].to_pylist()

       # Find missing addresses
       missing = [addr for addr in expected_addrs
                  if addr not in actual_addrs]

       # Create NULL-filled rows for missing addresses
       null_batch = _create_null_batch(missing, schema)

       # Combine and sort
       combined = pa.concat_tables([batch, null_batch])
       combined = combined.sort_by("_rowaddr")

       yield combined
   ```

3. **Handle intra-batch gaps:**
   **File:** `src/geneva/runners/ray/writer.py`
   **Function:** `_fill_rowaddr_gaps()`

   If a single batch has non-contiguous row addresses:
   ```
   Input:  _rowaddr = [1, 3, 5, 8]
   Output: _rowaddr = [1, 2, 3, 4, 5, 6, 7, 8]
                       [✓, ∅, ✓, ∅, ✓, ∅, ∅, ✓]
   ```

   Where `∅` = NULL for all columns except `_rowaddr`.

**Example scenario:**

```
Materialized view: table.where("x > 50")

Source fragment 0: 100 rows (x values: 0-99)
Matches: rows 51-99 (49 matches)

Expected destination fragment 0 layout:
Row 0:  NULL  (x=0, filtered out)
Row 1:  NULL  (x=1, filtered out)
...
Row 50: NULL  (x=50, filtered out)
Row 51: <data> (x=51, matches filter)
Row 52: <data> (x=52, matches filter)
...
Row 99: <data> (x=99, matches filter)

Total: 100 physical rows, 49 logical rows
```

#### Step 4: Column Filtering

```python
it = _filter_columns_to_schema(it, self.column_names)
```

Removes columns not in materialized view schema:
- `__source_row_id` (internal only)
- `__is_set` (internal only)
- Source columns excluded from view
- Temporary columns like `BACKFILL_SELECTED`

#### Step 5: Data File Writing

```python
# Collect all batches
all_batches = list(it)
table = pa.Table.from_batches(all_batches)

# Write to Lance file
with lance.LanceFileWriter(temp_path, schema) as writer:
    writer.write_batch(table)

# Create DataFile object
data_file = lance.LanceOperation.DataFile(
    path=temp_path,
    fields=[
        lance.LanceOperation.FieldMetadata(id=i)
        for i in range(len(schema))
    ]
)

return (self.fragment_id, data_file, rows_written)
```

**Output:**
- New Lance data file at `temp_path`
- `DataFile` object for commit
- Row count for progress tracking

### Important Implementation Note


When creating PyArrow arrays for NULL-filled rows, Geneva uses **explicit list collection** instead of generators:

```python
# CORRECT (used in codebase)
values = [None if addr in gaps else orig_values[i] for ...]
array = pa.array(values, type=field.type)

# INCORRECT (causes buffer issues)
values = (None if addr in gaps else orig_values[i] for ...)
array = pa.array(values, type=field.type)
```

**Why?** PyArrow needs to compute buffer sizes upfront for variable-width types (strings, lists). Generators don't support this.

---

## Commit and Versioning


### Fragment Writer Session Management


Each fragment has a dedicated `FragmentWriterSession`:

```python
class FragmentWriterSession:
    def __init__(self, fragment_id: int, writer: ray.ActorHandle):
        self.fragment_id = fragment_id
        self.writer = writer
        self.inflight_futures = []
        self.checkpoint_queue = []

    def ingest(self, checkpoint_key: str, offset: int):
        """Queue checkpoint for writing"""
        self.checkpoint_queue.append((offset, checkpoint_key))

        # Start write if not at capacity
        if len(self.inflight_futures) < MAX_INFLIGHT:
            self._dispatch_write()

    def poll(self) -> tuple[int, DataFile, int] | None:
        """Non-blocking check for completion"""
        ready, not_ready = ray.wait(self.inflight_futures, timeout=0)
        if ready:
            return ray.get(ready[0])
        return None

    def drain(self) -> tuple[int, DataFile, int]:
        """Blocking wait for all writes to complete"""
        while self.inflight_futures:
            result = ray.get(self.inflight_futures[0])
            self.inflight_futures.pop(0)
            return result
```

**Benefits:**
- **Pipelining:** Start next write while previous completes
- **Backpressure:** Limit inflight futures to control memory
- **Progress tracking:** Know when fragment is complete

### Recording Fragment Completion

**Method:** `_record_fragment()`

When a fragment write completes:

```python
def _record_fragment(frag_id: int, new_file: DataFile, rows_written: int):
    # 1. Store data file path in checkpoint for deduplication
    checkpoint_key = f"fragment_data_file:{uri}:{frag_id}:{task_hash}"
    checkpoint_store[checkpoint_key] = new_file.path

    # 2. Track input row count
    self.frag_inputs[frag_id] += rows_written

    # 3. Check if fragment was skipped (already existed)
    was_skipped = frag_id in self.skipped_fragment_ids

    # 4. Add to commit list
    self.to_commit.append((frag_id, new_file, rows_written))

    # 5. Update progress
    self.job_tracker.record_fragment_completion(frag_id)

    # 6. Attempt incremental commit
    self._commit_if_n_fragments()
```

### Incremental Commit Strategy

**Method:** `_commit_if_n_fragments()`

Geneva commits every `commit_granularity` fragments (default: 10):

```python
def _commit_if_n_fragments(self):
    if len(self.to_commit) < self.commit_granularity:
        return  # Not enough fragments yet

    # Take batch to commit
    batch = self.to_commit[:self.commit_granularity]
    self.to_commit = self.to_commit[self.commit_granularity:]

    # Commit batch
    self._commit_fragments(batch)
```

**Why incremental commits?**
1. **Fault tolerance:** Committed fragments survive failures
2. **Progress visibility:** Users can query partial results
3. **Memory efficiency:** Free checkpoint store entries after commit
4. **Concurrency:** Shorter critical sections reduce conflicts

### Commit Operation

**Lance API:**
```python
operation = lance.LanceOperation.DataReplacement(
    replacements=[
        lance.LanceOperation.DataReplacementGroup(
            fragment_id=frag_id,
            new_file=new_file,
        )
        for frag_id, new_file, _rows in to_commit
    ]
)

lance.LanceDataset.commit(
    uri=self.ds_uri,
    operation=operation,
    read_version=self.ds_version  # Optimistic concurrency control
)
```

**Key features:**
- **Atomic:** All fragments committed together or none
- **Versioned:** Based on read version, detects conflicts
- **Multi-fragment:** Can replace many fragments in single commit

### Conflict Detection and Retry


If commit fails due to concurrent writer:

```python
try:
    lance.LanceDataset.commit(uri, operation, read_version=version)
except lance.errors.CommitConflictError:
    # Exponential backoff retry
    if attempt < MAX_RETRIES:
        time.sleep(2 ** attempt)
        retry_commit()
    else:
        raise
```

**Conflict resolution:**
1. Read latest version
2. Check if any of our fragments were modified
3. If not, retry commit with new version
4. If yes, fail (rare - indicates concurrent refresh)

### Skipped Fragment Handling


Fragments already processed (checkpoint exists) are skipped during task creation but **collected for commit inclusion**.

**How it works:**
1. During planning, identify which destination fragments have existing checkpoints
2. Skip creating processing tasks for these fragments (no UDF re-execution)
3. Collect references to the existing data files from the checkpoint store
4. Include these references in the final commit alongside newly processed fragments

**Why collect instead of just skip?**
- Ensures consistent table version with all fragments included
- Allows commit to reference existing data files without reprocessing
- Maintains proper Lance table structure

**Benefits:**
- **Idempotency:** Safe to re-run refresh
- **Efficiency:** Skip already-computed fragments (no UDF re-execution)
- **Partial refresh:** Only recompute changed source data
- **Commit consistency:** All fragments included in final commit

---
