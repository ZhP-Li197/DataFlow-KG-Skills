# Example: KG Entity Extraction Prompt

## 场景说明

**Target:** 从科学论文摘要中抽取命名实体，供后续三元组抽取使用。
**OP_NAME:** `KGEntityExtraction`
**KG_Category:** GENERAL_KG

---

## Round 1 采访摘要

| Block | 问题 | 回答 |
|---|---|---|
| 1 | 任务类型 | 新建 prompt_template |
| 2 | 目标算子 | `KGEntityExtraction` |
| 3 | 输出约束强度 | 强约束 JSON schema |
| 4 | 风格与语气 | 专业简洁 |
| 5 | 约束来源 | 业务规则优先 |
| 6 | KG 算子类别 | GENERAL_KG |

## Round 2 采访摘要

| Block | 问题 | 回答 |
|---|---|---|
| 1 | build_prompt 入参 | 仅 `text`（单个文本块） |
| 2 | 输出格式细节 | JSON 字符串数组，每个元素为实体原文 |
| 3 | 样例覆盖 | 1 正常 + 1 边界 |
| 4 | 验收重点 | 接口一致性优先 |
| 5 | DataFrame 列名映射 | 使用矩阵默认列名（`raw_chunk` → `entity`） |

---

## Stage 1: 决策 JSON

```json
{
  "op_name": "KGEntityExtraction",
  "kg_category": "GENERAL_KG",
  "prompt_class": "SciPaperEntityExtractionPrompt",
  "binding_mode": "DIYPromptABC",
  "arguments": ["text"],
  "run_input_keys": ["raw_chunk"],
  "run_output_key": "entity",
  "output_contract": "JSON 字符串数组：[\"实体1\", \"实体2\", ...]，空文本返回 []",
  "operator_contract_source": "operator-compatibility-matrix.md",
  "strategy": "继承 DIYPromptABC，实现 build_system_prompt（角色+格式约束）和 build_prompt（渲染文本输入）",
  "reason": "KGEntityExtraction 通过 prompt_template.build_prompt(text) 和 build_system_prompt() 调用，接口来自矩阵。输出为字符串数组，不含 entity_type 或 source 字段（矩阵明确）。",
  "static_checks": [
    "operator_interface_aligned",
    "build_system_prompt_implemented",
    "no_invented_params",
    "no_undefined_template_vars",
    "output_schema_explicit",
    "output_schema_matches_run_output_key",
    "no_invented_kg_fields"
  ]
}
```

---

## Stage 2: 完整产物

### 1. Requirement Mapping
- Target: 从科学论文摘要中抽取命名实体
- OP_NAME: `KGEntityExtraction`
- KG Category: GENERAL_KG
- Constraints: 只抽取文本中明确出现的实体，禁止推断或虚构
- Expected Output: JSON 字符串数组
- run_input_keys: `raw_chunk` → `text` (type: str)
- run_output_key: `entity`
- Output JSON schema (来自矩阵): JSON 字符串数组 `["实体1", "实体2", ...]`
- Inferred Items: 无

### 2. Prompt Design Summary
- Prompt structure: system prompt（角色 + 任务规则 + 输出格式约束）+ user prompt（仅渲染文本）
- build_system_prompt 返回内容: 实体抽取专家角色定义，明确"只抽取文本中出现的实体"规则，以及 JSON 数组格式要求
- build_prompt(text: str) 返回内容: 将 text 嵌入固定前缀框架，无其他逻辑
- Guardrails: 禁止推断、禁止添加 entity_type / source 等额外字段
- Failure handling: 文本为空或无可抽取实体时返回空数组 `[]`
- Binding mode: DIYPromptABC（KGEntityExtraction 需要 build_system_prompt + build_prompt）
- Operator contract source: operator-compatibility-matrix.md — KGEntityExtraction 行

### 3. Prompt Template Code

```python
__all__ = ['SciPaperEntityExtractionPrompt']

from dataflow.core.prompt import DIYPromptABC


class SciPaperEntityExtractionPrompt(DIYPromptABC):
    def __init__(self):
        pass

    def build_system_prompt(self) -> str:
        return """# Role
You are a named entity extraction specialist for scientific knowledge graphs.

# Task
Extract all named entities that appear explicitly in the given text. Focus on:
- Persons, organizations, locations
- Scientific concepts, methods, datasets, models
- Chemicals, genes, proteins (if present)

# Constraints
- Only extract entities that appear verbatim or near-verbatim in the text.
- Do NOT infer, generalize, or add entities not mentioned in the text.
- Do NOT add metadata fields such as entity_type or source.
- If the text contains no extractable entities, return an empty array.

# Output Format (MANDATORY)
Return ONLY a valid JSON array of strings. No explanation, no markdown fences, no extra keys.
Example: ["Entity A", "Entity B", "Entity C"]
Empty result: []
"""

    def build_prompt(self, text: str) -> str:
        return f"""Extract all named entities from the following text:

---
{text}
---
"""
```

### 4. Operator Integration Snippet + Walkthrough

```python
from your_prompts.sci_paper_entity_extraction_prompt import SciPaperEntityExtractionPrompt

# 在算子初始化中绑定自定义 prompt
entity_extractor = KGEntityExtraction(
    llm_serving=llm_serving,
    prompt_template=SciPaperEntityExtractionPrompt()
)

# run() 从 DataFrame 的 raw_chunk 列读取，写入 entity 列
entity_extractor.run(
    storage=storage.step(),
    input_key="raw_chunk",
    output_key="entity"
)
```

**Sample case A (normal):**
- Input text: `"BERT was introduced by Devlin et al. at Google in 2018. It uses a Transformer encoder architecture pre-trained on Wikipedia and BookCorpus."`
- Expected output: `["BERT", "Devlin", "Google", "Transformer", "Wikipedia", "BookCorpus"]`

**Sample case B (edge — 空文本):**
- Input text: `""`
- Expected output: `[]`
- 说明: build_system_prompt 中明确要求空结果返回 `[]`，不报错。

### 5. Static Acceptance Result + Caveats

- [x] input_completeness — Target、OP_NAME、两轮采访均已完成
- [x] operator_interface_aligned — build_prompt(text) 与矩阵 KGEntityExtraction 行一致
- [x] build_system_prompt_implemented — 已实现，返回角色+格式约束
- [x] no_invented_params — 无虚构参数
- [x] output_schema_explicit — JSON 字符串数组，schema 明确
- [x] output_schema_matches_run_output_key — 顶层输出为字符串数组，对应 run_output_key="entity"
- [x] output_format_matches_parser — 实体抽取不需要 `<subj>/<rel>` 格式，N/A
- [x] no_invented_kg_fields — 未添加 entity_type、source 等字段
- [x] upstream_downstream_compatible — raw_chunk 为典型原始文本列；entity 为 KGTripleExtraction 的上游输入
- [x] walkthrough_consistent — 两条样例行为与 output_contract 一致

Residual risks:
- 若文本语言为中文，需确认 LLM 能正确识别中文实体边界（v1 不做语言切换逻辑）。
