# Example: Hyper-Relation KG Path-based QA

## User Request

```
Target: From statements that carry qualifiers (role, period, location) per fact, extract a hyper-relation KG and generate 2-hop path-based QA.
Sample file: ./data/positions.json
Expected outputs: QA_pairs
```

## Sample Data

```json
[
  {"doc_id": "p-1", "raw_chunk": "Barack Obama served as the 44th President of the United States from 2009 to 2017. He was the first African American president. He was awarded the Nobel Peace Prize in 2009."},
  {"doc_id": "p-2", "raw_chunk": "Angela Merkel served as Chancellor of Germany from 2005 to 2021. She represented the Christian Democratic Union. She earned a doctorate in quantum chemistry before entering politics."}
]
```

Each fact has more than the (subject, relation, object) triple — there are qualifiers like time period, role, organization. Hyper-relation KG captures these as `<attribute>` slots inside each tuple.

## Stage 1: Operator Decision

```json
{
  "kg_type": "hyper-relation",
  "task": "path_qa",
  "ops": ["KGEntityExtraction", "HRKGTripleExtraction", "KGRelationTuplePathGenerator", "HRKGRelationTriplePathQAGeneration"],
  "field_flow": "raw_chunk -> entity -> tuple -> 2_hop_paths -> QA_pairs",
  "reason": "Sample sentences carry multiple qualifiers per fact (date range, role, organization) that don't fit a flat triple — hyper-relation KG fits. Path-based QA matches the user's request; the chain reuses the general-purpose path sampler on the hyper-tuple output."
}
```

## Stage 2

### Field Mapping

| Sample field | Role | Notes |
|---|---|---|
| `doc_id` | passthrough | dropped at path sampling |
| `raw_chunk` | source text | consumed by `KGEntityExtraction`, `HRKGTripleExtraction` |

Generated: `entity`, `tuple` (hyper-tuples), `2_hop_paths`, `QA_pairs`.

### Ordered Operator List

1. `KGEntityExtraction(lang="en")` — `raw_chunk` → `entity`
2. `HRKGTripleExtraction(lang="en")` — `raw_chunk` → `tuple`
3. `KGRelationTuplePathGenerator(k=2)` — `input_key="tuple"`, `output_key_meta="hop_paths"` → column `2_hop_paths` (**row-expanding**)
4. `HRKGRelationTriplePathQAGeneration(hop=2, lang="en")` — `input_key_meta="hop_paths"` → `QA_pairs`

### Reasoning Summary

`HRKGTripleExtraction` writes hyper-tuples to the `tuple` column (not `triple`). The general-purpose `KGRelationTuplePathGenerator` parses any tuple format that includes `<subj>`, `<obj>`, `<rel>` markers, so it handles hyper-tuples too — just pass `input_key="tuple"`.

`HRKGRelationTriplePathQAGeneration` writes its output to a column called `QA_pairs` (not `2_QA_pairs` — only the temporal QA generator prefixes the hop number). Rows whose QA generation yields fewer than 2 pairs are reset to `[]`, so expect some empty rows in the output cache.

Although the original `KGEntityExtraction` step is technically optional (the hyper-relation extractor does not consume `entity`), running it first lets the user feed the same `entity` column into other downstream operators (e.g. a domain-specific filter) without re-extracting.

### Complete Pipeline Code

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


class HyperRelationPathQAPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/positions.json",
            cache_path="./cache",
            file_name_prefix="hrkg_path_qa_step",
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
        self.path_sampler = KGRelationTuplePathGenerator(
            k=2,
            max_paths_per_group=100,
        )
        self.path_qa_generator = HRKGRelationTriplePathQAGeneration(
            llm_serving=self.llm_serving, hop=2, lang="en",
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
        self.path_sampler.run(
            storage=self.storage.step(),
            input_key="tuple",
            output_key_meta="hop_paths",
        )
        self.path_qa_generator.run(
            storage=self.storage.step(),
            input_key_meta="hop_paths",
            output_key="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = HyperRelationPathQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

### Adjustable Parameters / Caveats

- `hop=1` reads the `tuple` column directly and asks single-fact QA; `hop=2` reads `2_hop_paths`. Only `1` and `2` are supported — `3+` raises `ValueError`
- `KGRelationTuplePathGenerator(k=2)` and `HRKGRelationTriplePathQAGeneration(hop=2)` must agree on the same number; the output column name is derived from `k` and the input column name from `hop`
- Hyper-tuple format varies by upstream LLM output — the operator preserves whatever JSON structure the LLM emits in the `tuple` field
- If many rows end up with `QA_pairs == []`, lower model temperature or switch to a stronger model; the operator filters out rows producing fewer than 2 pairs
