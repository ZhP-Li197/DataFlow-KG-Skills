---
name: hrkg-relation-triple-path-qa-generation
description: >-
  Reference for HRKGRelationTriplePathQAGeneration. LLM-generates QA pairs over
  hyper-tuples (hop=1) or sampled hyper-relation paths (hop=2).
  Use when: producing QA datasets that exercise multi-argument facts.

trigger_keywords:
  - HRKGRelationTriplePathQAGeneration
  - hrkg-relation-triple-path-qa-generation
  - hyper-relation QA
  - n-ary QA

version: 1.0.0
---

# HRKGRelationTriplePathQAGeneration Operator Reference

QA generator that consumes hyper-tuples or sampled 2-hop paths and emits question-answer pairs. Includes a built-in quality gate (rows with `len(QA_pairs) < 2` are reset to `[]`).

## 1. Import

```python
from dataflow.operators.hyper_relation_kg import HRKGRelationTriplePathQAGeneration
```

## 2. Constructor

```python
HRKGRelationTriplePathQAGeneration(
    llm_serving,                # required
    seed=0,
    lang="en",
    hop=1,                      # 1 or 2 ONLY
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |
| `hop` | No | `1` | Must be `1` or `2`; any other value raises `ValueError` |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key="QA_pairs",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | None | Step storage |
| `input_key_meta` | No | `"hop_paths"` | Used only when `hop>1`; input column resolved as `"{hop}_{input_key_meta}"` |
| `output_key` | No | `"QA_pairs"` | Output column (flat name, not `{hop}_` prefixed) |

## 4. Actual Execution Logic

1. Resolve `input_key`:
   - `hop=1` → reads literal `"tuple"` column, ignores `input_key_meta`
   - `hop=2` → reads `"{hop}_{input_key_meta}"` (e.g. `"2_hop_paths"`)
2. Convert each row's input to a string (list values are `"\n".join`-ed)
3. Call the LLM with `HRKGOneHopQAPathGenerationPrompt` or `HRKGTwoHopPathQAGenerationPrompt`
4. Parse the JSON response and extract `QA_pairs`
5. If `len(QA_pairs) < 2`, reset the row to `[]` (quality gate)

## 5. Important Rules

1. `hop` accepts only `1` or `2`; other values raise `ValueError`
2. When `hop=1`, input column is hard-coded `"tuple"`; `input_key_meta` has no effect
3. Output column name is flat `output_key` — does NOT carry `{hop}_` prefix
4. Rows with `len(QA_pairs) < 2` are dropped to `[]`; expect some empty rows
5. LLM parse failures also produce `[]`

## 6. Typical Usage

```python
# 1-hop hyper-tuple QA
self.hrkg_qa = HRKGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=1, lang="en",
)
self.hrkg_qa.run(
    storage=self.storage.step(),
    output_key="QA_pairs",
)

# 2-hop path QA
self.hrkg_qa = HRKGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=2, lang="en",
)
self.hrkg_qa.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key="QA_pairs",
)
```

## 7. Return Value

```python
return [output_key]
```
