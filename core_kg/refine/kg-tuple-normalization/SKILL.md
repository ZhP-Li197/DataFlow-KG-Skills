---
name: kg-tuple-normalization
description: >-
  Reference documentation for the KGTupleNormalization operator. LLM-canonicalizes
  synonymous relations/attributes and de-duplicates triples in-place.
  Use when: after KGTripleExtraction or KGRelationTripleInference produces raw
  triples that may contain synonyms or directional inconsistencies.

trigger_keywords:
  - KGTupleNormalization
  - kg-tuple-normalization
  - triple normalization
  - synonym canonicalization

version: 1.0.0
---

# KGTupleNormalization Operator Reference

LLM-based canonicalization for triple or tuple lists. Synonymous relations are merged (e.g. `is_married_to` ↔ `was_married_to`), directions are unified, and duplicates are dropped.

## 1. Import

```python
from dataflow.operators.general_kg import KGTupleNormalization
```

## 2. Constructor

```python
KGTupleNormalization(
    llm_serving,                # required
    seed=0,
    lang="en",
    attribute_prompt=None,      # defaults to KGAttributeNormalizationPrompt(lang)
    relation_prompt=None,       # defaults to KGRelationNormalizationPrompt(lang)
    num_q=5,                    # reserved, unused
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |
| `attribute_prompt` | No | `None` | Custom attribute-triple normalization prompt |
| `relation_prompt` | No | `None` | Custom relation-triple normalization prompt |
| `num_q` | No | `5` | Reserved, unused |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="normalized_triple",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | `None` | Step storage |
| `input_key` | No | `"triple"` | Source triple/tuple list column |
| `output_key` | No | `"normalized_triple"` | Output column |

## 4. Actual Execution Logic

1. Read DataFrame from `storage`; verify `input_key` exists and `output_key` does not
2. Inspect the **first triple of the first row** to detect whether the list is `<rel>`-style (relation) or `<attribute>`-style (attribute); raises `ValueError` if neither
3. Pick the corresponding prompt (relation or attribute)
4. For each row, call `llm_serving.generate_from_input(...)` with the row's triple list
5. Parse the LLM response (strip ```` ```json ```` fences, JSON-load) and extract the `"normalized_triple"` field
6. Write the resulting normalized list (or string) into `dataframe[output_key]`

## 5. Important Rules

1. `input_key` must exist and `output_key` must not
2. Mixed list types per row (some relation, some attribute) are not supported — the operator picks one prompt based on the first triple
3. LLM parse failures result in an empty string `""` (not an empty list) for that row
4. The operator does NOT expand rows; row count is preserved

## 6. Typical Usage

```python
self.normalizer = KGTupleNormalization(
    llm_serving=self.llm_serving,
    lang="en",
)

self.normalizer.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="normalized_triple",
)
```

## 7. Return Value

```python
return [output_key]
```
