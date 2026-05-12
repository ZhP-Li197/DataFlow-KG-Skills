---
name: kg-relation-tuple-path-generator
description: >-
  Reference for KGRelationTuplePathGenerator. Enumerates k-hop undirected paths
  from any triple-format column. Pure-graph, no LLM. Row-expanding.
  Use when: feeding a path-based QA generator (general / temporal / hyper-relation).

trigger_keywords:
  - KGRelationTuplePathGenerator
  - kg-relation-tuple-path-generator
  - path sampling
  - path enumeration
  - k-hop paths

version: 1.0.0
---

# KGRelationTuplePathGenerator Operator Reference

Pure-graph path enumerator. Parses any column whose values are triple-format strings (`<subj> X <obj> Y <rel> Z` or with extra fields like time, attribute), builds an undirected graph, and writes all distinct k-edge paths.

## 1. Import

```python
from dataflow.operators.general_kg import KGRelationTuplePathGenerator
```

## 2. Constructor

```python
KGRelationTuplePathGenerator(
    seed=0,
    lang="en",                  # accepted but unused
    k=2,                        # path length (k edges)
    max_paths_per_group=100,    # cap per input row
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `seed` | No | `0` | Random seed for path ordering |
| `lang` | No | `"en"` | Accepted but unused |
| `k` | No | `2` | Path length in edges; output column name uses this value as prefix |
| `max_paths_per_group` | No | `100` | Hard cap on paths emitted per input row |

**Note**: this operator does NOT take `llm_serving`.

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key_meta="hop_paths",
)
# returns: [<actual_output_column>]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | None | Step storage |
| `input_key` | No | `"triple"` | Source triple list column (pass `"tuple"` for temporal/hyper-relation) |
| `output_key_meta` | No | `"hop_paths"` | Output column **suffix**; actual column name is `"{k}_{output_key_meta}"`, e.g. `"2_hop_paths"` |

## 4. Actual Execution Logic

1. For each input row, parse triples into `(subject, object, relation_payload)` tuples
2. Build an undirected graph (each triple → one edge between `subject` and `object`)
3. DFS-enumerate distinct paths of length `k`
4. Canonicalize paths via edge-set comparison so reversed or reordered duplicates are dropped
5. Emit ONE OUTPUT ROW per path, serialized as `"triple1 || triple2 || ..."` joined by `" || "`
6. Cap each input group at `max_paths_per_group` paths

## 5. Important Rules

1. Output column is `"{k}_{output_key_meta}"` — cannot be a flat custom name; downstream path-QA operators read this format via their `hop` parameter
2. **Row-expanding**: total output rows = sum of paths per input row. Passthrough columns from upstream are NOT preserved
3. The operator handles `triple` (general KG), `tuple` (temporal 4-tuple, hyper-tuple) format alike — pass `input_key` accordingly
4. Triples that fail to parse are silently skipped during graph construction
5. Path deduplication is by edge set, so two paths with the same edges in different traversal orders are merged

## 6. Typical Usage

```python
self.path_sampler = KGRelationTuplePathGenerator(
    k=2,
    max_paths_per_group=100,
)

# General KG
self.path_sampler.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key_meta="hop_paths",
)
# Produces a "2_hop_paths" column.

# Temporal or hyper-relation KG
self.path_sampler.run(
    storage=self.storage.step(),
    input_key="tuple",
    output_key_meta="hop_paths",
)
```

## 7. Return Value

```python
return [<actual_output_column>]
```
