---
name: kg-relation-triple-path-qa-generation
description: >-
  Reference for KGRelationTriplePathQAGeneration. LLM-generates QA pairs over
  1-hop triples or 2-hop paths from KGRelationTuplePathGenerator.
  Use when: building reasoning-flavored QA grounded in a path-shaped KG context.

trigger_keywords:
  - KGRelationTriplePathQAGeneration
  - kg-relation-triple-path-qa-generation
  - path QA
  - 1-hop QA
  - 2-hop QA

version: 1.0.0
---

# KGRelationTriplePathQAGeneration Operator Reference

QA generator over single triples (`hop=1`) or 2-hop paths (`hop=2`). The input column is selected dynamically based on `hop`.

## 1. Import

```python
from dataflow.operators.general_kg import KGRelationTriplePathQAGeneration
```

## 2. Constructor

```python
KGRelationTriplePathQAGeneration(
    llm_serving,                # required
    seed=0,
    lang="en",
    hop=1,                      # 1 or 2
    num_q=5,                    # reserved, unused
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |
| `hop` | No | `1` | `1` selects `KGOneHopQAPathGenerationPrompt`; `2` selects `KGTwoHopPathQAGenerationPrompt` |
| `num_q` | No | `5` | Reserved, unused |

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
| `storage` | Yes | `None` | Step storage |
| `input_key_meta` | No | `"hop_paths"` | Used only when `hop>1`; input column resolved as `"{hop}_{input_key_meta}"` (e.g. `"2_hop_paths"`) |
| `output_key` | No | `"QA_pairs"` | Output column name |

## 4. Actual Execution Logic

1. Resolve `input_key`:
   - `hop=1` → reads the literal `"triple"` column (ignores `input_key_meta`)
   - `hop>1` → reads `"{hop}_{input_key_meta}"` (e.g. `"2_hop_paths"`)
2. For each row, call the LLM with the path string
3. Parse the response and write `QA_pairs` list to the output column
4. Output column name is **always** `output_key` (no `{hop}_` prefix)

## 5. Important Rules

1. `hop` ∈ {1, 2} — other values are not exercised by the prompt selection
2. When `hop=1`, the input column is hard-coded to `"triple"`, regardless of `input_key_meta`
3. The operator does not filter rows by `len(QA_pairs)` — empty lists are kept as-is
4. Row count is preserved

## 6. Typical Usage

```python
# 1-hop QA over triples
self.qa_generator = KGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=1, lang="en",
)
self.qa_generator.run(
    storage=self.storage.step(),
    output_key="QA_pairs",
)

# 2-hop QA over sampled paths
self.qa_generator = KGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=2, lang="en",
)
self.qa_generator.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key="QA_pairs",
)
```

## 7. Return Value

```python
return [output_key]
```
