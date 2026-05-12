# Example: GraphRAG Evidence-Constrained Answer Prompt

## 场景说明

**Target:** 基于检索到的知识图谱子图（subgraph）生成答案，答案必须严格来自证据，禁止使用外部知识。
**OP_NAME:** `KGGraphRAGGetAnswer`
**KG_Category:** GRAPH_RAG

---

## Round 1 采访摘要

| Block | 问题 | 回答 |
|---|---|---|
| 1 | 任务类型 | 新建 prompt_template |
| 2 | 目标算子 | `KGGraphRAGGetAnswer` |
| 3 | 输出约束强度 | 强约束（答案必须有据可查，不可推断） |
| 4 | 风格与语气 | 专业简洁 |
| 5 | 约束来源 | 业务规则优先（证据约束是核心需求） |
| 6 | KG 算子类别 | GRAPH_RAG |

## Round 2 采访摘要

| Block | 问题 | 回答 |
|---|---|---|
| 1 | build_prompt 入参 | `subgraph_prompt`（已序列化的子图证据字符串） |
| 2 | 输出格式细节 | 纯文本答案，无 JSON 包装 |
| 3 | 样例覆盖 | 1 正常 + 1 边界（子图无相关信息） |
| 4 | 验收重点 | 接口一致性 + 证据约束落地 |
| 5 | DataFrame 列名映射 | 使用矩阵默认列名（`question`, `subgraph_prompt` → `answer`） |

---

## Stage 1: 决策 JSON

```json
{
  "op_name": "KGGraphRAGGetAnswer",
  "kg_category": "GRAPH_RAG",
  "prompt_class": "GraphRAGEvidenceConstrainedAnswerPrompt",
  "binding_mode": "DIYPromptABC",
  "arguments": ["subgraph_prompt"],
  "run_input_keys": ["question", "subgraph_prompt"],
  "run_output_key": "answer",
  "output_contract": "纯文本答案字符串，若无相关证据则输出固定拒绝语",
  "operator_contract_source": "operator-compatibility-matrix.md",
  "strategy": "继承 DIYPromptABC，build_system_prompt 强制证据约束，build_prompt 渲染子图证据",
  "reason": "KGGraphRAGGetAnswer 使用 build_prompt(subgraph_prompt) 渲染证据，build_system_prompt 定义角色和证据规则。run_input_keys 含 question 和 subgraph_prompt，但 build_prompt 只接收 subgraph_prompt（question 由算子内部处理）。输出为纯文本，对应 run_output_key=answer（矩阵确认）。",
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
- Target: 基于 KG 子图证据生成答案，禁止幻觉
- OP_NAME: `KGGraphRAGGetAnswer`
- KG Category: GRAPH_RAG
- Constraints: 答案必须完全基于提供的子图证据；若证据不足，必须明确说明无法回答
- Expected Output: 纯文本答案字符串
- run_input_keys: `question` (算子内部使用), `subgraph_prompt` → `subgraph_prompt` (type: str)
- run_output_key: `answer`
- Output JSON schema (来自矩阵): 纯文本答案（无 JSON 包装）
- Inferred Items: 无

### 2. Prompt Design Summary
- Prompt structure: system prompt（证据约束角色 + 禁止规则 + 拒答模板）+ user prompt（渲染子图证据）
- build_system_prompt 返回内容: GraphRAG 答题专家角色，强制"只能从提供的证据回答"规则，以及无相关证据时的拒答固定语
- build_prompt(subgraph_prompt: str) 返回内容: 将子图证据字符串嵌入固定前缀，供 LLM 阅读
- Guardrails: 禁止使用训练数据知识、禁止推断、禁止补充未出现的信息
- Failure handling: 子图无相关信息时，输出固定拒答语 `"Based on the provided knowledge graph evidence, I cannot answer this question."`
- Binding mode: DIYPromptABC（KGGraphRAGGetAnswer 需要 build_system_prompt + build_prompt）
- Operator contract source: operator-compatibility-matrix.md — KGGraphRAGGetAnswer 行

### 3. Prompt Template Code

```python
__all__ = ['GraphRAGEvidenceConstrainedAnswerPrompt']

from dataflow.core.prompt import DIYPromptABC


class GraphRAGEvidenceConstrainedAnswerPrompt(DIYPromptABC):
    def __init__(self):
        pass

    def build_system_prompt(self) -> str:
        return """# Role
You are a knowledge graph question answering assistant. Your answers must be grounded exclusively in the provided knowledge graph evidence.

# Task
Answer the user's question using ONLY the facts present in the provided subgraph evidence. Do not use any external knowledge, background knowledge, or information from your training data.

# Constraints
- Every claim in your answer must be directly traceable to a triple or fact in the provided evidence.
- Do NOT infer, extrapolate, or fill gaps with general knowledge.
- Do NOT mention entities, relations, or facts that do not appear in the evidence.
- If the evidence is irrelevant or insufficient to answer the question, respond with the exact refusal phrase below.

# Output Format (MANDATORY)
Respond with a concise factual answer in plain text (no JSON, no markdown).
If evidence is insufficient: respond with exactly — "Based on the provided knowledge graph evidence, I cannot answer this question."
"""

    def build_prompt(self, subgraph_prompt: str) -> str:
        return f"""Knowledge Graph Evidence:
---
{subgraph_prompt}
---

Answer the question based solely on the evidence above.
"""
```

### 4. Operator Integration Snippet + Walkthrough

```python
from your_prompts.graphrag_evidence_constrained_answer_prompt import GraphRAGEvidenceConstrainedAnswerPrompt

# 在算子初始化中绑定自定义 prompt
answer_generator = KGGraphRAGGetAnswer(
    llm_serving=llm_serving,
    prompt_template=GraphRAGEvidenceConstrainedAnswerPrompt()
)

# run() 从 question 和 subgraph_prompt 列读取，写入 answer 列
answer_generator.run(
    storage=storage.step(),
    input_keys=["question", "subgraph_prompt"],
    output_key="answer"
)
```

**Sample case A (normal — 有相关证据):**
- subgraph_prompt: `"<subj> BERT <obj> Google <rel> developed_by\n<subj> BERT <obj> 2018 <rel> released_in\n<subj> BERT <obj> Transformer <rel> based_on"`
- question (context): `"When was BERT developed and by whom?"`
- Expected answer: `"BERT was developed by Google and released in 2018."`

**Sample case B (edge — 证据不足):**
- subgraph_prompt: `"<subj> GPT-4 <obj> OpenAI <rel> developed_by"`
- question (context): `"What is the capital of France?"`
- Expected output: `"Based on the provided knowledge graph evidence, I cannot answer this question."`
- 说明: system prompt 中的拒答模板确保此场景有确定性输出。

### 5. Static Acceptance Result + Caveats

- [x] input_completeness — Target、OP_NAME、两轮采访均已完成
- [x] operator_interface_aligned — build_prompt(subgraph_prompt) 与矩阵 KGGraphRAGGetAnswer 行一致
- [x] build_system_prompt_implemented — 已实现，包含证据约束和拒答规则
- [x] no_invented_params — 无虚构参数
- [x] output_schema_explicit — 纯文本，明确拒答固定语（确定性输出）
- [x] output_schema_matches_run_output_key — 纯文本对应 run_output_key="answer"
- [x] output_format_matches_parser — answer 为文本输出，无 triple 格式要求，N/A
- [x] no_invented_kg_fields — 无虚构字段
- [x] upstream_downstream_compatible — subgraph_prompt 由 KGGraphRAGSubgraphRetrieval 输出；answer 为终端输出列
- [x] walkthrough_consistent — 两条样例行为与 output_contract 一致

Residual risks:
- LLM 可能在证据高度相关但措辞稍有歧义时给出部分推断。建议在实际部署后增加后处理校验。
