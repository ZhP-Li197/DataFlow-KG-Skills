"""
DataFlow-KG Prompt 骨架模板
使用方式：复制此文件，替换所有 <PLACEHOLDER> 为实际内容

说明：
  - 标准 Prompt：继承 PromptABC（受 @prompt_restrict 白名单限制）
  - DIY Prompt：继承 DIYPromptABC（绕过白名单，更灵活）
  - 必须加 @PROMPT_REGISTRY.register() 装饰器
  - 必须同时实现 build_system_prompt() 和 build_prompt()
  - system prompt 中必须明确 JSON 输出格式及字段标签
  - 若算子需限制 Prompt 类型：在算子类上用 @prompt_restrict(MyKGPrompt)
    注意：@prompt_restrict 必须在最外层，位于 @OPERATOR_REGISTRY.register() 上方
"""

import json
import textwrap

from dataflow.core.prompt import PromptABC, DIYPromptABC
from dataflow.utils.registry import PROMPT_REGISTRY


@PROMPT_REGISTRY.register()
class <PromptClassName>(PromptABC):
    """
    <Prompt 功能一句话描述>

    配合 <OperatorClassName> 使用。
    三元组格式：关系型用 <subj>/<rel>/<obj>，属性型用 <entity>/<attribute>/<value>
    """

    def __init__(self, lang: str = "en"):
        self.lang = lang

    def build_system_prompt(self) -> str:
        """
        构建系统提示词。
        KG 结构化输出必须在此处明确 JSON 格式及字段标签。
        """
        if self.lang == "zh":
            return textwrap.dedent("""\
                你是一个知识图谱构建专家。
                请从给定文本中抽取<关系型/属性型>三元组，以 JSON 格式返回。

                输出格式（严格遵守）：
                {
                    "triple": [
                        "<subj>主语<subj> <rel>关系<rel> <obj>宾语<obj>",
                        ...
                    ]
                }

                注意：
                - 每个三元组用标签字符串表示，不要用列表或其他格式
                - 仅输出 JSON，不要添加任何解释
            """)
        return textwrap.dedent("""\
            You are a knowledge graph construction expert.
            Extract <relation/attribute> triples from the given text and return them in JSON format.

            Output format (strictly follow):
            {
                "triple": [
                    "<subj>subject<subj> <rel>relation<rel> <obj>object<obj>",
                    ...
                ]
            }

            Rules:
            - Represent each triple as a tagged string, not a list
            - Output JSON only, no explanations
        """)

    def build_prompt(
        self,
        text: str,
        # entity_list: list = None,
    ) -> str:
        """构建用户输入部分的 Prompt"""
        # if entity_list:
        #     entity_str = json.dumps(entity_list, ensure_ascii=False)
        #     return f"文本：\n{text}\n\n合法实体列表：\n{entity_str}"
        return f"文本：\n{text}" if self.lang == "zh" else f"Text:\n{text}"


# ─── DIY Prompt（绕过 @prompt_restrict 白名单）────────────────────────────────
#
# @PROMPT_REGISTRY.register()
# class <DIYPromptClassName>(DIYPromptABC):
#
#     def __init__(self, lang: str = "en"):
#         self.lang = lang
#
#     def build_system_prompt(self) -> str:
#         return "你是一个自定义知识图谱处理助手。"
#
#     def build_prompt(self, text: str) -> str:
#         return f"请处理：{text}"
#
# ─────────────────────────────────────────────────────────────────────────────


# ─── 在算子中绑定 Prompt 类型的用法 ──────────────────────────────────────────
#
# @prompt_restrict(<PromptClassName>)       # 外层
# @OPERATOR_REGISTRY.register()            # 内层，紧贴类定义
# class <OperatorClassName>(OperatorABC):
#     def __init__(self, llm_serving, lang="en",
#                  prompt_template: <PromptClassName> = None):
#         self.logger = get_logger()
#         self.llm_serving = llm_serving
#         self.prompt_template = prompt_template or <PromptClassName>(lang=lang)
#
# ─────────────────────────────────────────────────────────────────────────────


# ─── 三元组格式速查 ───────────────────────────────────────────────────────────
#
# 关系型三元组：  "<subj>主语<subj> <rel>关系<rel> <obj>宾语<obj>"
# 属性型三元组：  "<entity>实体<entity> <attribute>属性<attribute> <value>值<value>"
# 时序四元组：    "<subj>X<subj> <obj>Y<obj> <rel>Z<rel> <time>T<time>"（无时间填 NA）
#
# JSON key 由具体 Prompt 业务决定（如 "triple"、"valid_triple"、"entity" 等）
# ─────────────────────────────────────────────────────────────────────────────
