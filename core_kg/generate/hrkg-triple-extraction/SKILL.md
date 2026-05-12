---
name: hrkg-triple-extraction
description: >-
  Reference for HRKGTripleExtraction. Extracts hyper-relation tuples carrying
  multiple qualifier/attribute slots per fact.
  Use when: text contains multi-argument facts where a single (subject, relation,
  object) is insufficient.

trigger_keywords:
  - HRKGTripleExtraction
  - hrkg-triple-extraction
  - hyper-relation
  - n-ary KG
  - hyper-tuple

version: 1.0.0
---

# HRKGTripleExtraction Operator Reference

Hyper-relation KG extractor. Reads raw text and emits tuples that may carry attribute / qualifier slots beyond the basic (subject, relation, object), e.g. "Obama served as President from 2009 to 2017".

## 1. Import

```python
from dataflow.operators.hyper_relation_kg import HRKGTripleExtraction
```

## 2. Constructor

```python
HRKGTripleExtraction(
    llm_serving,                # required
    seed=0,
    lang="en",
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |

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
| `output_key` | No | `"tuple"` | Output hyper-tuple list column |

## 4. Actual Execution Logic

1. Read DataFrame; verify `input_key` exists and `output_key` does not
2. Apply the same text-quality gates as `KGEntityExtraction` (length, sentence count, special-char ratio)
3. For each row, call `llm_serving.generate_from_input(...)` with `HRKGHyperRelationExtractorPrompt`
4. Parse the JSON response, extract the `"tuple"` field
5. Each row's `tuple` becomes a list of hyper-tuple objects (the exact JSON shape is LLM-determined; the operator preserves it as-is)

## 5. Important Rules

1. Output column is named `tuple`, NOT `triple` — downstream operators must read from `tuple`
2. The operator does not normalize the hyper-tuple JSON schema; downstream code should be lenient about extra `<attribute>` / `<qualifier>` markers
3. Row count is preserved; LLM parse failures produce empty list `[]`

## 6. Typical Usage

```python
self.hrkg_extractor = HRKGTripleExtraction(
    llm_serving=self.llm_serving,
    lang="en",
)

self.hrkg_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="tuple",
)
```

## 7. Return Value

```python
return [output_key]
```
