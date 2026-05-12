---
name: kg-triple-extraction
description: >-
  Reference documentation for the KGTripleExtraction operator. Extracts
  relation or attribute triples from text given a candidate entity list.
  Use when: after KGEntityExtraction has produced the entity column and the
  pipeline needs structured triples.

trigger_keywords:
  - KGTripleExtraction
  - kg-triple-extraction
  - triple extraction
  - relation triple
  - attribute triple

version: 1.0.0
---

# KGTripleExtraction Operator Reference

Extracts entity–relation–object (or entity–attribute–value) triples from raw text using an LLM constrained by a pre-extracted entity list.

## 1. Import

```python
from dataflow.operators.general_kg import KGTripleExtraction
```

## 2. Constructor

```python
KGTripleExtraction(
    llm_serving,                # required
    seed=0,
    triple_type="attribute",    # "relation" or "attribute"
    lang="en",
    num_q=5,                    # reserved, unused
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `triple_type` | No | `"attribute"` | `"relation"` selects `KGRelationTripleExtractionPrompt`; `"attribute"` selects `KGAttributeTripleExtractionPrompt` |
| `lang` | No | `"en"` | Prompt language |
| `num_q` | No | `5` | Reserved, currently unused |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    input_key_meta="entity",
    output_key="triple",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | `None` | Step storage |
| `input_key` | No | `"raw_chunk"` | Source text column |
| `input_key_meta` | No | `"entity"` | Entity list column (typically from `KGEntityExtraction`) |
| `output_key` | No | `"triple"` | Output triple list column |

## 4. Actual Execution Logic

1. Read DataFrame from `storage`; verify `input_key` and `input_key_meta` exist and `output_key` does not
2. For each row, build a prompt with the text + the entity list and call `llm_serving.generate_from_input(...)`
3. Parse the LLM JSON response, extracting the `"triple"` field
4. Each row's `output_key` becomes a `List[str]` of triples like `"<subj> X <obj> Y <rel> Z"`

## 5. Important Rules

1. `input_key` and `input_key_meta` must both exist; `output_key` must not
2. The `entity` column is expected to be a list-like or a comma-separated string; the operator does not auto-parse arbitrary types
3. Rows whose LLM response cannot be parsed receive an empty list `[]`; no exception is raised
4. The row count is preserved — this operator does NOT expand rows; each row's `triple` is a list value

## 6. Typical Usage

```python
self.triple_extractor = KGTripleExtraction(
    llm_serving=self.llm_serving,
    triple_type="relation",
    lang="en",
)

self.triple_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    input_key_meta="entity",
    output_key="triple",
)
```

## 7. Return Value

```python
return [output_key]
```
