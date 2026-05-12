---
name: mmkg-entity-based-subgraph-sampling
description: >-
  Reference for MMKGEntityBasedSubgraphSampling. Multimodal variant of subgraph
  sampling: emits subgraph + filtered vis_triple + matching vis_url per starting entity.
  Use when: producing aligned (text, visual triples, image URLs) bundles for
  multimodal QA generation.

trigger_keywords:
  - MMKGEntityBasedSubgraphSampling
  - mmkg-entity-based-subgraph-sampling
  - multimodal subgraph sampling
  - vis_url propagation

version: 1.0.0
---

# MMKGEntityBasedSubgraphSampling Operator Reference

Multimodal subgraph sampler. Reads `triple`, `vis_triple`, and `img_dict`, then emits one row per starting entity that bundles:

- a textual `subgraph`
- a filtered `vis_triple` covering only the entities in that subgraph
- a `vis_url` list aligned with that filtered `vis_triple` (deduplicated by first-appearance order)

## 1. Import

```python
from dataflow.operators.multi_model_kg import MMKGEntityBasedSubgraphSampling
```

## 2. Constructor

```python
MMKGEntityBasedSubgraphSampling(
    llm_serving,                # accepted but unused
    seed=0,
    lang="en",                  # accepted but unused
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
    vis_triple_key="vis_triple",
    sampling_type="hop",        # "bfs" | "hop"  (no "rw" support here)
    start_entity=None,
    M=5,
    hop=2,
)
# returns: [output_key, vis_triple_key, "vis_url"]
```

## 4. Actual Execution Logic

1. Read the DataFrame and pull `triple`, `vis_triple`, `img_dict` (the latter two have hard-coded names by convention)
2. Choose starting entities (all if `start_entity=None`)
3. For each starting entity:
   - sample a `subgraph` via BFS or k-hop
   - filter `vis_triple` to keep only visual triples whose subject is in the sampled subgraph
   - extract `vis_url` from `img_dict` for each img_id mentioned by the filtered visual triples, deduplicated by first appearance
4. Emit one output row per starting entity carrying the three aligned values

## 5. Important Rules

1. `sampling_type` ∈ {`"bfs"`, `"hop"`} — `"rw"` is NOT supported in the multimodal variant
2. **Row-expanding**: output row count = number of starting entities; passthrough columns NOT preserved
3. `img_dict` column name is hard-coded; `vis_triple` column is configurable via `vis_triple_key` but the default name should match `MMKGVisualTripleExtraction`'s output
4. The output `vis_url` is aligned with the **filtered** `vis_triple` after first-appearance dedup; the alignment is what downstream `MMKGSubgraphBaseQAGeneration` relies on
5. Subject parsing of visual triples uses regex `r"<subj>\s*(.+?)\s*(?=<obj>)"` — visual triples produced by `MMKGVisualTripleExtraction` follow this format

## 6. Typical Usage

```python
self.mm_subgraph_sampler = MMKGEntityBasedSubgraphSampling(
    llm_serving=self.llm_serving,
    lang="en",
)

self.mm_subgraph_sampler.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="subgraph",
    vis_triple_key="vis_triple",
    sampling_type="hop",
    hop=2,
)
```

## 7. Return Value

```python
return [output_key, vis_triple_key, "vis_url"]
```
