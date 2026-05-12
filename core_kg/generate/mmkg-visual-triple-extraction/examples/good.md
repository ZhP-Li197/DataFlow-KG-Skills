# Example: Extract Visual Triples from Local Images

## Field Flow
```
raw_chunk → [KGEntityExtraction] → entity
img_dict + entity → [MMKGVisualTripleExtraction] → vis_triple
```

## Sample Input
```json
[
  {
    "raw_chunk": "Tesla unveiled the Cybertruck at a product event. Elon Musk appeared on stage during the launch presentation.",
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

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request, APIVLMServing_openai
from dataflow.operators.general_kg import KGEntityExtraction
from dataflow.operators.multi_model_kg import MMKGVisualTripleExtraction


class VisualTripleExtractionPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/launch.json",
            cache_path="./cache",
            file_name_prefix="mmkg_vis_step",
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
        self.visual_triple_extractor = MMKGVisualTripleExtraction(
            llm_serving=self.vlm_serving,
            quality_threshold=3,
            lang="en",
        )

    def forward(self):
        self.entity_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk", output_key="entity",
        )
        self.visual_triple_extractor.run(
            storage=self.storage.step(),
            input_key="img_dict",
            input_key_meta="entity",
            output_key="vis_triple",
        )


if __name__ == "__main__":
    pipeline = VisualTripleExtractionPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- Both `APILLMServing_request` (for `KGEntityExtraction`) and `APIVLMServing_openai` (for `MMKGVisualTripleExtraction`) are required. Both can point at the same OpenAI-compatible endpoint with a vision-capable model
- Lower `quality_threshold` (e.g. 1-2) yields more triples at the cost of noise; raise it (e.g. 4-5) for high-precision pipelines
- Empty `vis_triple` lists usually mean either the VLM saw nothing relevant or the threshold filtered all responses out
