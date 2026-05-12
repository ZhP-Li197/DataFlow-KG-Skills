# Example: Extract Hyper-Relation Tuples

## Field Flow
```
raw_chunk → [KGEntityExtraction] → entity → [HRKGTripleExtraction] → tuple
```

Although `HRKGTripleExtraction` does not read `entity` directly, running entity extraction first gives downstream operators consistent column names for joint use.

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import KGEntityExtraction
from dataflow.operators.hyper_relation_kg import HRKGTripleExtraction


class HyperTupleExtractionPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/positions.json",
            cache_path="./cache",
            file_name_prefix="hrkg_step",
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

    def forward(self):
        self.entity_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="entity",
        )
        self.hrkg_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="tuple",
        )


if __name__ == "__main__":
    pipeline = HyperTupleExtractionPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- Hyper-tuple text format is LLM-dependent; expect `<subj> ... <obj> ... <rel> ... <attribute> ...` style strings or nested JSON objects
- Downstream path samplers expect column `tuple`, so pass `input_key="tuple"` when reusing `KGRelationTuplePathGenerator`
- Sparse extractions (lots of empty lists) usually indicate the LLM did not detect multi-argument structure — try a stronger model or richer text
