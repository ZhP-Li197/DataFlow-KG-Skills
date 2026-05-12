"""
DataFlow-KG Pipeline 骨架模板
使用方式：复制此文件，替换所有 <PLACEHOLDER> 为实际内容

风格：Style B（普通类，无 PipelineABC 继承）
适用：绝大多数 KG Pipeline

注意：
  - storage 在 __init__ 中声明（不要在 forward() 中创建）
  - 每个算子调用传 storage=self.storage.step()
  - 算子成员变量命名带 _stepN 后缀，N 为执行顺序
  - LLM Serving 在 __init__ 中统一声明
  - API key 通过 key_name_of_api_key 传入环境变量名，不硬编码字符串
  - 从父模块 import 算子（LazyLoader 机制，不用子包路径）
"""

import os

from dataflow.serving.api_llm_serving_request import APILLMServing_request
from dataflow.utils.storage import FileStorage

# from dataflow.operators.general_kg import (
#     KGEntityExtraction,
#     KGTripleExtraction,
#     KGTupleValidity,
#     KGTupleRemoveRepeated,
# )
# from dataflow.operators.temporal_kg import TKGTupleExtraction
# from dataflow.operators.domain_kg.medical_kg import MedKGTripleExtraction


class <PipelineClassName>:
    """
    <Pipeline 功能一句话描述>

    数据流：<input_field> → [步骤1] → <mid_field> → [步骤2] → <output_field>
    """

    def __init__(self):
        # ── Storage：在 __init__ 中声明，不在 forward() 中创建 ──────────
        self.storage = FileStorage(
            first_entry_file_name="<path/to/input.json>",
            cache_path="./cache",
            file_name_prefix="<pipeline_name>_step",
            cache_type="json",
        )

        # ── LLM Serving：在 __init__ 中统一声明 ──────────────────────────
        self.llm_serving = APILLMServing_request(
            api_url=os.environ.get("DF_API_URL", "<http://your-api-endpoint/v1/chat/completions>"),
            key_name_of_api_key="DF_API_KEY",  # 环境变量名，不是 key 本身
            model_name=os.environ.get("DF_MODEL_NAME", "<model-name>"),
            max_workers=20,  # KG Pipeline 推荐 8-20，根据 API 限速调整
        )

        # ── 算子成员变量：带 _stepN 后缀，N 为执行顺序 ──────────────────
        # self.entity_extractor_step1 = KGEntityExtraction(
        #     llm_serving=self.llm_serving,
        #     lang="en",
        # )
        # self.triple_extractor_step2 = KGTripleExtraction(
        #     llm_serving=self.llm_serving,
        #     triple_type="relation",
        #     lang="en",
        # )
        # self.validity_filter_step3 = KGTupleValidity(
        #     llm_serving=self.llm_serving,
        #     triple_type="relation",
        #     lang="en",
        # )

    def forward(self):
        """按顺序执行所有算子。每次 run() 传 storage=self.storage.step()"""

        # ── Step 1：实体抽取 ──────────────────────────────────────────────
        # self.entity_extractor_step1.run(
        #     storage=self.storage.step(),
        #     input_key="raw_chunk",
        #     output_key="entity",
        # )

        # ── Step 2：三元组抽取（input_key_meta 与上一步 output_key 对齐）─
        # self.triple_extractor_step2.run(
        #     storage=self.storage.step(),
        #     input_key="raw_chunk",
        #     input_key_meta="entity",
        #     output_key="triple",
        # )

        # ── Step 3：三元组有效性过滤 ─────────────────────────────────────
        # self.validity_filter_step3.run(
        #     storage=self.storage.step(),
        #     input_key="triple",
        #     output_key="valid_triple",
        # )

        pass


if __name__ == "__main__":
    # 运行前确保 API key 已设置（通过环境变量）：
    #   export DF_API_KEY="your-api-key"
    #   export DF_API_URL="http://your-api/v1/chat/completions"
    #   export DF_MODEL_NAME="your-model-name"

    pipeline = <PipelineClassName>()
    pipeline.forward()


# ─────────────────────────────────────────────────────────────────────────────
# Style A 参考（继承 PipelineABC，支持 compile() 特性）
# 适用：需要可视化 DAG 或断点续传的场景
# 注意：请从 DataFlow-KG 源码确认 PipelineABC 的实际 import 路径
#
# class MyKGPipeline(PipelineABC):
#     def __init__(self):
#         super().__init__()
#         self.storage = FileStorage(...)
#         self.llm_serving = APILLMServing_request(...)
#         self.op_step1 = KGEntityExtraction(llm_serving=self.llm_serving)
#         self.op_step2 = KGTripleExtraction(llm_serving=self.llm_serving, triple_type="relation")
#
#     def forward(self):
#         self.op_step1.run(storage=self.storage.step(), input_key="raw_chunk", output_key="entity")
#         self.op_step2.run(storage=self.storage.step(), input_key="raw_chunk",
#                           input_key_meta="entity", output_key="triple")
#
# ─────────────────────────────────────────────────────────────────────────────
