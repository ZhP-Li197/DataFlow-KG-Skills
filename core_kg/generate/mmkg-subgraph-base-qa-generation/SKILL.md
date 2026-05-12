---
name: mmkg-subgraph-base-qa-generation
description: >-
  Reference for MMKGSubgraphBaseQAGeneration. VLM-generated QA pairs grounded
  in a textual subgraph plus its aligned vis_triple and vis_url.
  Use when: producing multimodal QA from MMKGEntityBasedSubgraphSampling output.

trigger_keywords:
  - MMKGSubgraphBaseQAGeneration
  - mmkg-subgraph-base-qa-generation
  - multimodal QA
  - VLM QA

version: 1.0.0
---

# MMKGSubgraphBaseQAGeneration Operator Reference

Multimodal QA generator. Reads a row's `vis_url` list and `subgraph`, internally rebuilds an `img_id → url` map by parsing `vis_triple`, and calls a VLM with the corresponding images plus the subgraph triples.

## 1. Import

```python
from dataflow.operators.multi_model_kg import MMKGSubgraphBaseQAGeneration
```

## 2. Constructor

```python
MMKGSubgraphBaseQAGeneration(
    llm_serving,                # required — must be APIVLMServing_openai
    lang="en",
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | VLM serving backend |
| `lang` | No | `"en"` | Prompt language |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="vis_url",
    input_key_meta="subgraph",
    output_key="QA_pairs",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | None | Step storage |
| `input_key` | No | `"vis_url"` | Image-path list column |
| `input_key_meta` | No | `"subgraph"` | Subgraph triple list column |
| `output_key` | No | `"QA_pairs"` | Output QA list column |

## 4. Actual Execution Logic

1. Read DataFrame; per row, pull `vis_url`, `vis_triple` (hard-coded column name), and `subgraph`
2. Parse `img_id` from each `vis_triple` via regex `r"<obj>\s*(.+?)\s*(?=<rel>)"`
3. Build `img_dict` by zipping deduplicated img_ids (first-appearance order) with `vis_url` entries
4. If `subgraph` is a string, split on `"\n"` to obtain triple list
5. Per image, call the VLM with the matching image plus the subgraph context
6. Extract `QA_pairs` from each LLM JSON response; aggregate all image-level QAs into one row's output

## 5. Important Rules

1. `llm_serving` must be `APIVLMServing_openai`
2. The column name `vis_triple` is hard-coded — do not rename upstream
3. `vis_url` and `vis_triple` must be aligned in the order produced by `MMKGEntityBasedSubgraphSampling`. Manual edits between sampler and QA generator will break the mapping
4. LLM parse failures produce empty list `[]`; the row is not removed
5. Row count is preserved; each row's `QA_pairs` is a list value

## 6. Typical Usage

```python
self.mm_qa_generator = MMKGSubgraphBaseQAGeneration(
    llm_serving=self.vlm_serving,
    lang="en",
)

self.mm_qa_generator.run(
    storage=self.storage.step(),
    input_key="vis_url",
    input_key_meta="subgraph",
    output_key="QA_pairs",
)
```

## 7. Return Value

```python
return [output_key]
```
