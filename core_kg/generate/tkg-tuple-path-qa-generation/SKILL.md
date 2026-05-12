---
name: tkg-tuple-path-qa-generation
description: >-
  Reference for TKGTuplePathQAGeneration. LLM-generates time-aware QA pairs
  over temporal tuples (hop=1) or sampled temporal paths (hop>1).
  Use when: building time-anchored QA datasets — when did X happen, ordering,
  intervals, etc.

trigger_keywords:
  - TKGTuplePathQAGeneration
  - tkg-tuple-path-qa-generation
  - temporal QA
  - time-order QA
  - time-interval QA

version: 1.0.0
---

# TKGTuplePathQAGeneration Operator Reference

Time-aware QA generator with four prompt flavors covering point-in-time, ordering, and interval questions.

## 1. Import

```python
from dataflow.operators.temporal_kg import TKGTuplePathQAGeneration
```

## 2. Constructor

```python
TKGTuplePathQAGeneration(
    llm_serving,                # required
    seed=0,
    lang="en",
    hop=2,                      # hop number, used to build input/output column names
    qa_type="time_point",       # "time_point" | "event_order" | "time_order" | "time_interval"
    num_q=5,                    # reserved, unused
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |
| `hop` | No | `2` | Number of edges in the path; used as both the input and output column prefix |
| `qa_type` | No | `"time_point"` | Selects one of 4 time-aware prompts; invalid values raise `ValueError` |
| `num_q` | No | `5` | Reserved, unused |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key_meta="QA_pairs",
)
# returns: [<actual_output_column>]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | `None` | Step storage |
| `input_key_meta` | No | `"hop_paths"` | Input column **suffix**; actual column is `"{hop}_{input_key_meta}"`, e.g. `"2_hop_paths"` |
| `output_key_meta` | No | `"QA_pairs"` | Output column **suffix**; actual column is `"{hop}_{output_key_meta}"`, e.g. `"2_QA_pairs"` |

## 4. Actual Execution Logic

1. Resolve `input_key`:
   - `hop=1` → reads literal `"tuple"`, ignores `input_key_meta`
   - `hop>1` → reads `"{hop}_{input_key_meta}"`
2. For each row, call the LLM with the selected `qa_type` prompt
3. Parse the response, extract `"QA_pairs"`
4. Output column is `"{hop}_{output_key_meta}"`

## 5. Important Rules

1. `qa_type` must be one of the four supported values, else `ValueError`
2. Output column name carries the `{hop}_` prefix — you cannot pin it to a flat name like `QA_pairs`
3. When `hop=1`, input is the literal `"tuple"` column; `input_key_meta` has no effect
4. Row count is preserved; empty QA lists are kept as-is

## 6. Typical Usage

```python
self.path_qa_generator = TKGTuplePathQAGeneration(
    llm_serving=self.llm_serving,
    hop=2,
    qa_type="time_order",
    lang="en",
)

self.path_qa_generator.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key_meta="QA_pairs",
)
# Writes "2_QA_pairs"
```

## 7. Return Value

```python
return [<actual_output_column>]
```
