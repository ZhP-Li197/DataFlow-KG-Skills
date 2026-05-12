# Example: 2-hop Path QA

## Field Flow
```
raw_chunk → entity → triple → [KGRelationTuplePathGenerator(k=2)] → 2_hop_paths → [KGRelationTriplePathQAGeneration(hop=2)] → QA_pairs
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGRelationTuplePathGenerator,
    KGRelationTriplePathQAGeneration,
)


class PathQAPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/input.json",
            cache_path="./cache",
            file_name_prefix="path_qa_step",
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
        self.path_sampler = KGRelationTuplePathGenerator(k=2, max_paths_per_group=100)
        self.path_qa_generator = KGRelationTriplePathQAGeneration(
            llm_serving=self.llm_serving, hop=2, lang="en",
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
        self.path_sampler.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key_meta="hop_paths",
        )
        self.path_qa_generator.run(
            storage=self.storage.step(),
            input_key_meta="hop_paths",
            output_key="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = PathQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- The path sampler writes its output to `"2_hop_paths"`; the QA generator reads from the same column because `hop=2` and `input_key_meta="hop_paths"`
- For 1-hop QA, drop the path sampler and instantiate `KGRelationTriplePathQAGeneration(hop=1)` directly after triple extraction; it will read `"triple"` automatically
- Output column is always `QA_pairs` (no `{hop}_` prefix, unlike the temporal variant)
