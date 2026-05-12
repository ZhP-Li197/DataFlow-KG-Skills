# Example: 2-hop Hyper-Relation Path QA

## Field Flow
```
raw_chunk → entity → [HRKGTripleExtraction] → tuple → [KGRelationTuplePathGenerator(k=2)] → 2_hop_paths → [HRKGRelationTriplePathQAGeneration(hop=2)] → QA_pairs
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGRelationTuplePathGenerator,
)
from dataflow.operators.hyper_relation_kg import (
    HRKGTripleExtraction,
    HRKGRelationTriplePathQAGeneration,
)


class HyperPathQAPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/positions.json",
            cache_path="./cache",
            file_name_prefix="hrkg_qa_step",
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
        self.hrkg_extractor = HRKGTripleExtraction(
            llm_serving=self.llm_serving, lang="en",
        )
        self.path_sampler = KGRelationTuplePathGenerator(k=2, max_paths_per_group=100)
        self.hrkg_qa = HRKGRelationTriplePathQAGeneration(
            llm_serving=self.llm_serving, hop=2, lang="en",
        )

    def forward(self):
        self.entity_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk", output_key="entity",
        )
        self.hrkg_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk", output_key="tuple",
        )
        self.path_sampler.run(
            storage=self.storage.step(),
            input_key="tuple",
            output_key_meta="hop_paths",
        )
        self.hrkg_qa.run(
            storage=self.storage.step(),
            input_key_meta="hop_paths",
            output_key="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = HyperPathQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- Output column is the flat `QA_pairs`, unlike the temporal variant which prefixes with the hop number
- `KGRelationTuplePathGenerator` is reused here; pass `input_key="tuple"` so it reads from the hyper-tuple column
- The path sampler must use `k=2` to match `hop=2` on the QA generator; mismatched values cause a column-not-found error
- Rows with fewer than 2 QA pairs get cleared to `[]` by the operator's built-in quality gate; raise model temperature or pick a stronger model if too many rows are empty
