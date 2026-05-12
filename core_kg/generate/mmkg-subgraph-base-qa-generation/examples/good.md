# Example: Multimodal Subgraph QA Generation

## Field Flow
```
(vis_url, subgraph, vis_triple) → [MMKGSubgraphBaseQAGeneration] → QA_pairs
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
    MMKGSubgraphBaseQAGeneration,
)


class MultimodalQAPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/launch.json",
            cache_path="./cache",
            file_name_prefix="mmkg_qa_step",
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
            input_key="triple", output_key="subgraph",
            vis_triple_key="vis_triple", sampling_type="hop", hop=2,
        )
        self.mm_qa_generator.run(
            storage=self.storage.step(),
            input_key="vis_url", input_key_meta="subgraph", output_key="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = MultimodalQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- All five steps must run in this order. Skipping the subgraph sampler will leave `vis_url`/`vis_triple` misaligned and the QA generator will produce noisy or empty output
- The VLM is invoked twice: once during step 3 (visual triple extraction) and once during step 5 (QA generation). Costs scale with `len(vis_url)` per row
- An empty `QA_pairs` list is the most common failure mode — typically caused by malformed vis_triple regex matches; check the upstream cache file
