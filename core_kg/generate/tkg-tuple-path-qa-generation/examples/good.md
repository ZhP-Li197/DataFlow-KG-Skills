# Example: 2-hop Time-Order QA over News Timelines

## Field Flow
```
raw_chunk → [TKGTupleExtraction] → tuple → [KGRelationTuplePathGenerator(k=2)] → 2_hop_paths → [TKGTuplePathQAGeneration(hop=2, qa_type="time_order")] → 2_QA_pairs
```

## Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.temporal_kg import TKGTupleExtraction, TKGTuplePathQAGeneration
from dataflow.operators.general_kg import KGRelationTuplePathGenerator


class TemporalPathQAPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/news.json",
            cache_path="./cache",
            file_name_prefix="tkg_path_step",
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
        self.path_sampler = KGRelationTuplePathGenerator(k=2, max_paths_per_group=100)
        self.path_qa_generator = TKGTuplePathQAGeneration(
            llm_serving=self.llm_serving,
            hop=2,
            qa_type="time_order",
            lang="en",
        )

    def forward(self):
        self.tuple_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="tuple",
        )
        self.path_sampler.run(
            storage=self.storage.step(),
            input_key="tuple",
            output_key_meta="hop_paths",
        )
        self.path_qa_generator.run(
            storage=self.storage.step(),
            input_key_meta="hop_paths",
            output_key_meta="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = TemporalPathQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- `qa_type` options: `"time_point"`, `"event_order"`, `"time_order"`, `"time_interval"` — pick by what kind of questions the dataset should produce
- Final output column is `"2_QA_pairs"` (always prefixed with `hop`); flatten in pandas post-processing if a flat column is needed
- For 1-hop QA over individual 4-tuples, drop the path sampler and set `hop=1`; the QA operator will read `"tuple"` directly
