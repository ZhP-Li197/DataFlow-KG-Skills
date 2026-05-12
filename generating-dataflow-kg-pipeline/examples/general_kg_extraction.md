# Example: General KG Extraction from Text

## User Request

```
Target: Extract relation triples from short biographical paragraphs and normalize them.
Sample file: ./data/bios.json
Expected outputs: normalized_triple
```

## Sample Data

```json
[
  {"doc_id": "bio-1", "raw_chunk": "Marie Curie was a physicist and chemist. She was born in Warsaw. Pierre Curie was her husband and research partner."},
  {"doc_id": "bio-2", "raw_chunk": "Alan Turing studied mathematics at Cambridge. He worked at Bletchley Park during World War II as a cryptanalyst."}
]
```

## Stage 1: Operator Decision

```json
{
  "kg_type": "general",
  "task": "extraction",
  "ops": ["KGEntityExtraction", "KGTripleExtraction", "KGTupleNormalization"],
  "field_flow": "raw_chunk -> entity -> triple -> normalized_triple",
  "reason": "Sample is plain biographical text with no temporal qualifiers, no images, no multi-argument facts — general KG fits. User asked for normalized triples, so the chain ends with KGTupleNormalization."
}
```

## Stage 2

### Field Mapping

| Sample field | Role | Notes |
|---|---|---|
| `doc_id` | passthrough | preserved across steps |
| `raw_chunk` | source text | consumed by entity + triple extractors |

Generated: `entity` (str), `triple` (List[str]), `normalized_triple` (List[str]).

### Ordered Operator List

1. `KGEntityExtraction(llm_serving, lang="en")` — `input_key="raw_chunk"` → `output_key="entity"`
2. `KGTripleExtraction(llm_serving, triple_type="relation", lang="en")` — `input_key="raw_chunk"`, `input_key_meta="entity"` → `output_key="triple"`
3. `KGTupleNormalization(llm_serving, lang="en")` — `input_key="triple"` → `output_key="normalized_triple"`

### Reasoning Summary

`KGTripleExtraction` requires the `entity` column to anchor the LLM, so `KGEntityExtraction` must run first. `triple_type="relation"` is chosen because biographical text describes relations (was, born_in, married_to) rather than enumerated attributes. The last step canonicalizes synonymous relations (e.g. `is_married_to` ↔ `was_married_to`).

### Complete Pipeline Code

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGTupleNormalization,
)


class BiographyKGExtractionPipeline(PipelineABC):
    def __init__(self):
        super().__init__()

        self.storage = FileStorage(
            first_entry_file_name="./data/bios.json",
            cache_path="./cache",
            file_name_prefix="bio_kg_step",
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
        self.triple_extractor = KGTripleExtraction(
            llm_serving=self.llm_serving,
            triple_type="relation",
            lang="en",
        )
        self.triple_normalizer = KGTupleNormalization(
            llm_serving=self.llm_serving,
            lang="en",
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
        self.triple_normalizer.run(
            storage=self.storage.step(),
            input_key="triple",
            output_key="normalized_triple",
        )


if __name__ == "__main__":
    pipeline = BiographyKGExtractionPipeline()
    pipeline.compile()
    pipeline.forward()
```

### Adjustable Parameters / Caveats

- `lang="zh"` switches to Chinese prompts for both extractors and the normalizer
- `triple_type="attribute"` if the text describes properties rather than relations (e.g. product specs)
- Skipping `KGTupleNormalization` is acceptable when downstream consumes raw triples directly
- `KGEntityExtraction` silently drops rows shorter than 10 chars, longer than 200000 chars, with <2 sentence terminators, or with >30% special chars; verify the sample passes these gates
