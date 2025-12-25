# Materialized Views Architecture

**Audience:** Sales engineers, support engineers, architects, and new contributors

**Purpose:** Understand how Geneva materialized views work at a conceptual level to support customers, debug issues, and contribute to the codebase.

---

## What are Materialized Views?

Materialized views are precomputed query results that are stored as physical tables. Instead of running expensive queries repeatedly, you compute the results once and store them for fast access.

**Business Value:**
- **Performance:** Query results cached as tables (milliseconds vs. minutes)
- **Cost Efficiency:** Compute once, query many times
- **Efficient Data Loading:** Precomputed transformations for exploratory analysis and ML training

**Geneva's Approach:**
Geneva materialized views are built on Lance tables with support for:
- Filtering (SQL WHERE clauses)
- Shuffling (randomized ordering for ML training)
- User-defined functions (computed columns like embeddings, predictions)
- Incremental refresh (process only new data, not everything)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MATERIALIZED VIEW SYSTEM                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐                                  ┌──────────────┐
│ SOURCE TABLE │                                  │ MATERIALIZED │
│  (Lance DB)  │                                  │     VIEW     │
│              │                                  │  (Lance DB)  │
│ ┌──────────┐ │                                  │ ┌──────────┐ │
│ │Fragment 0│ │                                  │ │Fragment 0│ │
│ │Fragment 1│ │                                  │ │Fragment 1│ │
│ │Fragment 2│ │                                  │ │Fragment 2│ │
│ └──────────┘ │                                  │ └──────────┘ │
└──────┬───────┘                                  └──────▲───────┘
       │                                                 │
       │ 1. Read source data                 4. Write results
       ▼                                                  │
┌─────────────────────────────────────────────────────────────────┐
│                      RAY PROCESSING CLUSTER                     │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Worker 1   │  │   Worker 2   │  │   Worker 3   │           │
│  │              │  │              │  │              │           │
│  │  Apply UDFs  │  │  Apply UDFs  │  │  Apply UDFs  │           │
│  │   Process    │  │   Process    │  │   Process    │           │
│  │   Batches    │  │   Batches    │  │   Batches    │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │ 2. Store checkpoints                │
│                           ▼                                     │
│                   ┌─────────────────┐                           │
│                   │ CHECKPOINT STORE│                           │
│                   │                 │                           │
│                   │  Deduplication  │                           │
│                   │  Progress Track │                           │
│                   │  Fault Tolerant │                           │
│                   └────────┬────────┘                           │
│                            │ 3. Fragment Writers read ckpts     │
└────────────────────────────┼────────────────────────────────────┘
                             ▼
                     Fragment Writers
                     (see fragment_writers.md)
```

### Key Components

1. **Source Table**: Original Lance table with raw data
2. **Ray Workers**: Distributed processors that apply transformations (filters, UDFs)
3. **Checkpoint Store**: Intermediate storage for fault tolerance and deduplication
4. **Fragment Writers**: Specialized writers that commit results to the materialized view
5. **Materialized View**: Destination Lance table with computed results

---

## Recent Enhancements (v0.8.x+)

**For Sales Engineers & Architects:** Highlight these capabilities when discussing materialized views:

### Incremental Refresh Optimizations

**Checkpoint Reuse:** The system now intelligently skips re-processing of data that hasn't changed:
- Previously processed fragments are automatically detected and reused
- Only new or modified data is computed, dramatically reducing refresh time
- **Performance impact:** A table with 1TB of existing data + 10GB new data only processes the 10GB

**Fragment Granularity Control (`max_rows_per_fragment`):**
- Fine-tune parallelism by controlling destination fragment sizes during refresh
- Smaller fragments = more parallel workers = faster refresh for large updates
- Useful for memory-intensive UDFs (embeddings, predictions)
- **Example:** Processing 1M new rows with `max_rows_per_fragment=50000` creates 20 fragments instead of 1, allowing 20x more parallelism

**Use Case:** A customer with a 10TB table running hourly refreshes can:
1. Enable stable row IDs on source table (one-time setup)
2. Use `max_rows_per_fragment=100000` for optimal parallelism
3. Each refresh only processes new data since last run
4. Refresh time proportional to new data size, not total table size

### Performance Characteristics Summary

| Operation | Time Complexity | Typical Time | Notes |
|-----------|----------------|--------------|-------|
| First refresh | O(n) | Minutes-hours | All data processed |
| Incremental refresh | O(k) where k=new rows | Seconds-minutes | Only new data processed |
| Incremental with max_rows_per_fragment | O(k/p) where p=parallelism | Faster | More workers processing simultaneously |
| Query materialized view | O(1) scan | Milliseconds | No recomputation needed |

---

## How It Works: Creation & Refresh

### 1. Creating a Materialized View

```
User Code:
  view = query.where("age > 21").add_column(sentiment_udf).create_materialized_view()

Flow:
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐
│ Extract │────>│   Create    │────>│ Initialize  │────>│ Ready to │
│  Query  │     │ Placeholder │     │  Metadata   │     │ Refresh  │
│ Config  │     │    Table    │     │             │     │          │
└─────────┘     └─────────────┘     └─────────────┘     └──────────┘

Result: Empty table with:
- Schema matching query output
- Metadata storing query definition
- Placeholder rows with NULL values
```

**What happens:**
1. Query is serialized and stored in table metadata
2. Empty destination table created with correct schema
3. Placeholder rows added (one per matching source row)
4. Rows contain `__source_row_id` (pointer to source data)
5. Table ready for refresh operation

**⚠️ Important Recommendation: Stable Row IDs**

Materialized views need the source table to have **stable row IDs** enabled. This ensures that row identifiers remain constant even after table compaction operations, which is essential for incremental refresh across multiple versions.

**How to enable stable row IDs:**
```python
# When creating a new table
db.create_table(
    name='my_table',
    data=my_data,
    storage_options={'new_table_enable_stable_row_ids': 'true'}
)
```

**What happens if stable row IDs are not enabled:**
The table can be created and initially refreshed, but subsequent refreshes can only refresh to the **same source version** as the original (so, the same rows and columns as the original). Refreshing to a different version will fail.

**Recommendation**: Always enable stable row IDs for source tables used in materialized views to support full incremental refresh capabilities.

See the "Stable Row IDs" section below for more details.

### 2. Refreshing the View (Full Refresh)

```
User code:
  view.refresh()

Step 1: Plan
┌─────────────────────────────────────────────────────────────┐
│  Read destination table → Find all rows with __is_set=False │
│  Create tasks: one per batch of rows                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 2: Execute (Parallel)
┌───────────────────────────────────────────────────────────────────┐
│  Ray Worker 1            Ray Worker 2            Ray Worker 3     │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐ │
│  │Read batch via│        │Read batch via│        │Read batch via│ │
│  │__source_row_id        │__source_row_id        │__source_row_id │
│  ├──────────────┤        ├──────────────┤        ├──────────────┤ │
│  │Apply filters │        │Apply filters │        │Apply filters │ │
│  ├──────────────┤        ├──────────────┤        ├──────────────┤ │
│  │Run UDFs      │        │Run UDFs      │        │Run UDFs      │ │
│  ├──────────────┤        ├──────────────┤        ├──────────────┤ │
│  │Write to      │        │Write to      │        │Write to      │ │
│  │checkpoint    │        │checkpoint    │        │checkpoint    │ │
│  └──────────────┘        └──────────────┘        └──────────────┘ │
└───────────────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 3: Commit
┌─────────────────────────────────────────────────────────────┐
│  Fragment Writers read checkpoints → Write to destination   │
│  Update __is_set=True for processed rows                    │
│  Commit new version of materialized view table              │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Destination-driven: Tasks created based on destination table structure
- Checkpointed: Progress saved to handle failures
- Idempotent: Safe to re-run, skips already-processed work

### 3. Incremental Refresh (Processing New Data)

When source table gets new data, only process the additions:

```
User code:
  view.refresh()

Before:
  Source: [Frag 0] [Frag 1] [Frag 2]
  View:   [Frag 0] ← contains results from source frags 0,1,2

After source update:
  Source: [Frag 0] [Frag 1] [Frag 2] [Frag 3] [Frag 4] ← NEW

Incremental Refresh:
  ┌─────────────────────────────────────────┐
  │ 1. Identify new source fragments (3,4)  │
  │ 2. Apply original query to new data     │
  │ 3. Append placeholder rows to view      │
  │ 4. Map destination fragments to source  │
  │ 5. Process only new rows (parallel)     │
  │ 6. Mark new data as processed           │
  └─────────────────────────────────────────┘

Result:
  View:   [Frag 0] [Frag 1] ← Frag 0 untouched, Frag 1 is new data
          (old)    (new computations)
```

**Benefits:**
- Only compute results for new source data
- Existing results remain unchanged (no recomputation)
- Proportional cost: process 1MB of new data, not 1TB total

---

## Key Concepts Explained

### Stable Row IDs

**What are stable row IDs?**

Stable row IDs are a Lance feature that ensures row identifiers remain constant even when table operations like compaction reorganize the physical data. Without stable row IDs, compaction changes the physical row addresses, which breaks materialized view refresh.

**Why materialized views benefit from stable row IDs:**

Materialized views track source data using `__source_row_id` pointers for refresh operations. During incremental refresh:
1. The refresh process identifies which source rows need to be processed
2. It reads data from the source table using these row IDs
3. If compaction changes the row IDs, the pointers become invalid
4. The refresh cannot find the correct source data and will fail

**Important**: The MV table itself remains readable and usable even if `__source_row_id` is invalid. You can still query the computed data. It's only the refresh operation that fails.

Without stable row IDs, refreshes can only target the same source version to avoid compaction issues.

**The compaction problem:**

Without stable row IDs, normal table maintenance breaks materialized view refresh:
```
Initial state:
  Source table: 4 fragments with row IDs [0-99], [100-199], [200-299], [300-399]
  Materialized view: Tracks rows via __source_row_id = [5, 150, 275, 350]

After compaction (WITHOUT stable row IDs):
  Source table: 2 fragments with row IDs [0-199], [200-399]
  Row IDs change: Old row 150 is now at a different physical address
  Materialized view: __source_row_id = [5, 150, 275, 350] now points to WRONG data
  Result: MV table is still readable and usable, but refresh operations will fail

After compaction (WITH stable row IDs):
  Source table: 2 fragments (physically reorganized)
  Row IDs remain: 5, 150, 275, 350 still point to the same logical rows
  Materialized view: Both queries and refresh operations work correctly
```

**Concrete example with sample data:**

Let's say we have a source table with user data spread across multiple fragments, and create a materialized view that filters adults:

```python
# Source table data (initial state) - 2 fragments
# Fragment 0:
source_table (fragment 0):
  row_id | name    | age
  -------|---------|----
  0      | Alice   | 15
  5      | Bob     | 25

# Fragment 1:
source_table (fragment 1):
  row_id | name    | age
  -------|---------|----
  3      | Carol   | 30
  8      | Dave    | 12

# Combined logical view:
source_table:
  row_id | fragment | offset | name  | age
  -------|----------|--------|-------|----
  0      | 0        | 0      | Alice | 15
  5      | 0        | 1      | Bob   | 25
  3      | 1        | 0      | Carol | 30
  8      | 1        | 1      | Dave  | 12
```

Now let's see what happens after compaction with different approaches:

**Key difference across implementations:**

The approach to storing `__source_row_id` has evolved:

- **v0.7.x and earlier**: Fragment+offset encoding `(fragment_id << 32 | offset)`. MV tables remain readable, but refresh breaks when fragment structure changes after compaction.
- **v0.8.x+ without stable row IDs**: Same fragment+offset encoding `(fragment_id << 32 | offset)` via Lance's `_rowid`. MV tables remain readable, but refresh breaks when compaction changes fragment IDs.
- **v0.8.x+ with stable row IDs**: Uses Lance's stable logical row IDs. Both MV queries and refresh work correctly even after compaction.

**Note**: v0.7.x and v0.8.x+ without stable row IDs use the same encoding (Version 1 in metadata). Both fail the same way after compaction: old fragment IDs no longer exist in the compacted table.

Let's see examples of each approach:

**Approach 1: Fragment + Offset encoding (v0.7.x and v0.8.x+ without stable row IDs)**
```python
# Uses fragment+offset encoding: __source_row_id = (fragment_id << 32 | offset)
# Both v0.7.x and v0.8.x+ without stable row IDs use this encoding

# Materialized view: filter for age >= 18
# After initial refresh:
mv_adults:
  __source_row_id | __is_set | name  | age
  ----------------|----------|-------|----
  1               | true     | Bob   | 25   # (0<<32 | 1) = Fragment 0, offset 1
  4294967296      | true     | Carol | 30   # (1<<32 | 0) = Fragment 1, offset 0

# Breaking down the encoding:
# - Bob: 1 = (0 << 32) | 1 = Fragment 0, offset 1
# - Carol: 4294967296 = (1 << 32) | 0 = Fragment 1, offset 0
#   (since 1 << 32 = 4294967296)

# After compaction into a single fragment:
source_table (after compaction, new fragment created):
  fragment | offset | name  | age
  ---------|--------|-------|----
  3        | 0      | Alice | 15   # New fragment 3 (old fragments 0, 1 removed)
  3        | 1      | Dave  | 12
  3        | 2      | Bob   | 25
  3        | 3      | Carol | 30

# The MV table itself is still usable:
mv_adults (table still readable):
  __source_row_id | __is_set | name  | age
  ----------------|----------|-------|----
  1               | true     | Bob   | 25   # User data (name, age) is valid ✓
  4294967296      | true     | Carol | 30   # User data (name, age) is valid ✓

# PROBLEM: __source_row_id is now invalid (refresh will fail)
# - __source_row_id=1 (Frag 0, offset 1) - Fragment 0 no longer exists! ❌
# - __source_row_id=4294967296 (Frag 1, offset 0) - Fragment 1 no longer exists! ❌
# Pointers reference non-existent fragments in the latest table version.
# The MV can still be queried and read, but refresh operations will fail!
```

**Approach 2: Stable row IDs (v0.8.x+ WITH stable row IDs enabled - RECOMMENDED)**
```python
# Uses Lance's stable row IDs feature - logical IDs persist across compaction

# Materialized view: filter for age >= 18
# After initial refresh:
mv_adults:
  __source_row_id | __is_set | name  | age
  ----------------|----------|-------|----
  5               | true     | Bob   | 25   # Stable ID: 5
  3               | true     | Carol | 30   # Stable ID: 3

# After source table compaction with stable row IDs enabled:
source_table (after compaction, 1 fragment):
  row_id | name  | age    # Physical reorganized, but stable IDs preserved
  -------|-------|----
  0      | Alice | 15     # Stable ID: 0
  5      | Bob   | 25     # Stable ID: 5 (same as before!)
  3      | Carol | 30     # Stable ID: 3 (same as before!)
  8      | Dave  | 12     # Stable ID: 8

# Note: Physical storage changed (now 1 fragment instead of 2), but
# stable row IDs maintained the logical row identifiers. The data may
# be in different positions on disk, but stable ID 5 still refers to
# Bob, stable ID 3 still refers to Carol, etc.

# Materialized view has the same stable row IDs
mv_adults:
  __source_row_id | __is_set | name  | age
  ----------------|----------|-------|----
  5               | true     | Bob   | 25   # Stable ID: 5
  3               | true     | Carol | 30   # Stable ID: 3

# SUCCESS: When refresh tries to read source rows:
# - __source_row_id=5 still points to Bob (age 25) ✓
# - __source_row_id=3 still points to Carol (age 30) ✓
# The MV works correctly even after compaction!
```

**Technical note:**

Stable row IDs is a feature in Lance added in version 0.21.0 (December 2024). It's enabled via the `new_table_enable_stable_row_ids` storage option when creating tables (added in lancedb 0.25.4b3).

**Important: pylance version requirement for blobs:**

When using blob columns with stable row IDs enabled, **pylance >= 1.1.0b2 is required**. Earlier versions have a bug where `take_blobs` fails on fragments created via DataReplacement operations (used during materialized view refresh). The error manifests as "index out of bounds" when accessing blob data from the second or later fragments.

**Troubleshooting:**

If a customer encounters a warning or error related to stable row IDs:

**During MV creation:**
1. A warning will be issued if the source table doesn't have stable row IDs
2. The MV will be created successfully, but with limitations
3. Refresh operations will only work for the same source version

**During refresh:**
1. If the error mentions "version" and "stable row IDs", the refresh is trying to use a different source version
2. To fix: Either refresh to the same version, or recreate the source table with stable row IDs enabled
3. To enable full refresh capabilities: Recreate source table with `storage_options={'new_table_enable_stable_row_ids': 'true'}`
4. Existing data can be copied to a new table with stable row IDs enabled

### Fragment Mapping

Materialized views maintain a mapping from destination rows back to source rows:

```
SOURCE TABLE             MATERIALIZED VIEW
┌──────────────┐       ┌────────────────────────┐
│ Fragment 0   │       │ Fragment 0             │
│  Row 0       │       │  Row 0 (__source_row_id│
│  Row 1       │       │         = Frag2:Row15) |
│  Row 2       │       │  Row 1 (__source_row_id│
├──────────────┤       │         = Frag0:Row2)  |
│ Fragment 1   │       │  Row 2 (__source_row_id│
│  Row 0       │       │         = Frag1:Row3)  |
│  ...         |       └────────────────────────┘  
|  Row 3       │
├──────────────┤
│ Fragment 2   │
│  Row 0       │
│  Row 1       |
|  ...         │
│  Row 15      |
└──────────────┘
```
Destination rows can come from any source fragment. This can be because of filtering (fewer rows in destination than source), shuffling, or just because the materialized view was created later. So we have a field in each materialized view row called `__source_row_id` that points back to its source fragment/row.

### Checkpointing for Fault Tolerance


Without checkpointing:
  Process 1000 batches → Crash at batch 999 → Start over (1000 batches)

With checkpointing:
  Process 1000 batches → Crash at batch 999 → Resume from 999 (1 batch)

Checkpoint Store:
```
  ┌─────────────────────────────────────┐
  │ Key: fragment_3_batch_0_100         │
  │ Value: /path/to/computed/data.lance │
  ├─────────────────────────────────────┤
  │ Key: fragment_3_batch_100_200       │
  │ Value: /path/to/computed/data.lance │
  └─────────────────────────────────────┘
```

### Source Version Management

Track which version of the source table was used:

```
Timeline:
  T1: Source v1 (1000 rows) → Create view → View refs source v1
  T2: Source v2 (1100 rows) → Source grows
  T3: Refresh view → Automatically uses latest (v2)
  T4: Source v3 (1200 rows) → Source grows
  T5: Refresh to specific version: view.refresh(src_version=2)
```

**Use cases:**
- **Reproducibility**: Pin to specific source version for testing
- **Rollback**: Revert to earlier source version

---

## Common Scenarios

### Scenario 1: Filtered Dataset for Team Sharing

Problem: Team B only needs customers in EMEA region

Solution:
  1. Create view: 
     ```
     emea_view = table.search(None).where("region == 'EMEA'").create_materialized_view(conn=db, view_name="emea_data")
     ```
  2. Team B queries `emea_view` (only EMEA data)
  3. Automatic access control via separate table
  4. Incremental refresh keeps view up-to-date

### Scenario 2: ML Training Data with Embeddings

Problem: Computing embeddings is expensive (GPU required)

Solution:
  1. Create view with embedding UDF: .add_column(embedding_udf)
  2. First refresh computes all embeddings (one-time cost)
  3. Incremental refresh only computes embeddings for new data
  4. Training reads precomputed view (no GPU needed)

Result: Train on 1M rows without recomputing embeddings each time

---

## Quick Reference

**Prerequisites:**
- ⚠️ Source table **should** be created with `storage_options={'new_table_enable_stable_row_ids': 'true'}`

**When to use materialized views:**
- Expensive queries run repeatedly
- Need precomputed aggregations or transformations
- Want to cache intermediate results
- ML training requires consistent dataset snapshots

**Key operations:**
- `create_materialized_view()`: Initialize empty view (warns if no stable row IDs)
- `view.refresh()`: Compute/update results (validates version compatibility)
- `view.refresh(src_version=N)`: Refresh to specific source version
- `view.refresh(max_rows_per_fragment=N)`: Control destination fragment granularity

**Performance characteristics:**
- **Creation**: Fast (just metadata and validation, no computation)
- **First refresh**: Slow (compute all results)
- **Incremental refresh**: Fast (only new data)
- **Query**: Fast (materialized results)

**Common issues:**
- **Warning during creation**: Source table doesn't have stable row IDs - MV will be limited to refreshing to the same version
- **Error: "Cannot refresh materialized view to version X"**: Trying to refresh to a different version without stable row IDs
  - Solution: Refresh to the same version, or recreate source table with stable row IDs enabled
- **Refresh fails after compaction**: Check if source table has stable row IDs enabled

**Performance troubleshooting:**
- **Refresh taking too long on incremental updates?**
  - Check if checkpoint reuse is working: Look for "Collected N checkpointed fragments" in logs
  - Try `max_rows_per_fragment=50000` or `100000` to increase parallelism
  - Verify stable row IDs are enabled on source table

- **Out of memory during refresh?**
  - Reduce `max_rows_per_fragment` to process smaller batches (e.g., `10000`)
  - Particularly important for memory-intensive UDFs (embeddings, large ML models)

- **Refresh processing data that was already computed?**
  - Checkpoint store may have been cleared - this is expected after first run
  - Subsequent refreshes will reuse checkpoints automatically
  - Source data may have changed (backfill) - data file tracking detects this
  - Check logs for "Checkpoint data files mismatch" messages


**For more details:**
- Stable row IDs: See "Stable Row IDs" section in "Key Concepts Explained"
- Incremental refresh mechanics: See "Incremental Refresh with New Source Data" below
- Fragment writer details: See `fragment_writers.md`
- Persistent formats: See "Persistent Formats Reference" below

---

## Best Practices for Production Deployments

**For Architects & Technical Leads:**

### Source Table Configuration

**Always enable stable row IDs for source tables used in materialized views:**
```python
db.create_table(
    name='events',
    data=data,
    storage_options={'enable_move_stable_row_ids': 'true'}
)
```

**Why:** Without stable row IDs, incremental refresh is limited to the same source version, which severely restricts utility. Stable row IDs have minimal overhead (~5% storage, negligible performance impact) but enable full incremental refresh capabilities.

### Refresh Performance Tuning

**Choosing `max_rows_per_fragment` value:**

| Scenario | Recommended Value | Reasoning |
|----------|------------------|-----------|
| Small updates (<100K rows) | Default (omit parameter) | Overhead of fragment management not worth it |
| Medium updates (100K-1M rows) | 50,000 - 100,000 | Good balance of parallelism vs. overhead |
| Large updates (>1M rows) | 100,000 - 500,000 | Maximize parallelism for large batches |
| Memory-intensive UDFs | 10,000 - 50,000 | Reduce memory footprint per worker |
| CPU-bound UDFs | 100,000 - 500,000 | Maximize CPU utilization across workers |

**Example configuration for embedding pipeline:**
```python
# Source: Image table with 10M images
# UDF: Generate embeddings (GPU required, memory-intensive)
# Update frequency: 100K new images daily

# Recommended configuration:
mv.refresh(max_rows_per_fragment=25000)

# Result: 4 fragments created, 4 Ray workers processing in parallel
# Each worker handles 25K images, staying within GPU memory limits
```

### Checkpoint Store Management

**Checkpoints enable incremental refresh** by storing intermediate results:

- **Location:** Stored alongside the materialized view table
- **Cleanup:** Automatically managed, no manual intervention needed
- **Size:** Proportional to processed data (typically 10-20% of MV size)
- **Persistence:** Survives across refresh operations to enable checkpoint reuse

**When checkpoints are invalidated:**
- Source table schema changes (columns added/removed/renamed)
- Query definition changes (filter, UDFs, shuffle modified)
- Materialized view is recreated
- Source data backfilled (data file changes - detected automatically)
- UDF re-run on same column (new data files created - detected automatically)
- Source table version changes (batch-level checkpoints)

### Monitoring & Observability

**Key metrics to track:**

1. **Checkpoint reuse rate:**
   - Log message: "Collected N checkpointed fragments with M rows"
   - Should be non-zero for incremental refreshes
   - If always zero, check if stable row IDs are enabled

2. **Fragment processing time:**
   - Each fragment should process in parallel
   - Unbalanced times indicate skewed data distribution
   - Consider adjusting `max_rows_per_fragment` for more even distribution

3. **Refresh duration trend:**
   - Should be proportional to new data size, not total table size
   - Linear growth indicates checkpoint reuse is working
   - Super-linear growth suggests checkpoints aren't being reused

### Common Anti-Patterns to Avoid

❌ **Creating MVs without stable row IDs on source**
- Limits refresh to same version only
- Breaks after any compaction operation
- ✅ **Solution:** Always enable stable row IDs

❌ **Using default fragment size for large updates**
- Single fragment = single worker = no parallelism
- ✅ **Solution:** Set `max_rows_per_fragment` based on update size

❌ **Clearing checkpoint store manually**
- Forces full recomputation on next refresh
- ✅ **Solution:** Let system manage checkpoints automatically

❌ **Frequent schema changes on source table**
- Invalidates checkpoints, forcing full refresh
- ✅ **Solution:** Plan schema evolution carefully, batch changes

---

## Implementation Internals

**Note:** The following sections provide detailed implementation information for debugging and supporting materialized views. These are intended for on-call engineers, support engineers, and contributors working on the codebase.

1. [Persistent Formats Reference](#persistent-formats-reference)
2. [Fragment Mapping: Source to Checkpoint to Destination](#fragment-mapping-source-to-checkpoint-to-destination)
3. [Checkpoint Mechanism and Progress Tracking](#checkpoint-mechanism-and-progress-tracking)
4. [Materialized View Refresh Process](#materialized-view-refresh-process)
5. [Incremental Refresh with New Source Data](#incremental-refresh-with-new-source-data)
6. [Source Version Management](#source-version-management)
7. [Query Operations Impact on Fragments and Layouts](#query-operations-impact-on-fragments-and-layouts)
8. [Checkpoint Store Implementations](#checkpoint-store-implementations)
9. [Error Handling and Recovery](#error-handling-and-recovery)
10. [Performance Tuning](#performance-tuning)
11. [Testing Examples](#testing-examples)
12. [Key Architectural Components](#key-architectural-components)

---

## Persistent Formats Reference

This section documents all persistent data formats and encoding schemes used by materialized views. These formats are critical for understanding how the system tracks data across source, checkpoints, and destination tables.

### Row Address Encoding (`__source_row_id`)


Row addresses are 64-bit integers encoding both fragment ID and row offset within that fragment:

```python
# Encoding (source code reference)
row_id = (fragment_id << 32) | row_offset

# Decoding
fragment_id = row_id >> 32
row_offset = row_id & 0xFFFFFFFF

# Example
row_id = 0x0000000300000005  # Fragment 3, row 5
fragment_id = 0x0000000300000005 >> 32  # = 3
row_offset = 0x0000000300000005 & 0xFFFFFFFF  # = 5
```

**Properties:**
- **Max fragment ID**: 2^32 - 1 (4,294,967,295)
- **Max rows per fragment**: 2^32 - 1 (4,294,967,295)
- **Storage type**: PyArrow `int64`
- **Column name**: `__source_row_id` in destination tables

This encoding allows Geneva to:
1. Quickly extract source fragment IDs from destination tables
2. Determine which destination fragments need reprocessing during incremental refresh
3. Efficiently track the mapping from destination rows back to source rows

**Important: Stable Row IDs Requirement**

For materialized views, the source table must have stable row IDs enabled. This ensures that the row address encoding remains valid even after compaction operations:
- **Without stable row IDs**: Compaction changes physical row addresses, breaking the `__source_row_id` pointers
- **With stable row IDs**: Row addresses remain constant across compaction, maintaining valid pointers
- This is why Geneva requires `new_table_enable_stable_row_ids` when creating source tables for materialized views

### Checkpoint Key Formats


Checkpoint keys identify unique units of work that can be deduplicated and resumed.

#### Fragment Deduplication Key

```python
# Format
prefix = (
    f"udf-{udf_name}_ver-{udf_version}_col-{column}_"
    f"where-{hash(filter)}_uri-{hash(dataset_uri)}_ver-{version}"
)
dedupe_key = f"{prefix}_frag-{frag_id}"

# Example - DESTINATION fragment ID is used!
uri = "/path/to/dest/table.lance"
frag_id = 3  # DESTINATION fragment ID (from task.dest_frag_id())
udf_name = "video_udf"
udf_version = "abc123def456"
column = "embedding"
filter = "x > 10"
version = 42  # dataset version
key = (
    "udf-video_udf_ver-abc123def456_col-embedding_where-80f7..._"
    "uri-d5dd..._ver-42_frag-3"
)
dedupe_key = key  # (no additional hash)
```

**Purpose:** Prevents duplicate processing of the same fragment across workers.

**Critical Note:** The `frag_id` is the **destination fragment ID**, not the source fragment ID. This is crucial for incremental refresh to correctly identify checkpointed work. For materialized views with filters/shuffle, source and destination fragment IDs differ.

**Stored as:** Key in checkpoint store with RecordBatch value containing file path reference.

#### Batch Checkpoint Key

```python
# Format
prefix = (
    f"udf-{udf_name}_ver-{udf_version}_col-{column}_"
    f"where-{hash(filter)}_uri-{hash(dataset_uri)}_ver-{version}"
)
checkpoint_key = f"{prefix}_frag-{frag_id}_range-{start}-{end}"

# Example (batch 0..50 of destination fragment 3)
udf_name = "video_udf"
udf_version = "abc123def456"
column = "embedding"
filter = "x > 10"
dataset_uri = "/path/to/dest/table.lance"
version = 42
frag_id = 3
start = 0
end = 50
checkpoint_key = (
    "udf-video_udf_ver-abc123def456_col-embedding_where-80f7..._"
    "uri-d5dd..._ver-42_frag-3_range-0-50"
)
```

**Purpose:** Tracks completion of individual batches within a fragment for fine-grained resumption.

### Checkpoint File Storage


Checkpoint files are stored as Lance tables containing references to staged data files.

```python
# Storage format (fragment-level checkpoints)
checkpoint_store[dedupe_key] = pa.RecordBatch.from_pydict({
    "file": [new_file.path],  # Path to staged .lance file
    "src_data_files": [json.dumps(sorted(file_paths))],  # Source data file paths
})

# File locations
checkpoint_dir/
  ├── {dedupe_key_1}.lance  # Checkpoint entry
  ├── {dedupe_key_2}.lance
  └── ...

staged_data_dir/
  ├── {fragment_id}_{batch_start}_{batch_end}.lance  # Actual data
  └── ...
```

**Properties:**
- **Format**: PyArrow RecordBatch with columns "file" and optionally "src_data_files"
- **File type**: `.lance` files
- **Naming**: SHA-256 hash of checkpoint key
- **Content**: File path reference to staged data, plus source data file paths for validation
- **Backward compatibility**: Checkpoints without `src_data_files` are invalidated to ensure correctness

### Schema Metadata Keys


Materialized view tables store query metadata in their schema:

```python
# Metadata keys (as UTF-8 encoded bytes)
MATVIEW_META_QUERY = b"geneva::view::query"           # Serialized query JSON
MATVIEW_META_BASE_TABLE = b"geneva::view::base_table"  # Source table name
MATVIEW_META_BASE_DBURI = b"geneva::view::base_table_db_uri"  # Source DB URI
MATVIEW_META_BASE_VERSION = b"geneva::view::base_table_version"  # Source version
MATVIEW_META_VERSION = b"geneva::view::version"        # MV format version ("1" or "2")

# Example metadata
schema.metadata[b"geneva::view::query"] = b'{"filter": "age > 21", ...}'
schema.metadata[b"geneva::view::base_table"] = b"users"
schema.metadata[b"geneva::view::base_table_db_uri"] = b"/path/to/source.lance"
schema.metadata[b"geneva::view::base_table_version"] = b"42"
schema.metadata[b"geneva::view::version"] = b"2"
```

**Properties:**
- **Encoding**: UTF-8 bytes (required for PyArrow schema metadata)
- **Query format**: JSON serialization of GenevaQuery object
- **Version format**: Integer as string bytes
- **MV Version**: Indicates encoding format and source table capabilities
  - `"1"`: Fragment+offset encoding, source without stable row IDs (v0.7.x and v0.8.x+)
  - `"2"`: Stable row IDs enabled, source with stable row IDs (v0.8.x+)
  - Determines refresh behavior: version 1 MVs can only refresh to same source version, version 2 MVs can refresh across versions
- **Persistence**: Stored in Lance table schema, survives table operations

### Internal Column Formats

All materialized view tables include these system columns:

```python
# Column schemas
__source_row_id: int64         # Row address encoding (see above)
__is_set: bool                 # Whether row has been computed

# Initial state after create_materialized_view()
__source_row_id: [1234, 5678, ...]  # Populated with target row IDs
__is_set: [False, False, ...]       # All False (not yet computed)

# After refresh()
__is_set: [True, True, ...]         # All True (computed)
```

### Checkpoint Store Data Model


The checkpoint store maps checkpoint keys to file references:

```python
# Interface
checkpoint_store: Mapping[str, pa.RecordBatch]

# Key: Checkpoint deduplication key (SHA-256 hash)
key: str = hashlib.sha256(...).hexdigest()

# Value: RecordBatch with file path
value: pa.RecordBatch = pa.RecordBatch.from_pydict({
    "file": ["/path/to/staged/data.lance"]
})

# Operations
if key in checkpoint_store:
    # Fragment already processed, skip
    pass
else:
    # Process fragment and store result
    checkpoint_store[key] = result_batch
```

---

## Fragment Mapping: Source to Checkpoint to Destination

### Mapping Example

**Scenario:** Materialized view with filter and shuffle

```
SOURCE TABLE (3 fragments)
Fragment 0: rows 0-99     → _rowaddr: [0, 1, ..., 99]
Fragment 1: rows 100-199  → _rowaddr: [4294967396, ..., 4294967495]
Fragment 2: rows 200-299  → _rowaddr: [8589934792, ..., 8589934891]

QUERY: where("x > 150").shuffle(seed=42)
Matching rows: [151, 152, ..., 199, 200, 201, ..., 299]
After shuffle: [287, 163, 241, ..., 189]

DESTINATION TABLE (created with 2 fragments)
Fragment 0: __source_row_id = [8589935079, 4294967563, 8589935033, ...]
                              = [287, 163, 241, ...]
Fragment 1: __source_row_id = [..., 8589934981]
                              = [..., 189]

REFRESH PROCESS:
CopyTask for dest fragment 0:
  1. Read __source_row_id from dest fragment 0
  2. Take rows [287, 163, 241, ...] from source
     - Row 287 from source fragment 2, offset 87
     - Row 163 from source fragment 1, offset 63
     - Row 241 from source fragment 2, offset 41
  3. Apply UDFs to create computed columns
  4. Write to dest fragment 0 with _rowaddr = [0, 1, 2, ...]
```

**Key observation:** Source fragment boundaries are irrelevant to destination fragments. The mapping is purely based on the logical query result.

---

## Checkpoint Mechanism and Progress Tracking

### Fragment-Level Checkpointing


Each fragment + map task combination gets a unique deduplication key:

```python
def _get_fragment_dedupe_key(uri: str, frag_id: int, map_task: MapTask) -> str:
    key = f"{uri}:{frag_id}:{map_task.checkpoint_key()}"
    return hashlib.sha256(key.encode()).hexdigest()
```

This enables:
- **Deduplication:** Skip processing if fragment already computed
- **Idempotency:** Safe to retry failed fragments
- **Partial completion:** Only process remaining fragments after failure

### Batch-Level Checkpointing


The `CheckpointingApplier` stores each batch with MD5-based key:

```python
class CheckpointingApplier:
    def apply(self, task: ReadTask) -> Iterator[pa.RecordBatch]:
        checkpoint_key = task.checkpoint_key()  # MD5 of task params

        if checkpoint_key in self._checkpoint_store:
            yield self._checkpoint_store[checkpoint_key]
        else:
            for batch in task.to_batches():
                batch_with_schema = self._apply_map(batch)
                self._checkpoint_store[checkpoint_key] = batch_with_schema
                yield batch_with_schema
```

**Checkpoint key includes:**
- URI and version
- Column list
- Fragment ID, offset, limit
- Where clause (if any)

This granularity allows resumption at batch level if pipeline fails.

### Checkpoint Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ CHECKPOINT STORE                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Fragment 0, Batch 0 → RecordBatch (key: sha256(...))       │
│  Fragment 0, Batch 1 → RecordBatch                          │
│  Fragment 1, Batch 0 → RecordBatch                          │
│  ...                                                        │
│                                                             │
│  Data File for Fragment 0 → "/path/to/data-file-0.lance"    │
│  Data File for Fragment 1 → "/path/to/data-file-1.lance"    │
│                                                             │
└────────────┬────────────────────────────┬───────────────────┘
             ↑                            ↓
        Write batches              Read batches
             │                            │
   ┌─────────┴─────────┐        ┌─────────┴──────────┐
   │ CheckpointingAp   │        │ FragmentWriter     │
   │ plier (Ray)       │        │ (Ray)              │
   └───────────────────┘        └────────────────────┘
```

**Cleanup:** Checkpoint store can be cleared after commit succeeds, but is often retained for debugging and potential re-use.

### Source Data Change Detection (Data File Tracking)


When source data is modified via backfill (adding new data files to existing fragments), the checkpoint system must detect this and invalidate stale checkpoints. This is done via **data file path tracking**.

**Problem:** Backfill adds new data files to source fragments without changing the fragment ID:
```
Before backfill: Frag 0 files = [abc123.lance]
After backfill:  Frag 0 files = [abc123.lance, def456.lance]
```

If checkpoint validation only checks if the destination file exists, it would incorrectly skip reprocessing the backfilled data.

**Solution:** Store and validate **source data file paths** - the set of data file paths from the source fragments. When any backfill runs (even re-running a UDF on the same column), new data files with new UUIDs are created, changing the file path set.

#### Why Data File Paths (vs Field IDs)?

We originally considered tracking field IDs (the set of field IDs that have data files). However, field IDs are insufficient for detecting all changes:

| Scenario | Field IDs Change? | Data Files Change? | Detected? |
|----------|------------------|-------------------|-----------|
| Backfill new field | ✓ | ✓ | ✓ Both work |
| UDF re-run same field | ✗ | ✓ | Only data files |

When a UDF is re-run on the same column (e.g., with different logic), the field ID stays the same but a new data file is created. Data file path tracking detects this.

#### Why Union of Data Files?

Checkpoints are keyed by **destination** fragment ID. A single destination fragment can pull rows from **multiple source fragments** (due to filtering, shuffling). We store the **union** of data file paths to detect when ANY source fragment changes:

```
Source Table              Destination Table (MV)
┌──────────────┐            ┌────────────┐
│ Src Frag 0   │──────┐     │ Dst Frag 0 │  ← checkpoint stores union of
│ files=[a.lance]     │     │            │    all data file paths
├──────────────┤      ├────▶│            │
│ Src Frag 1   │──────┤     │            │
│ files=[b.lance]     │     └────────────┘
├──────────────┤      │
│ Src Frag 2   │──────┘
│ files=[c.lance, d.lance]
└──────────────┘

Union = {a.lance, b.lance, c.lance, d.lance}
```

**When any backfill runs:** New data file is created (e.g., `e.lance`), union changes → checkpoint invalidated → reprocess.

#### Filtering to Relevant Columns Only

Data file tracking is further optimized to only include files containing columns that the MV actually reads. This prevents unnecessary MV reprocessing when unrelated columns are backfilled.

**Problem:** Without filtering, adding and backfilling a new column to the source table would invalidate all MV checkpoints, even if the MV doesn't use that column:
```
Source table columns: [id, value]
MV selects: [id, value]

User adds column: extra
User backfills: extra

Without filtering: MV checkpoint invalidated (new data file for extra)
With filtering: MV checkpoint still valid (extra not in MV's relevant columns)
```

**Solution:** Compute the set of field IDs for columns the MV reads from source, then only track data files containing those field IDs:

```python
# In _get_relevant_field_ids():
# Extract field IDs for columns the MV uses
relevant_field_ids = {field_id for col in input_cols
                      for field_id in extract_field_ids(schema, col)}

# In get_source_data_files():
# Only include files containing relevant fields
return frozenset(
    df.path for df in src_frag.data_files()
    if set(df.fields) & relevant_field_ids
)
```

**How it works:**
1. At refresh start, compute `relevant_field_ids` from MV's input columns
2. When collecting data files for checkpoint validation, filter to files containing at least one relevant field
3. Data files for unrelated columns are excluded from tracking
4. Backfilling unrelated columns creates new data files, but they're not tracked → checkpoint stays valid

**Example:**
```
Source fragment files:
  - file_a.lance (fields: [0, 1])  # id, value
  - file_b.lance (fields: [2])     # extra (added later)

MV uses columns: [id, value] → relevant_field_ids = {0, 1}

Tracked files = {file_a.lance}  # file_b.lance excluded (field 2 not relevant)
```

**Benefits:**
- Adding new columns to source doesn't invalidate MV checkpoints
- Backfilling columns not used by MV doesn't trigger reprocessing
- Reduces unnecessary computation when source schema evolves

**Test reference:** See `test_mv_refresh_ignores_unrelated_column_backfill` in `test_runners_ray_matview.py`

#### How It Works

1. **During checkpoint creation** (in `_record_fragment`):
   - Compute union of data file paths from all source fragments that contributed to this destination
   - Store both the destination file path AND the source data file paths in the checkpoint
   - Example checkpoint data:
     ```
     {
       "file": "path/to/dest/data.lance",
       "src_data_files": "[\"a.lance\", \"b.lance\", \"c.lance\"]"
     }
     ```

2. **During checkpoint validation** (in `_validate_checkpoint_data_files`):
   - Read the stored data file paths from the existing checkpoint
   - Compute the current data file paths from the same source fragments
   - Compare the two sets:
     - If they match → checkpoint is valid, skip reprocessing
     - If they differ → checkpoint is invalid, reprocess the destination fragment
   - Log message on mismatch: "Checkpoint data files mismatch"

#### MV Version 2 (Stable Row IDs) Handling

For MV version 2, source fragment IDs cannot be extracted from stable row IDs (the row ID encoding is opaque). In this case, data files are collected from **all source fragments** (conservative but correct):

- **When specific source fragment IDs are available** (MV v1):
  - Compute data file union for only those specific source fragments
  - More precise - only checks fragments that actually contribute to the destination

- **When source fragment IDs are unavailable** (MV v2 with stable row IDs):
  - Compute data file union for ALL source fragments in the table
  - Conservative approach - any data file change anywhere invalidates checkpoints
  - Ensures correctness even without fragment-level tracking

#### Two-Level Checkpoint Invalidation

Source changes are detected at two levels:

1. **Fragment-level checkpoints**: Store `src_data_files` in checkpoint VALUE
   - Detects any backfill (new data files created)
   - Detects UDF re-runs on same column (new data files with new UUIDs)

2. **Batch-level checkpoints**: Include `src.version` in checkpoint KEY
   - Any source version change invalidates batch checkpoints
   - More aggressive but correct (no stale data)

**Important:** `CopyTask.version` property exposes `self.src.version` for batch checkpoint key generation. This ensures batch checkpoints are invalidated when source version changes.

**Note on Compaction:** Compaction is handled separately via stable row IDs. Data file tracking is specifically for detecting backfill changes, not compaction.

#### Backward Compatibility

- Existing checkpoints without `src_data_files` are invalidated to ensure correctness
- This forces a re-process on first refresh after upgrade, but ensures no stale data
- New checkpoints will include `src_data_files` for future validation

---

## Materialized View Refresh Process

**Why this matters:** The refresh process recomputes materialized view results based on the latest (or specified) source data. Understanding how refresh works helps debug issues with stale data, version mismatches, or performance problems.

### Key Concepts

The refresh process reconstructs the original query from metadata stored in the materialized view's schema:
- **Same source table** and version for consistent reads
- **Same filter/shuffle/UDF operations** applied
- **Destination-driven**: Iterates through existing view fragments, not source fragments
- **Checkpointed**: Can resume from failures without reprocessing completed work

### Version Management

**Why it matters:** Controlling source versions enables reproducibility, testing with historical data, and proper incremental refresh.

**Key capabilities:**
- **Automatic**: `view.refresh()` uses latest source version by default
- **Explicit**: `view.refresh(src_version=42)` pins to specific version
- **Cross-database**: Source can be in different database than view
- **Tracked**: Version metadata stored in view schema for audit trail

**Use cases:**
- Testing with historical snapshots
- Rollback scenarios when source data has issues
- Compliance requirements for version tracking

---

## Incremental Refresh with New Source Data


When new data is added to the source table, the materialized view can incrementally process only the new rows without recomputing existing results.

### Append-Only Strategy

The implementation uses a simple **append-only strategy** that avoids race conditions and complex coordination:

**Key Insight:** Use `table.add()` to append new placeholder rows as a NEW fragment instead of using DataReplacement operations that can conflict with concurrent writers.

### Implementation Overview

The incremental refresh process follows these steps:

1. **Build destination-to-source mapping** by reading `__source_row_id` from destination fragments
2. **Check destination fragment checkpoints** (not source fragment checkpoints)
3. **Identify source fragments needing processing** by checking if their data exists in checkpointed destination fragments
4. **Query new fragments** with filters and shuffle applied
5. **Append placeholder rows** using `table.add()` (creates new destination fragment)
6. **Process only affected fragments** using destination-driven `CopyTask`s

**Critical Design Detail:** Checkpoint lookups use **destination fragment IDs**, not source fragment IDs. This is because:
- Checkpoints are keyed by `_get_fragment_dedupe_key(dst_uri, dest_frag_id, map_task)`
- For materialized views with filters/shuffle, source and destination fragment IDs differ
- A source fragment check would always fail, causing full reprocessing on every refresh
- The mapping from source to destination is determined by inspecting `__source_row_id` values

**How `max_rows_per_fragment` affects checkpoints:**

When using `max_rows_per_fragment`, new rows are split across multiple destination fragments, and each gets its own checkpoint:

```
Source fragment 5: 100 new rows
max_rows_per_fragment=30

Creates destination fragments:
  - Fragment 10: rows 0-29   → checkpoint_key = sha256("dst_uri:10:task_key")
  - Fragment 11: rows 30-59  → checkpoint_key = sha256("dst_uri:11:task_key")
  - Fragment 12: rows 60-89  → checkpoint_key = sha256("dst_uri:12:task_key")
  - Fragment 13: rows 90-99  → checkpoint_key = sha256("dst_uri:13:task_key")

Each destination fragment's __source_row_id values point back to source fragment 5.
```

The checkpoint structure is `ckp_store[dest_frag_key] -> {file: path)}`:
1. We cache the computed result (in the destination)
2. Source-to-destination is a many-to-many mapping (with filters/shuffle)
3. The `__source_row_id` column enables reverse lookups when needed


### Complete Example

**Initial state:**
```
Source table: 3 fragments (0, 1, 2) with 300 rows
Query: where("value > 150") → 150 matches

After initial refresh:
  Destination fragment 0: 150 rows
  Checkpoints: Source fragments [0, 1, 2] marked as processed
```

**Add new data:**
```
Source table: Add fragments [3, 4] with 100 rows
Query filter "value > 150" matches: 50 new rows
```

**Incremental refresh execution:**

1. **Build destination-to-source mapping:**
   - Scan existing destination fragment 0 for `__source_row_id`
   - Extract source fragment IDs: `dst_to_src_map[0] = {0, 1, 2}`
   - Check destination fragment 0 checkpoint: **exists** (from initial refresh)

2. **Identify unprocessed sources:**
   - Check which source fragments have checkpointed data in destination
   - Source fragments [0, 1, 2] are in destination fragment 0 which has a checkpoint
   - Source fragments [3, 4] are **not** in any checkpointed destination fragment
   - `source_fragments_without_checkpoint = [3, 4]`

3. **Query with filter:**
   - Apply "value > 150" to source fragments [3, 4]
   - Extract 50 matching row addresses

4. **Append placeholders:**
   - Create new destination fragment(s) with placeholder rows
   - All `__is_set = False`, all data columns NULL
   - With `max_rows_per_fragment`, rows are split across multiple smaller fragments

5. **Update mapping for new fragment:**
   - Destination fragment 1 contains rows from source fragments [3, 4]
   - `fragments_to_process = {1}` (fragment 0 has checkpoint, fragment 1 is new)

6. **Execute CopyTasks:**
   - Skip destination fragment 0 (has checkpoint)
   - Process destination fragment 1 (no checkpoint, contains source [3, 4])
   - `CopyTask` reads `__source_row_id`, fetches from source, applies UDFs
   - Writes results to destination fragment 1

7. **Create checkpoints:**
   - Mark destination fragment 1 as processed
   - Checkpoint key: `_get_fragment_dedupe_key(dst_uri, frag_id=1, map_task)`
   - Now source fragments [3, 4] are checkpointed (via destination fragment 1)

8. **Collect checkpointed fragments for commit:**
   - Retrieve existing data file references for skipped fragments
   - Include in final commit alongside newly processed fragments

**Final state:**
```
Destination table: 2 fragments
  Fragment 0: 150 rows (from checkpoint, not recomputed)
  Fragment 1: 50 rows (newly computed)
Total: 200 rows
```

### Checkpoint Lookup Algorithm

The incremental refresh checkpoint lookup follows this precise algorithm:

```python
# 1. Build mapping from destination fragments to source fragments
dst_to_src_map = {}
dest_fragments_with_checkpoint = set()

for dst_frag in dst_dataset.get_fragments():
    # Check if this DESTINATION fragment has a checkpoint
    checkpoint_exists = _check_fragment_data_file_exists(
        dst_uri, dst_frag.fragment_id, map_task, checkpoint_store
    )

    if checkpoint_exists:
        dest_fragments_with_checkpoint.add(dst_frag.fragment_id)

    # Read __source_row_id to extract source fragment IDs
    scanner = dst_dataset.scanner(
        columns=["__source_row_id"],
        fragments=[dst_frag]
    )
    dst_frag_data = scanner.to_table()
    source_frag_ids = {
        row_id >> 32 for row_id in dst_frag_data["__source_row_id"]
    }
    dst_to_src_map[dst_frag.fragment_id] = source_frag_ids

# 2. Determine which source fragments need processing
for src_frag in src_dataset.get_fragments():
    # Is this source fragment's data in ANY checkpointed destination fragment?
    is_checkpointed = any(
        src_frag.fragment_id in src_frags and
        dst_frag_id in dest_fragments_with_checkpoint
        for dst_frag_id, src_frags in dst_to_src_map.items()
    )

    if not is_checkpointed:
        source_fragments_without_checkpoint.append(src_frag.fragment_id)
```

**Why this works:**
- Correctly handles many-to-one source-to-destination mapping (filters consolidate fragments)
- Uses destination fragment IDs for checkpoint keys (matches how checkpoints are written)
- Efficiently scans destination fragments once using scanner API (not to_table())
- Reuses the mapping to identify which destination fragments need processing

### Why This Design Works

1. **Append-only safety:** `table.add()` avoids race conditions with parallel writes
2. **Destination-driven:** Correct handling of filters/shuffle that consolidate fragments
3. **Fragment immutability:** Source fragments never change once created
4. **Idempotent:** Safe to re-run, skips already-processed fragments
5. **Incremental cost:** Processing proportional to new data only
6. **Correct consolidation:** Multiple source fragments → single destination fragment handled correctly
7. **Correct checkpoint lookups:** Uses destination fragment IDs, matching how checkpoints are written

### Checkpoint Collection for Skipped Fragments

When fragments are skipped (already checkpointed), they must still be included in the final commit to ensure a consistent table version.

**How it works:**
1. Previously checkpointed fragments are identified during planning
2. Their existing data file references are retrieved from the checkpoint store
3. These references are included in the final commit alongside newly processed fragments

**Why this matters:**
- Ensures the materialized view remains consistent after refresh
- Avoids reprocessing data that was already computed
- Allows incremental refreshes to build on previous work

### Fragment Granularity Control (`max_rows_per_fragment`)

The `max_rows_per_fragment` parameter controls how new data is organized into destination fragments during incremental refresh.

**Default behavior:** All new placeholder rows are added as a single fragment.

**With `max_rows_per_fragment`:** New rows are split across multiple smaller fragments.

**Example:** Adding 15 new rows with `max_rows_per_fragment=7` creates 3 fragments (7 + 7 + 1 rows).

**When to use:**
- **Better parallelism:** More fragments allow more Ray workers to process in parallel
- **Finer checkpointing:** Smaller fragments mean less rework if a refresh fails partway through
- **Memory management:** Limit how much data each worker processes at once (useful for memory-intensive UDFs like embeddings)

**Important:** `max_rows_per_fragment` is a **per-refresh parameter**, not a table-level configuration:
- Different values can be used in each `refresh()` call
- Only affects **new** placeholder fragments created during that refresh
- Existing fragments (with or without checkpoints) are untouched
- Results in mixed fragment sizes in the table, which Lance handles normally

**Example of varying values:**
```python
# Initial data: 1000 rows
mv.refresh(max_rows_per_fragment=500)  # Creates fragments A, B (500 rows each)

# New data: 300 rows
mv.refresh(max_rows_per_fragment=100)  # Creates fragments C, D, E (100, 100, 100 rows)

# New data: 50 rows
mv.refresh()  # Creates fragment F (50 rows, default behavior)
```

### Shuffle Behavior During Incremental Refresh

**Important:** Shuffle only applies to NEW data during refresh, preserving original shuffle order for existing data.

**Initial creation:**
```python
# All row IDs are shuffled together
row_ids = query.to_arrow()["_rowid"].to_pylist()
if query.shuffle:
    rng = np.random.default_rng(query.shuffle_seed)
    rng.shuffle(row_ids)
```

**Incremental refresh:**
```python
# Only new row IDs are extracted (with same shuffle seed applied to new data)
new_row_ids = query_new_fragments.to_arrow()["_rowid"].to_pylist()
# Shuffle applied if original query had shuffle
# New data appended, not interleaved with existing data
```

**Result:** Original data maintains its shuffle order, new data added with consistent shuffle semantics.

### Test Reference

See `src/tests/test_runners_ray_matview.py` for complete working examples:

- **Basic incremental refresh**: Adding new source data and refreshing
- **Checkpoint reuse**: Multiple refresh cycles demonstrating skipped fragment handling
- **Chained views**: Incremental refresh through materialized views built on other materialized views
- **Fragment granularity**: Using `max_rows_per_fragment` to control destination fragment sizes
- **Backfill detection via data files**: `test_materialized_view_refresh_detects_backfill_via_field_coverage` - detects when source is backfilled with new columns
- **UDF re-run detection**: `test_materialized_view_refresh_detects_udf_rerun_same_field` - detects when UDF is re-run on same column with different logic

---

## Query Operations Impact on Fragments and Layouts

**Why this matters:** Understanding how query operations affect the materialized view structure helps debug performance issues, understand storage costs, and design efficient queries.

### Filter (`where()`)

**Impact:**
- **Row count:** Reduced based on filter selectivity
- **Fragment structure:** Unchanged (same number of fragments as source)
- **Physical layout:** Sparse (filtered rows represented as NULLs)

**Example:**
```
Source fragment 0: 1000 rows
Filter "age > 21": 300 matches

Destination fragment 0:
  Physical rows: 1000
  Logical rows: 300 (rows 0-699 are NULL)
```

**Key point:** Physical layout preserves fragment boundaries for efficient mapping.

### Shuffle

**Impact:**
- **Row order:** Randomized based on seed
- **Fragment structure:** Unchanged
- **Physical layout:** Same density, different order

**Reproducibility:** Same seed always produces same shuffle order. Critical for ML training data consistency.

**Use cases:**
- Randomize data for ML training
- Break locality for better load balancing
- Create different views of same filtered data

### Limit

**Impact:**
- **Row count:** Exactly `limit` rows (or fewer if source has fewer)
- **Fragment structure:** May have fewer fragments than source
- **Physical layout:** Dense (all rows present)

**Example:** `table.limit(100)` with batch_size=1024 creates 1 destination fragment.

### Offset

**Impact:**
- **Row selection:** Skip first N rows
- **Fragment structure:** Unchanged from base query
- **Physical layout:** Same as base query (offset not stored)

**Use case:** Pagination combined with limit: `table.offset(50).limit(100)` returns rows 50-149.

### UDF Columns

**Impact:**
- **Schema:** Additional computed columns
- **Fragment structure:** Unchanged
- **Physical layout:** Same as base query

**Performance note:** UDFs are **not** applied during view creation, only during refresh. This enables fast initialization with lazy computation.

**Use cases:**
- Add embeddings (expensive GPU operations)
- Add predictions from ML models
- Add derived features for analysis

### Column Selection

**Impact:**
- **Schema:** Subset of source columns
- **Fragment structure:** Unchanged
- **Physical layout:** Smaller data files (fewer columns written)

**Use case:** Reduce storage costs by excluding unused columns from materialized view.

---


**Note:** Fragment writer and commit/versioning details are in `fragment_writers.md` (shared with backfill operations).

---

## Key Architectural Components

### Task Hierarchy


```
ReadTask (abstract base)
├── ScanTask
│   - Read from source table with fragment ID
│   - Uses Lance scanner with offset/limit
│   - Supports where clause filtering
│   - Returns batches with _rowaddr column
│
└── CopyTask
    - Read from source using __source_row_id
    - Maps to specific destination fragment
    - Uses Lance take() for random access
    - Encodes _rowaddr for destination

MapTask (abstract base)
├── BackfillUDFTask
│   - Applies single UDF to batches
│   - Used for adding columns to existing tables
│   - Handles BACKFILL_SELECTED filtering
│
└── CopyTableTask
    - Applies multiple UDFs from query
    - Used for materialized view refresh
    - Supports column exclusion
    - Handles null values for filtered rows
```

### Pipeline Components


```
ColumnAddPipelineJob
├── ActorPool[CheckpointingApplier]
│   - Ray remote actors
│   - Apply map tasks to read tasks
│   - Store results in checkpoint store
│   - Return checkpoint keys
│
├── FragmentWriterManager
│   ├── FragmentWriterSession (per fragment)
│   │   ├── Ray.remote(FragmentWriter)
│   │   │   - Buffer and sort batches
│   │   │   - Align to physical layout
│   │   │   - Filter columns
│   │   │   - Write Lance file
│   │   │
│   │   ├── Checkpoint queue
│   │   └── Inflight futures (max 3)
│   │
│   └── Commit coordinator
│       - Track completed fragments
│       - Batch commits every N fragments
│       - Handle version conflicts
│
└── JobTracker
    - Progress tracking
    - Fragment completion metrics
    - Task counts
```

### Data Flow Diagram

```
┌──────────────────────┐
│   SOURCE TABLE       │
│   (Lance)            │
└──────────┬───────────┘
           │
           │ CopyTask reads __source_row_id
           │ from destination, takes rows
           │ from source
           ↓
┌──────────────────────┐
│ CheckpointingApplier │  Apply UDFs
│ (Ray)                │ ───────────→ CopyTableTask
└──────────┬───────────┘
           │
           │ Store batches with
           │ checkpoint key
           ↓
┌──────────────────────┐
│ CHECKPOINT STORE     │
│ (Lance)              │
└──────────┬───────────┘
           │
           │ Retrieve batches
           │ for fragment
           ↓
┌──────────────────────┐
│ FragmentWriter       │  1. Buffer & sort
│ (Ray)                │  2. Align to physical layout
│                      │  3. Filter columns
│                      │  4. Write Lance file
└──────────┬───────────┘
           │
           │ Return (frag_id, DataFile, rows)
           ↓
┌──────────────────────┐
│ FragmentWriter       │  Record completion
│ Manager              │  Batch commits
└──────────┬───────────┘
           │
           │ lance.LanceOperation.DataReplacement
           ↓
┌──────────────────────┐
│ DESTINATION TABLE    │
│ (Lance)              │
│ - Updated fragments  │
│ - New version        │
└──────────────────────┘
```

### Query Metadata Storage


Metadata keys stored in Lance schema.metadata:

```python
MATVIEW_META = "geneva::view::"
MATVIEW_META_QUERY = f"{MATVIEW_META}query"           # Serialized GenevaQuery JSON
MATVIEW_META_BASE_TABLE = f"{MATVIEW_META}base_table" # Source table name
MATVIEW_META_BASE_DBURI = f"{MATVIEW_META}base_table_db_uri"  # Source DB URI
MATVIEW_META_BASE_VERSION = f"{MATVIEW_META}base_table_version"  # Source version
```

**Example:**
```python
schema = lance.dataset(view_uri).schema
metadata = schema.metadata

query_json = metadata[b"geneva::view::query"]
# {
#   "table": "users",
#   "columns": ["name", "age"],
#   "where": "age > 21",
#   "shuffle": true,
#   "shuffle_seed": 42,
#   "column_udfs": [...]
# }
```

This metadata enables:
- **Refresh without query object:** Reconstruct from metadata
- **Schema evolution:** Detect source table changes
- **Audit trail:** Know exact query that created view

---

## Summary

Geneva materialized views provide a robust, distributed system for precomputing query results:

### Key Innovations

1. **Explicit row mapping:** `__source_row_id` enables precise source-to-destination mapping
2. **Checkpoint-based recovery:** Granular deduplication at fragment and batch level
3. **Physical layout alignment:** Sparse logical views represented as dense physical fragments
4. **Incremental commits:** Atomic multi-fragment updates with conflict detection
5. **Lazy computation:** Fast initialization with deferred UDF execution

### Performance Characteristics

- **Creation:** O(n) scan to extract row IDs, minimal compute
- **Refresh:** O(n) for full refresh, parallelized across Ray actors
- **Partial refresh:** O(k) where k = changed rows (if using where-as-bool-column)
- **Storage:** O(n) physical rows (includes NULLs for filtered data)

### Future Enhancements

- **Rank/window functions:** Not yet implemented - Would require sorted/partitioned fragments

---
