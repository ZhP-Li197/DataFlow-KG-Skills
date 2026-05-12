---
name: tkg-tuple-extraction
description: >-
  Reference for TKGTupleExtraction. Extracts time-anchored 4-tuples (relation
  or attribute flavors) from text.
  Use when: the input text carries explicit timestamps / dates / time spans
  and the pipeline needs a temporal KG.

trigger_keywords:
  - TKGTupleExtraction
  - tkg-tuple-extraction
  - temporal KG
  - 4-tuple extraction
  - time-anchored

version: 1.0.0
---

# TKGTupleExtraction Operator Reference

Temporal KG extractor. Reads raw text and emits time-anchored 4-tuples — either relation-flavored (`subject → relation → object @ time`) or attribute-flavored (`subject → attribute → value @ time`).

## 1. Import

```python
from dataflow.operators.temporal_kg import TKGTupleExtraction
```

## 2. Constructor

```python
TKGTupleExtraction(
    llm_serving,                # required
    triple_type="attribute",    # "relation" | "attribute"
    seed=0,
    lang="en",
    num_q=5,                    # reserved, unused
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `triple_type` | No | `"attribute"` | `"relation"` → time-anchored relations; `"attribute"` → time-anchored attributes |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |
| `num_q` | No | `5` | Reserved, unused |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="tuple",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | `None` | Step storage |
| `input_key` | No | `"raw_chunk"` | Source text column |
| `output_key` | No | `"tuple"` | Output 4-tuple list column |

## 4. Actual Execution Logic

1. Read DataFrame; verify `input_key` exists and `output_key` does not
2. Preprocess text using the same gates as `KGEntityExtraction` (length 10-200000, ≥2 sentence terminators, ≤30% special chars)
3. For each row, call `llm_serving.generate_from_input(...)`
4. Parse JSON response, extract the `"tuple"` field
5. Write a `List` of 4-tuples per row

## 5. Important Rules

1. `input_key` must exist; `output_key` must not
2. Output column is `tuple`, NOT `triple`. Downstream operators (e.g. `KGRelationTuplePathGenerator`) must be configured with `input_key="tuple"`
3. Row count is preserved; each row's tuple list is forwarded as a value
4. LLM parse failures produce empty list `[]`

## 6. Typical Usage

```python
self.tuple_extractor = TKGTupleExtraction(
    llm_serving=self.llm_serving,
    triple_type="relation",
    lang="en",
)

self.tuple_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="tuple",
)
```

## 7. Return Value

```python
return [output_key]
```
