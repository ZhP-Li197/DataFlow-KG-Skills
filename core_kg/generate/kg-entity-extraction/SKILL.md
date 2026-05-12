---
name: kg-entity-extraction
description: >-
  Reference documentation for the KGEntityExtraction operator. Extracts entity
  surface forms from raw text using an LLM.
  Use when: every KG pipeline needs an entity column before triple/quadruple
  extraction; this operator produces it from a free-text input column.

trigger_keywords:
  - KGEntityExtraction
  - kg-entity-extraction
  - entity extraction
  - KG entity

version: 1.0.0
---

# KGEntityExtraction Operator Reference

`KGEntityExtraction` is the canonical entry point for DataFlow-KG pipelines. It reads a raw text column and emits a comma-separated entity string per row.

## 1. Import

```python
from dataflow.operators.general_kg import KGEntityExtraction
```

## 2. Constructor

```python
KGEntityExtraction(
    llm_serving,                # required
    seed=0,                     # optional
    lang="en",                  # optional; "en" or "zh"
    prompt_template=None,       # optional; defaults to KGEntityExtractionPrompt(lang)
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | LLM serving object (e.g. `APILLMServing_request`) |
| `seed` | No | `0` | Random seed; initializes an internal `Random` but is not used during inference |
| `lang` | No | `"en"` | Prompt language; `"en"` or `"zh"` |
| `prompt_template` | No | `None` | Custom `KGEntityExtractionPrompt` or `DIYPromptABC` instance; `None` falls back to the default |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entity",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | `None` | Current operator-step storage object |
| `input_key` | No | `"raw_chunk"` | Column read from the current DataFrame |
| `output_key` | No | `"entity"` | Column written back |

## 4. Actual Execution Logic

1. Read the DataFrame from `storage`
2. Validate `input_key` exists and `output_key` does NOT
3. For each row, preprocess the text and skip if it fails any quality gate:
   - Length must be ≥ 10 and ≤ 200000 characters
   - Must contain ≥ 2 sentence terminators (`.` or `。`)
   - Special-character ratio must be ≤ 30%
4. Build a prompt via the template and call `llm_serving.generate_from_input(...)` per row
5. Parse the LLM JSON response into a list of entity strings; join with `", "`
6. Strip common English stopwords (`the / a / an / of / and / or / ...`) when normalizing
7. Write the resulting strings into `dataframe[output_key]` and persist via `storage.write(...)`
8. Return `[output_key]`

## 5. Important Rules

1. `input_key` must exist in the current DataFrame
2. `output_key` must NOT exist (no overwriting)
3. Rows that fail the text-quality gate get an empty string `""` as their entity — they are not removed
4. On LLM parse failure the row also gets `""`; no exception is raised

## 6. Typical Usage

```python
from dataflow.operators.general_kg import KGEntityExtraction

self.entity_extractor = KGEntityExtraction(
    llm_serving=self.llm_serving,
    lang="en",
)

self.entity_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entity",
)
```

## 7. Return Value

```python
return [output_key]
```

Used for downstream chaining and column tracking.
