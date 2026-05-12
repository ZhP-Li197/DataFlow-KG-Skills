# Example: Normalize Extracted Triples

## User Request
"After extracting triples, canonicalize synonymous relations."

## Sample Data
```json
[
  {"raw_chunk": "Marie Curie was a physicist and chemist. She was born in Warsaw. Pierre Curie was her husband and research partner."}
]
```

## Field Mapping
```
Available: raw_chunk
Generated: entity, triple, normalized_triple
Field flow: raw_chunk → entity → triple → [KGTupleNormalization] → normalized_triple
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGTupleNormalization,
)


class NormalizationPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/input.json",
            cache_path="./cache",
            file_name_prefix="norm_step",
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
        self.normalizer = KGTupleNormalization(
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
        self.normalizer.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key="normalized_triple",
        )


if __name__ == "__main__":
    pipeline = NormalizationPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Debugging
- `cache/norm_step_step3.json` — each row's `normalized_triple` should be the same or shorter than `triple` (synonyms merged)
- If the result is the string `""` instead of a list, the LLM response could not be parsed; check `cache/norm_step_step2.json` for the raw input
