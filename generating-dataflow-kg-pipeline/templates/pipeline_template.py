"""
Standard DataFlow-KG Pipeline Template.

Follow this exact structure for every generated KG pipeline:
- subclass dataflow.pipeline.PipelineABC and call super().__init__()
- build storage + LLM serving + operator instances in __init__
- chain operators in forward() with storage.step()
- compile() then forward() in __main__

Replace CustomKGPipeline with a name that reflects the task, e.g.
TextToKGPipeline, TemporalPathQAPipeline, MultimodalKGPipeline.
"""

from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request

# Import the operators you actually need. Examples:
# from dataflow.operators.general_kg import (
#     KGEntityExtraction, KGTripleExtraction, KGTupleNormalization,
# )
# from dataflow.operators.temporal_kg import TKGTupleExtraction, TKGTuplePathQAGeneration
# from dataflow.operators.multi_model_kg import (
#     MMKGVisualTripleExtraction, MMKGEntityBasedSubgraphSampling, MMKGSubgraphBaseQAGeneration,
# )
# from dataflow.operators.hyper_relation_kg import (
#     HRKGTripleExtraction, HRKGRelationTriplePathQAGeneration,
# )


class CustomKGPipeline(PipelineABC):
    """
    Standard KG pipeline structure following DataFlow-KG api_pipelines conventions.
    """

    def __init__(self):
        super().__init__()

        # Storage configuration.
        # first_entry_file_name MUST point to a JSON array file (one top-level [...]).
        # KG pipelines use cache_type="json" by default — DO NOT switch to jsonl
        # unless the user explicitly requests it.
        self.storage = FileStorage(
            first_entry_file_name="path/to/input.json",
            cache_path="./cache",
            file_name_prefix="kg_pipeline_step",
            cache_type="json",
        )

        # LLM serving configuration.
        # key_name_of_api_key defaults to "DF_API_KEY"; KG examples set it explicitly
        # so users can swap providers via env var.
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o-mini",
            max_workers=4,
            temperature=0.0,
        )

        # If your pipeline includes multimodal KG operators, also build a VLM serving:
        # from dataflow.serving import APIVLMServing_openai
        # self.vlm_serving = APIVLMServing_openai(
        #     api_url="https://api.openai.com/v1",
        #     key_name_of_api_key="DF_API_KEY",
        #     model_name="gpt-4o-mini",
        #     max_workers=4,
        #     temperature=0.0,
        # )

        # Instantiate the operators chosen by the decision table here.
        # Example for general KG extraction:
        # self.entity_extractor = KGEntityExtraction(
        #     llm_serving=self.llm_serving, lang="en",
        # )
        # self.triple_extractor = KGTripleExtraction(
        #     llm_serving=self.llm_serving, triple_type="relation", lang="en",
        # )
        # self.triple_normalizer = KGTupleNormalization(
        #     llm_serving=self.llm_serving, lang="en",
        # )

    def forward(self):
        """
        Execute pipeline steps sequentially. Each call must pass storage=self.storage.step()
        so the previous step's output becomes the next step's input.
        """
        # Add operator.run() calls in execution order. Example:
        # self.entity_extractor.run(
        #     storage=self.storage.step(),
        #     input_key="raw_chunk",
        #     output_key="entity",
        # )
        # self.triple_extractor.run(
        #     storage=self.storage.step(),
        #     input_key="raw_chunk",
        #     input_key_meta="entity",
        #     output_key="triple",
        # )
        # self.triple_normalizer.run(
        #     storage=self.storage.step(),
        #     input_key="triple",
        #     output_key="normalized_triple",
        # )
        pass


if __name__ == "__main__":
    pipeline = CustomKGPipeline()
    pipeline.compile()
    pipeline.forward()
