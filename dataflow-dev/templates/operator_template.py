"""
DataFlow-KG 算子骨架模板
使用方式：复制此文件，替换所有 <PLACEHOLDER> 为实际内容

模板类型：通用 KG 算子（支持 LLM 驱动和非 LLM 两种模式）
"""

import json
import re
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from tqdm import tqdm

from dataflow import get_logger
from dataflow.core import OperatorABC, LLMServingABC
from dataflow.core.prompt import prompt_restrict
from dataflow.utils.registry import OPERATOR_REGISTRY
from dataflow.utils.storage import DataFlowStorage

# from dataflow.prompts.core_kg.<module> import <PromptClassName>


# @prompt_restrict(<PromptClassName>)  # 有 prompt 限制时取消注释，必须在最外层
@OPERATOR_REGISTRY.register()
class <OperatorClassName>(OperatorABC):
    """
    <算子功能一句话描述>

    类型：<filter / generate / refinement / eval>
    模块：<general_kg / temporal_kg / graph_reasoning / graph_rag / domain_kg / ...>
    """

    def __init__(
        self,
        # llm_serving: LLMServingABC,
        # lang: str = "en",
        # seed: int = 0,
    ):
        # KG 算子直接调用 get_logger()，不调用 super().__init__()
        self.logger = get_logger()

        # self.llm_serving = llm_serving
        # self.lang = lang
        # self.prompt_template = <PromptClassName>(lang=lang)

    @staticmethod
    def get_desc(lang: str = "en") -> tuple:
        """返回算子描述 tuple（必须同时支持 zh / en，返回 3 元素 tuple）"""
        if lang == "zh":
            return (
                "<算子中文功能描述，一句话>",
                "<算子核心能力说明>",
                "<输入输出列说明，如：输入列 triple 为三元组列表，输出列 valid_triple 为过滤后的列表>",
            )
        return (
            "<Operator English description, one sentence>",
            "<Core capability>",
            "<Input/output column description, e.g.: Takes triple (List[str]) as input and outputs valid_triple (List[str])>",
        )

    def process_batch(
        self,
        texts: List[str],
        # entity_lists: List[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """LLM 批处理逻辑。与 run() 分离，便于独立测试。"""
        results = []
        for text in tqdm(texts, desc="Processing"):
            user_inputs = [self.prompt_template.build_prompt(text)]
            system_prompt = self.prompt_template.build_system_prompt()
            responses = self.llm_serving.generate_from_input(
                user_inputs=user_inputs,
                system_prompt=system_prompt,
            )
            parsed = self._parse_llm_response(responses[0])
            results.append({"<output_key>": parsed})
        return results

    def _parse_llm_response(self, response: str) -> List[Any]:
        """解析 LLM 返回值，带容错（参考 dev_notes.md §1.8 模板 A/B/C/D）"""
        try:
            cleaned = re.sub(r"```json|```", "", response).strip()
            return json.loads(cleaned).get("<json_key>", [])
        except Exception as e:
            self.logger.warning(f"Failed to parse LLM response: {e}")
            return []

    def _validate_dataframe(self, dataframe: pd.DataFrame):
        """检查输入列存在，输出列不冲突（run() 开头必须调用）"""
        required_keys = [self.input_key]
        # required_keys = [self.input_key, self.input_key_meta]
        forbidden_keys = [self.output_key]

        missing = [k for k in required_keys if k not in dataframe.columns]
        conflict = [k for k in forbidden_keys if k in dataframe.columns]

        if missing:
            raise ValueError(f"Missing required column(s): {missing}")
        if conflict:
            raise ValueError(
                f"The following column(s) already exist and would be overwritten: {conflict}"
            )

    def run(
        self,
        storage: DataFlowStorage,
        input_key: str = "<default_input_col>",
        # input_key_meta: str = "<meta_col>",
        output_key: str = "<default_output_col>",
    ):
        self.input_key = input_key
        # self.input_key_meta = input_key_meta
        self.output_key = output_key

        dataframe = storage.read("dataframe")
        self._validate_dataframe(dataframe)

        texts = dataframe[self.input_key].tolist()
        # entity_lists = dataframe[self.input_key_meta].tolist()

        # ── LLM 驱动算子 ──────────────────────────────────────────────────
        # outputs = self.process_batch(texts)
        # dataframe[self.output_key] = [o.get(output_key, []) for o in outputs]

        # ── 非 LLM 算子：直接处理 ────────────────────────────────────────
        # results = [self._process(t) for t in texts]
        # dataframe[self.output_key] = results

        output_file = storage.write(dataframe)
        self.logger.info(f"Results saved to {output_file}")

        return [output_key]

    # def _process(self, text: str):
    #     """非 LLM 处理逻辑"""
    #     raise NotImplementedError
