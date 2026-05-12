# Example: Multimodal KG + Subgraph QA from Text and Local Images

## User Request

```
Target: Build a multimodal KG from a paragraph that has two product/event images, then generate visual QA grounded in both the text and the images.
Sample file: ./data/launch.json
Expected outputs: QA_pairs
```

## Sample Data

```json
[
  {
    "raw_chunk": "Tesla unveiled the Cybertruck at a product event. Elon Musk appeared on stage during the launch presentation. The presentation focused on electric vehicle design and manufacturing.",
    "img_dict": {
      "img_cybertruck": "./images/cyber.jpg",
      "img_musk_stage": "./images/musk.jpg"
    },
    "vis_url": [
      "./images/cyber.jpg",
      "./images/musk.jpg"
    ]
  }
]
```

## Stage 1: Operator Decision

```json
{
  "kg_type": "multimodal",
  "task": "multimodal_qa",
  "ops": ["KGEntityExtraction", "KGTripleExtraction", "MMKGVisualTripleExtraction", "MMKGEntityBasedSubgraphSampling", "MMKGSubgraphBaseQAGeneration"],
  "field_flow": "raw_chunk -> entity -> triple, img_dict+entity -> vis_triple -> subgraph+vis_triple+vis_url -> QA_pairs",
  "reason": "Sample carries both text and a local image dict — multimodal KG fits. The chain produces textual triples, visual triples linking entities to image IDs, then samples subgraphs that bundle text + visual + URL, and finally calls a VLM-backed QA generator that sees both subgraph and images."
}
```

## Stage 2

### Field Mapping

| Sample field | Role | Notes |
|---|---|---|
| `raw_chunk` | source text | consumed by `KGEntityExtraction`, `KGTripleExtraction` |
| `img_dict` | image table | `{img_id: local_path}`; consumed by `MMKGVisualTripleExtraction` |
| `vis_url` | image path list | aligned with `MMKGEntityBasedSubgraphSampling` output; consumed by `MMKGSubgraphBaseQAGeneration` |

Generated: `entity`, `triple`, `vis_triple`, `subgraph`, `QA_pairs`.

### Ordered Operator List

1. `KGEntityExtraction` — `raw_chunk` → `entity`
2. `KGTripleExtraction(triple_type="relation")` — `(raw_chunk, entity)` → `triple`
3. `MMKGVisualTripleExtraction(quality_threshold=3)` — `(img_dict, entity)` → `vis_triple` (uses VLM)
4. `MMKGEntityBasedSubgraphSampling(sampling_type="hop", hop=2)` — `(triple, vis_triple, img_dict)` → `subgraph + vis_triple + vis_url` (**row-expanding**)
5. `MMKGSubgraphBaseQAGeneration` — `(vis_url, subgraph)` → `QA_pairs` (uses VLM)

### Reasoning Summary

The visual triple extractor produces strings of form `"<subj> {entity} <obj> {img_id} <rel> depicted_in "`. `MMKGEntityBasedSubgraphSampling` aligns `vis_url` with the `vis_triple` order so the downstream QA generator can rebuild the `img_id → url` mapping correctly.

Two serving instances are required: a text LLM for steps 1-2 and a VLM (`APIVLMServing_openai`) for steps 3 and 5. Both can point at the same OpenAI-compatible endpoint with a vision-capable model (e.g. `gpt-4o-mini`).

Image paths in the sample must be **local files**: `APIVLMServing_openai._encode_image_to_base64` calls `open(path, "rb")` and does not fetch remote URLs.

### Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request, APIVLMServing_openai
from dataflow.operators.general_kg import KGEntityExtraction, KGTripleExtraction
from dataflow.operators.multi_model_kg import (
    MMKGVisualTripleExtraction,
    MMKGEntityBasedSubgraphSampling,
    MMKGSubgraphBaseQAGeneration,
)


class MultimodalKGPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/launch.json",
            cache_path="./cache",
            file_name_prefix="mmkg_step",
            cache_type="json",
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o-mini",
            max_workers=4,
            temperature=0.0,
        )
        self.vlm_serving = APIVLMServing_openai(
            api_url="https://api.openai.com/v1",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o-mini",
            max_workers=4,
            temperature=0.0,
        )

        self.entity_extractor = KGEntityExtraction(
            llm_serving=self.llm_serving, lang="en",
        )
        self.triple_extractor = KGTripleExtraction(
            llm_serving=self.llm_serving, triple_type="relation", lang="en",
        )
        self.visual_triple_extractor = MMKGVisualTripleExtraction(
            llm_serving=self.vlm_serving, quality_threshold=3, lang="en",
        )
        self.mm_subgraph_sampler = MMKGEntityBasedSubgraphSampling(
            llm_serving=self.llm_serving, lang="en",
        )
        self.mm_qa_generator = MMKGSubgraphBaseQAGeneration(
            llm_serving=self.vlm_serving, lang="en",
        )

    def forward(self):
        self.entity_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="entity",
        )
        self.triple_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            input_key_meta="entity",
            output_key="triple",
        )
        self.visual_triple_extractor.run(
            storage=self.storage.step(),
            input_key="img_dict",
            input_key_meta="entity",
            output_key="vis_triple",
        )
        self.mm_subgraph_sampler.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key="subgraph",
            vis_triple_key="vis_triple",
            sampling_type="hop",
            hop=2,
        )
        self.mm_qa_generator.run(
            storage=self.storage.step(),
            input_key="vis_url",
            input_key_meta="subgraph",
            output_key="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = MultimodalKGPipeline()
    pipeline.compile()
    pipeline.forward()
```

### Adjustable Parameters / Caveats

- `quality_threshold` raises/lowers the VLM filter on visual triples (default 3 on a 1-5 scale)
- `sampling_type="bfs"` + `M=5` for a tighter subgraph; `"hop"` is the default but does not accept `"rw"` in the multimodal variant
- The VLM must support image inputs. `o4-mini`, `gpt-4o`, and `gpt-4o-mini` all work via `APIVLMServing_openai`
- Verify each path in `img_dict` and `vis_url` actually exists on disk before running, or the VLM step raises `FileNotFoundError`
- `vis_triple` column name is hard-coded inside `MMKGSubgraphBaseQAGeneration` — do not rename it
