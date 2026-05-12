# Example: 2-hop Subgraph Sampling per Entity

## Field Flow
```
triple → [KGEntityBasedSubgraphSampling(sampling_type="hop", hop=2)] → subgraph
```

Row count expands: one row per entity discovered in the input `triple` lists.

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGEntityBasedSubgraphSampling,
)


class SubgraphSamplingPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/input.json",
            cache_path="./cache",
            file_name_prefix="subgraph_step",
            cache_type="json",
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
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
        self.subgraph_sampler = KGEntityBasedSubgraphSampling(
            llm_serving=self.llm_serving, lang="en",
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
        self.subgraph_sampler.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key="subgraph",
            sampling_type="hop",
            hop=2,
        )


if __name__ == "__main__":
    pipeline = SubgraphSamplingPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- Switch to `sampling_type="bfs"` + `M=5` to cap each subgraph by triple count instead of radius
- `sampling_type="rw"` is more diverse but does not guarantee coverage of all neighbors
- Output column `subgraph` is a `List[str]` per row; upstream `doc_id`-style passthrough columns are dropped because the operator is row-expanding
