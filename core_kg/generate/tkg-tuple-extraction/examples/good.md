# Example: Extract Temporal 4-tuples from News

## Field Flow
```
raw_chunk → [TKGTupleExtraction(triple_type="relation")] → tuple
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.temporal_kg import TKGTupleExtraction


class TemporalExtractionPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/news.json",
            cache_path="./cache",
            file_name_prefix="tkg_step",
            cache_type="json",
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o-mini",
            max_workers=4,
            temperature=0.0,
        )

        self.tuple_extractor = TKGTupleExtraction(
            llm_serving=self.llm_serving,
            triple_type="relation",
            lang="en",
        )

    def forward(self):
        self.tuple_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="tuple",
        )


if __name__ == "__main__":
    pipeline = TemporalExtractionPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- Use `triple_type="relation"` for news / event timelines; `"attribute"` for time-anchored properties (e.g. "Apple's CEO from 2011 to present is Tim Cook")
- The output column name is `tuple`, not `triple` — downstream samplers and QA generators must read from `tuple`
- An empty `tuple` list usually means the text failed the length / sentence-count gate
