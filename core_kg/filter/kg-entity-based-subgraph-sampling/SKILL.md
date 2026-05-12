---
name: kg-entity-based-subgraph-sampling
description: >-
  Reference for KGEntityBasedSubgraphSampling. Samples a textual subgraph
  around each entity using BFS, k-hop neighborhood, or random walk. Row-expanding.
  Use when: a downstream QA generator needs local KG context per entity.

trigger_keywords:
  - KGEntityBasedSubgraphSampling
  - kg-entity-based-subgraph-sampling
  - subgraph sampling
  - BFS sampling
  - random walk

version: 1.0.0
---

# KGEntityBasedSubgraphSampling Operator Reference

Pure-graph subgraph sampler — no LLM call. Reads a triple list and emits one row per starting entity, each row containing the sampled subgraph.

## 1. Import

```python
from dataflow.operators.general_kg import KGEntityBasedSubgraphSampling
```

## 2. Constructor

```python
KGEntityBasedSubgraphSampling(
    llm_serving,                # accepted but never used
    seed=0,
    lang="en",                  # accepted but never used
    num_q=5,                    # reserved, unused
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes (by signature) | None | Accepted for interface compatibility; not invoked |
| `seed` | No | `0` | Random seed for random-walk and tiebreakers |
| `lang` | No | `"en"` | Accepted but unused |
| `num_q` | No | `5` | Reserved, unused |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="subgraph",
    sampling_type="hop",        # "bfs" | "hop" | "rw"
    start_entity=None,          # None → all entities
    M=5,                        # BFS triple cap
    hop=2,                      # k-hop radius
    num_walks=5,                # RW: walks per entity
    walk_length=3,              # RW: edges per walk
)
# returns: [output_key]
```

## 4. Actual Execution Logic

1. Read DataFrame; pull `input_key` column (a list of triples per row)
2. Collect all entities; choose `start_entity` (or use all entities if `None`)
3. For each starting entity, run the requested sampler:
   - `"bfs"` — breadth-first traversal, up to `M` triples
   - `"hop"` — collect all triples within `hop` edges
   - `"rw"` — `num_walks` random walks of length `walk_length`
4. Emit ONE OUTPUT ROW per entity, with the sampled subgraph (triples reformatted to `"<subj> {h} <obj> {t} <rel> {r}"`)

## 5. Important Rules

1. `sampling_type` must be `"bfs"` / `"hop"` / `"rw"`; otherwise raises `ValueError`
2. The operator is **row-expanding**: output row count = number of starting entities, NOT the input row count. Passthrough columns from upstream are NOT preserved
3. Triples that fail to match `"<subj> ... <obj> ... <rel> ..."` raise `ValueError` during parsing
4. Both `triple` and the `tuple` 4-tuple/hyper-tuple format are accepted, since the parser is permissive about extra `<...>` markers between `<obj>` and the next known marker

## 6. Typical Usage

```python
self.subgraph_sampler = KGEntityBasedSubgraphSampling(
    llm_serving=self.llm_serving,
    lang="en",
)

self.subgraph_sampler.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="subgraph",
    sampling_type="hop",
    hop=2,
)
```

## 7. Return Value

```python
return [output_key]
```
