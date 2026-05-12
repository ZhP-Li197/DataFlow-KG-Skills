# Example: General KG Subgraph QA

## User Request

```
Target: Build a small KG from short paragraphs and generate set-based QA pairs over local subgraphs.
Sample file: ./data/wiki_snippets.json
Expected outputs: QA_pairs
```

## Sample Data

```json
[
  {"doc_id": "w-1", "raw_chunk": "Albert Einstein was born in Ulm, Germany in 1879. He developed the theory of relativity. He received the Nobel Prize in Physics in 1921."},
  {"doc_id": "w-2", "raw_chunk": "Marie Curie discovered polonium and radium. She was the first woman to win a Nobel Prize. She won prizes in both physics and chemistry."}
]
```

## Stage 1: Operator Decision

```json
{
  "kg_type": "general",
  "task": "subgraph_qa",
  "ops": ["KGEntityExtraction", "KGTripleExtraction", "KGEntityBasedSubgraphSampling", "KGRelationTripleSubgraphQAGeneration"],
  "field_flow": "raw_chunk -> entity -> triple -> subgraph -> QA_pairs",
  "reason": "User wants QA grounded in local subgraphs, not single triples or full paths. The subgraph sampler emits one row per starting entity, which gives the QA generator enough context per question."
}
```

## Stage 2

### Field Mapping

| Sample field | Role | Notes |
|---|---|---|
| `doc_id` | passthrough | preserved through entity + triple steps; dropped after subgraph sampling because the sampler produces one row per entity |
| `raw_chunk` | source text | consumed by entity + triple extractors |

Generated: `entity`, `triple`, `subgraph`, `QA_pairs`.

### Ordered Operator List

1. `KGEntityExtraction` — `raw_chunk` → `entity`
2. `KGTripleExtraction(triple_type="relation")` — `(raw_chunk, entity)` → `triple`
3. `KGEntityBasedSubgraphSampling(sampling_type="hop", hop=2)` — `triple` → `subgraph` (**row-expanding**)
4. `KGRelationTripleSubgraphQAGeneration(qa_type="set")` — `subgraph` → `QA_pairs`

### Reasoning Summary

`KGEntityBasedSubgraphSampling` with `sampling_type="hop"` and `hop=2` produces a 2-hop neighborhood per entity. This neighborhood usually contains 3-8 triples — the right granularity for a set-based QA question like "What are all the awards Einstein received?". `qa_type="num"` is for numerical-style QA; `qa_type="set"` matches the request. `"base"` is avoided because the upstream operator has a known typo bug.

Row count expands at step 3: for each input document, one output row per entity in that document.

### Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGEntityBasedSubgraphSampling,
    KGRelationTripleSubgraphQAGeneration,
)


class SubgraphQAPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/wiki_snippets.json",
            cache_path="./cache",
            file_name_prefix="subgraph_qa_step",
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
        self.subgraph_sampler = KGEntityBasedSubgraphSampling(
            llm_serving=self.llm_serving, lang="en",
        )
        self.qa_generator = KGRelationTripleSubgraphQAGeneration(
            llm_serving=self.llm_serving, qa_type="set", lang="en",
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
        self.subgraph_sampler.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key="subgraph",
            sampling_type="hop",
            hop=2,
        )
        self.qa_generator.run(
            storage=self.storage.step(),
            input_key="subgraph",
            output_key="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = SubgraphQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

### Adjustable Parameters / Caveats

- `sampling_type="bfs"` + `M=5` caps each subgraph at 5 triples (smaller, more focused)
- `sampling_type="rw"` + `num_walks=5`, `walk_length=3` for random-walk diversity instead of full neighborhoods
- `qa_type="num"` produces numerical-style QA (e.g. "How many awards did Einstein win?")
- Subgraph sampling drops the `doc_id` passthrough column; if you need it, denormalize after QA generation in pandas
- `KGRelationTripleSubgraphQAGeneration` returns `[]` on LLM parse failure — verify the cache file isn't empty
