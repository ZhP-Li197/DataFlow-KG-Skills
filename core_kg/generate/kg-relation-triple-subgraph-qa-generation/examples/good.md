# Example: Set-style QA over Sampled Subgraphs

## Field Flow
```
raw_chunk → entity → triple → subgraph → [KGRelationTripleSubgraphQAGeneration(qa_type="set")] → QA_pairs
```

## Complete Pipeline Code

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
            first_entry_file_name="./data/input.json",
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
            input_key="raw_chunk", output_key="entity",
        )
        self.triple_extractor.run(
            storage=self.storage.step(),
            input_key="raw_chunk", input_key_meta="entity", output_key="triple",
        )
        self.subgraph_sampler.run(
            storage=self.storage.step(),
            input_key="triple", output_key="subgraph",
            sampling_type="hop", hop=2,
        )
        self.qa_generator.run(
            storage=self.storage.step(),
            input_key="subgraph", output_key="QA_pairs",
        )


if __name__ == "__main__":
    pipeline = SubgraphQAPipeline()
    pipeline.compile()
    pipeline.forward()
```

## Notes
- Use `qa_type="num"` for counting-style questions ("How many awards did Einstein win?")
- Use `qa_type="set"` for set-membership questions ("What are all the awards Einstein won?")
- Do NOT use `qa_type="base"` — known typo bug
- An empty `QA_pairs` list means the LLM response failed to parse; check the upstream `subgraph` column for malformed triples
