---
name: kg-relation-triple-inference
description: >-
  Reference for KGRelationTripleInference. Uses an LLM to infer implicit
  relation triples from an existing triple list and (optionally) the source
  text; can merge results back into the input column.
  Use when: extending the knowledge graph closure beyond what was directly
  stated in the text.

trigger_keywords:
  - KGRelationTripleInference
  - kg-relation-triple-inference
  - triple inference
  - KG closure

version: 1.0.0
---

# KGRelationTripleInference Operator Reference

LLM-based KG closure inference. Reads existing triples (optionally with source text) and emits implied triples that were not directly extracted.

## 1. Import

```python
from dataflow.operators.general_kg import KGRelationTripleInference
```

## 2. Constructor

```python
KGRelationTripleInference(
    llm_serving,                # required
    seed=0,
    lang="en",
    with_text=False,            # also read raw_chunk if True
    merge_to_input=False,       # dedupe-merge inferred back into "triple"
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |
| `with_text` | No | `False` | If `True`, also reads `raw_chunk` and uses `KGRelationGenerationPrompt`; otherwise uses `KGInferredTripleGenerationPrompt` |
| `merge_to_input` | No | `False` | If `True`, deduplicated inferred triples are appended back into the `triple` column |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="inferred_triple",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | `None` | Step storage |
| `input_key` | No | `"triple"` | Source triple list column |
| `output_key` | No | `"inferred_triple"` | Output column for inferred triples |

## 4. Actual Execution Logic

1. Read DataFrame; verify `input_key` exists and `output_key` does not
2. If `with_text=True`, also require `raw_chunk` in the DataFrame
3. For each row, call `llm_serving.generate_from_input(...)` with the triple list (and text if `with_text`)
4. Parse the LLM response JSON; extract the `"inferred_triple"` field
5. If `merge_to_input=True`, dedupe-append inferred triples back into the row's `triple` column (overwrites in place)
6. Write inferred triples to `dataframe[output_key]`

## 5. Important Rules

1. `input_key` must exist; `output_key` must not
2. `with_text=True` makes `raw_chunk` mandatory — will raise `KeyError` if missing
3. `merge_to_input=True` **mutates the original `triple` column** (in-place overwrite); pass `False` if you want non-destructive output
4. LLM parse failure → empty list for that row

## 6. Typical Usage

```python
# Non-destructive variant
self.inferrer = KGRelationTripleInference(
    llm_serving=self.llm_serving, lang="en",
)
self.inferrer.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="inferred_triple",
)

# Merge-back variant
self.closure = KGRelationTripleInference(
    llm_serving=self.llm_serving, lang="en",
    with_text=True, merge_to_input=True,
)
self.closure.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="inferred_triple",
)
```

## 7. Return Value

```python
return [output_key]
```
