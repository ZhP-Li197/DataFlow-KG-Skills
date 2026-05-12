# Example: Multimodal Subgraph Sampling

## Field Flow
```
(triple, vis_triple, img_dict) → [MMKGEntityBasedSubgraphSampling] → subgraph + filtered vis_triple + aligned vis_url
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request, APIVLMServing_openai
from dataflow.operators.general_kg import KGEntityExtraction, KGTripleExtraction
from dataflow.operators.multi_model_kg import (
    MMKGVisualTripleExtraction,
    MMKGEntityBasedSubgraphSampling,
)


class MultimodalSubgraphSamplingPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/launch.json",
            cache_path="./cache",
            file_name_prefix="mmkg_subg_step",
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

    def forward(self):
        self.entity_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk", output_key="entity",
        )
        self.triple_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk", input_key_meta="entity", output_key="triple",
        )
        self.visual_triple_extractor.run(
            storage=self.storage.step(),
            input_key="img_dict", input_key_meta="entity", output_key="vis_triple",
        )
        self.mm_subgraph_sampler.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key="subgraph",
            vis_triple_key="vis_triple",
            sampling_type="hop",
            hop=2,
        )


if __name__ == "__main__":
    pipeline = MultimodalSubgraphSamplingPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- The output rows are aligned by entity; one row per starting entity covers (textual subgraph, filtered visual triples, image paths)
- `sampling_type` must be `"bfs"` or `"hop"`; the multimodal variant does not implement random walk
- Downstream `MMKGSubgraphBaseQAGeneration` reads from the three output columns by name; do not rename them in subsequent steps
