# Example: Triple Inference with Merge-Back

## User Request
"After extracting triples, infer additional relations from the original text and merge them back into the triple list."

## Sample Data
```json
[
  {"raw_chunk": "Marie Curie was a physicist and chemist. She was born in Warsaw. Pierre Curie was her husband and research partner."}
]
```

## Field Mapping
```
Available: raw_chunk
Generated: entity, triple (overwritten), inferred_triple
Field flow: raw_chunk → entity → triple → [KGRelationTripleInference(with_text=True, merge_to_input=True)] → triple (extended) + inferred_triple
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGRelationTripleInference,
)


class InferencePipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/input.json",
            cache_path="./cache",
            file_name_prefix="inference_step",
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
        self.inferrer = KGRelationTripleInference(
            llm_serving=self.llm_serving,
            lang="en",
            with_text=True,
            merge_to_input=True,
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
        self.inferrer.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key="inferred_triple",
        )


if __name__ == "__main__":
    pipeline = InferencePipeline()
    pipeline.compile()
    pipeline.forward()
```

## Debugging
- `cache/inference_step_step3.json` — `triple` is the merged (original + inferred) list; `inferred_triple` is the inferred subset
- If `merge_to_input=False`, the original `triple` column is preserved and only `inferred_triple` is added
