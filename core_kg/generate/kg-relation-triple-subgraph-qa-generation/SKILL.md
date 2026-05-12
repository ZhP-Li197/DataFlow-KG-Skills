---
name: kg-relation-triple-subgraph-qa-generation
description: >-
  Reference for KGRelationTripleSubgraphQAGeneration. LLM-generates QA pairs
  grounded in a sampled subgraph column.
  Use when: a subgraph sampler has emitted local KG context per row and QA
  data is needed for training or evaluation.

trigger_keywords:
  - KGRelationTripleSubgraphQAGeneration
  - kg-relation-triple-subgraph-qa-generation
  - subgraph QA
  - KG QA generation

version: 1.0.0
---

# KGRelationTripleSubgraphQAGeneration Operator Reference

LLM-based QA generator that takes a subgraph (list of triples per row) and produces a list of `{"question", "answer"}` pairs.

## 1. Import

```python
from dataflow.operators.general_kg import KGRelationTripleSubgraphQAGeneration
```

## 2. Constructor

```python
KGRelationTripleSubgraphQAGeneration(
    llm_serving,                # required
    seed=0,
    lang="en",
    qa_type="num",              # "num" | "set" | "base"
    num_q=5,                    # reserved, unused
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving backend |
| `seed` | No | `0` | Random seed |
| `lang` | No | `"en"` | Prompt language |
| `qa_type` | No | `"num"` | `"num"` → counting/numerical QA; `"set"` → set-style QA; `"base"` → **AVOID** (has a `self.promt_template` typo in the current code) |
| `num_q` | No | `5` | Reserved, unused |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="subgraph",
    output_key="QA_pairs",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | `None` | Step storage |
| `input_key` | No | `"subgraph"` | Source subgraph list column |
| `output_key` | No | `"QA_pairs"` | Output column |

## 4. Actual Execution Logic

1. Read DataFrame; verify `input_key` exists and `output_key` does not
2. For each row, build a prompt over the subgraph triples and call `llm_serving.generate_from_input(...)`
3. Parse the LLM JSON response, extracting the `"QA_pairs"` field
4. On parse failure, the row gets an empty list `[]`; no exception

## 5. Important Rules

1. `qa_type="base"` selects an internal branch with a known typo (`self.promt_template`) and will raise `AttributeError` at run time — use `"num"` or `"set"` only
2. Row count is preserved; each row's `QA_pairs` is a list value
3. The operator does not validate the subgraph's triple format; malformed strings are forwarded to the LLM as-is

## 6. Typical Usage

```python
self.qa_generator = KGRelationTripleSubgraphQAGeneration(
    llm_serving=self.llm_serving,
    qa_type="set",
    lang="en",
)

self.qa_generator.run(
    storage=self.storage.step(),
    input_key="subgraph",
    output_key="QA_pairs",
)
```

## 7. Return Value

```python
return [output_key]
```
