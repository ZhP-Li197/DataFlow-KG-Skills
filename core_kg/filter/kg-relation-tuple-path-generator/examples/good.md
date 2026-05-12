# Example: 2-hop Path Enumeration over Relation Triples

## Field Flow
```
triple → [KGRelationTuplePathGenerator(k=2)] → 2_hop_paths
```

Row count expands: one row per distinct 2-hop path discovered across all input triples.

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGRelationTuplePathGenerator,
)


class PathSamplingPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/input.json",
            cache_path="./cache",
            file_name_prefix="path_step",
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
        self.path_sampler = KGRelationTuplePathGenerator(
            k=2,
            max_paths_per_group=100,
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
        self.path_sampler.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key_meta="hop_paths",
        )


if __name__ == "__main__":
    pipeline = PathSamplingPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- Output column is `"2_hop_paths"` (the `k` value is prefixed automatically); to read it downstream, set `hop=2` on the path-QA generator
- For temporal KG, run the upstream `TKGTupleExtraction` first and pass `input_key="tuple"` to this operator
- For hyper-relation KG, same as above with `HRKGTripleExtraction`
