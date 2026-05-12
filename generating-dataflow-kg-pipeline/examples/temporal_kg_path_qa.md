# Example: Temporal KG Path-based QA

## User Request

```
Target: From dated news snippets, build a temporal KG and generate time-anchored QA pairs over 2-hop paths.
Sample file: ./data/news.json
Expected outputs: 2_QA_pairs
```

## Sample Data

```json
[
  {"doc_id": "news-1", "raw_chunk": "In March 2020, the WHO declared COVID-19 a pandemic. Two months later, the U.S. CDC issued indoor mask guidance. By December 2020, the FDA had authorized the Pfizer vaccine for emergency use."},
  {"doc_id": "news-2", "raw_chunk": "Apple released the iPhone in June 2007. The App Store launched in July 2008. Apple acquired Beats Electronics in 2014. In 2020, Apple announced its transition to Apple Silicon for Macs."}
]
```

## Stage 1: Operator Decision

```json
{
  "kg_type": "temporal",
  "task": "path_qa",
  "ops": ["TKGTupleExtraction", "KGRelationTuplePathGenerator", "TKGTuplePathQAGeneration"],
  "field_flow": "raw_chunk -> tuple -> 2_hop_paths -> 2_QA_pairs",
  "reason": "Sample text is loaded with explicit dates and event orderings — temporal KG fits. User asked for path-based time QA, so the chain reuses the general-purpose KGRelationTuplePathGenerator on the 4-tuple output before the time-aware QA generator."
}
```

## Stage 2

### Field Mapping

| Sample field | Role | Notes |
|---|---|---|
| `doc_id` | passthrough | dropped at path sampling (row-expanding step) |
| `raw_chunk` | source text | consumed by `TKGTupleExtraction` |

Generated: `tuple` (List of time-anchored 4-tuples), `2_hop_paths` (List[str], one row per path), `2_QA_pairs` (List[Dict]).

### Ordered Operator List

1. `TKGTupleExtraction(triple_type="relation", lang="en")` — `raw_chunk` → `tuple`
2. `KGRelationTuplePathGenerator(k=2)` — `input_key="tuple"`, `output_key_meta="hop_paths"` → column `2_hop_paths` (**row-expanding**)
3. `TKGTuplePathQAGeneration(hop=2, qa_type="time_order", lang="en")` — `input_key_meta="hop_paths"`, `output_key_meta="QA_pairs"` → column `2_QA_pairs`

### Reasoning Summary

`TKGTupleExtraction` writes its output to the `tuple` column (not `triple`). `KGRelationTuplePathGenerator` parses any `"<subj> ... <obj> ... <rel> ..."` format, so it works on 4-tuples too — pass `input_key="tuple"` instead of the default `"triple"`. With `k=2`, it writes paths into `2_hop_paths`.

`TKGTuplePathQAGeneration` has 4 QA flavors: `time_point` (when did X happen?), `event_order` (which happened first?), `time_order` (chronological), `time_interval` (how long between X and Y?). `time_order` is the most natural fit for the news examples.

Output column is `"{hop}_{output_key_meta}"` = `"2_QA_pairs"` because the generator pre-fixes the hop number.

### Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.temporal_kg import (
    TKGTupleExtraction,
    TKGTuplePathQAGeneration,
)
from dataflow.operators.general_kg import KGRelationTuplePathGenerator


class TemporalKGPathQAPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/news.json",
            cache_path="./cache",
            file_name_prefix="tkg_path_qa_step",
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
        self.path_sampler = KGRelationTuplePathGenerator(
            k=2,
            max_paths_per_group=100,
        )
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
    pipeline = TemporalKGPathQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

### Adjustable Parameters / Caveats

- `qa_type="time_point"` for "when did X happen?" style; `"event_order"` for binary ordering; `"time_interval"` for duration questions
- `k=1` + `hop=1` skips path sampling and asks QA directly over individual 4-tuples (then `TKGTuplePathQAGeneration(hop=1)` reads the `tuple` column and `input_key_meta` is ignored)
- `max_paths_per_group=100` caps the row expansion; lower to 20-30 for cheaper runs
- `KGRelationTuplePathGenerator` does NOT take `llm_serving` — it is a pure graph operation
- The path QA generator's output column is always `"{hop}_{output_key_meta}"`; you cannot pin it to a custom flat name
