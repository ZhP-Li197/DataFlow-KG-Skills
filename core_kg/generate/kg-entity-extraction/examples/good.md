# Example: Single-Step Entity Extraction

## User Request
"Extract a list of named entities from short paragraphs."

## Sample Data
```json
[
  {"raw_chunk": "Marie Curie was a physicist and chemist. She was born in Warsaw. Pierre Curie was her husband and research partner."},
  {"raw_chunk": "Alan Turing studied mathematics at Cambridge. He worked at Bletchley Park during World War II as a cryptanalyst."}
]
```

## Field Mapping
```
Available: raw_chunk
Generated: entity
Field flow: raw_chunk → [KGEntityExtraction] → entity
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import KGEntityExtraction


class EntityExtractionPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/bios.json",
            cache_path="./cache",
            file_name_prefix="entity_step",
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
            llm_serving=self.llm_serving,
            lang="en",
        )

    def forward(self):
        self.entity_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="entity",
        )


if __name__ == "__main__":
    pipeline = EntityExtractionPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Debugging
- `cache/entity_step_step1.json` — each row gains an `entity` column with a comma-separated string like `"Marie Curie, Pierre Curie, Warsaw"`
- Empty `entity` strings indicate the text failed the length / sentence-count / special-char-ratio gate, or the LLM response could not be parsed
