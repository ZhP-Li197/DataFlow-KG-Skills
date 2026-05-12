---
name: mmkg-visual-triple-extraction
description: >-
  Reference for MMKGVisualTripleExtraction. Uses a VLM to extract visual
  triples linking textual entities to images in img_dict.
  Use when: building a multimodal KG that grounds entities in local image evidence.

trigger_keywords:
  - MMKGVisualTripleExtraction
  - mmkg-visual-triple-extraction
  - visual triple
  - multimodal KG extraction
  - VLM

version: 1.0.0
---

# MMKGVisualTripleExtraction Operator Reference

VLM-based extractor that, for each (entity candidate × image) pair, decides whether the image depicts the entity and emits a `depicted_in` visual triple.

## 1. Import

```python
from dataflow.operators.multi_model_kg import MMKGVisualTripleExtraction
```

## 2. Constructor

```python
MMKGVisualTripleExtraction(
    llm_serving,                # required — must be APIVLMServing_openai
    quality_threshold=3,        # VLM quality_score gate
    lang="en",
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `llm_serving` | Yes | None | VLM serving backend; pass an `APIVLMServing_openai` instance |
| `quality_threshold` | No | `3` | Integer 1-5; VLM responses with `quality_score < threshold` are dropped |
| `lang` | No | `"en"` | Prompt language |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="img_dict",
    input_key_meta="entity",
    output_key="vis_triple",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `storage` | Yes | None | Step storage |
| `input_key` | No | `"img_dict"` | Image dict column (`{img_id: local_path}`) |
| `input_key_meta` | No | `"entity"` | Candidate entity list column |
| `output_key` | No | `"vis_triple"` | Output triple list column |

## 4. Actual Execution Logic

1. For each row, read `img_dict` (accepts a dict or a JSON-encoded string) and `entity` (comma-separated list)
2. For each image, build a VLM prompt with the entity candidates and call `generate_from_input_multi_images(...)`
3. Parse each response — expect a JSON with `quality_score` and `entity` keys
4. Drop responses with `quality_score < quality_threshold`
5. For each predicted entity that matches a candidate (case-insensitive), emit `"<subj> {entity} <obj> {img_id} <rel> depicted_in "` (note trailing space)
6. Final `vis_triple` list is deduplicated via `set()`

## 5. Important Rules

1. `llm_serving` must be a VLM (`APIVLMServing_openai`), NOT the text-only `APILLMServing_request`
2. `img_dict` values must be **local file paths** — the VLM serving layer reads bytes with `open(path, "rb")`; remote URLs raise `FileNotFoundError`
3. Triple format is hard-coded as `"<subj> entity <obj> img_id <rel> depicted_in "` (the trailing space is intentional and consumed by downstream samplers)
4. Image extensions must be `.jpg`, `.jpeg`, or `.png` — `.webp` and other formats raise `ValueError` in `_encode_image_to_base64`
5. Row count is preserved; each row's `vis_triple` is a list value (possibly empty)

## 6. Typical Usage

```python
from dataflow.serving import APIVLMServing_openai

self.vlm_serving = APIVLMServing_openai(
    api_url="https://api.openai.com/v1",
    key_name_of_api_key="DF_API_KEY",
    model_name="gpt-4o-mini",
    max_workers=4,
    temperature=0.0,
)

self.visual_triple_extractor = MMKGVisualTripleExtraction(
    llm_serving=self.vlm_serving,
    quality_threshold=3,
    lang="en",
)

self.visual_triple_extractor.run(
    storage=self.storage.step(),
    input_key="img_dict",
    input_key_meta="entity",
    output_key="vis_triple",
)
```

## 7. Return Value

```python
return [output_key]
```
