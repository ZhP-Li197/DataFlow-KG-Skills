# Input Schema (Prompt Template Builder)

## Required Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `Target` | `str` | 业务目标与任务描述 | `将推理题过滤器改造成金融问题过滤器` |
| `OP_NAME` | `str` | 复用的目标算子类名 | `ReasoningQuestionFilter` |

## Optional Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `Constraints` | `str` | `""` | 语气、边界、禁用项、风险约束 |
| `Expected Output` | `str` | `""` | 期望输出格式（建议给 JSON schema） |
| `Arguments` | `list[str]` | `[]` | prompt 参数列表，示例：`["min_len=10", "drop_na=true"]` |
| `Sample Cases` | `list[str]` | `[]` | 1-3 条示例输入与期望行为 |
| `Tone/Style` | `str` | `"professional"` | 语言风格偏好 |
| `Validation Focus` | `str` | `"static-checklist"` | 验收重点 |

## Normalization Rules

1. `Arguments` 支持逗号、空格、换行输入，统一归一化为 `list[str]`。
2. `OP_NAME` 需去除多余空白并保持大小写。
3. `Sample Cases` 至少保留一条代表性正常样例；无样例时由采访阶段补齐。
4. `Expected Output` 为空时，允许基于现有 prompt 案例推断输出约束，但必须在 Stage 1 标注“推断项”。

## Missing Field Policy

- 缺少 `Target` 或 `OP_NAME`：必须追问，不能继续。
- 缺少 `Arguments`：默认 `[]`，但需在 Stage 1 说明是否推断。
- 缺少 `Expected Output`：允许默认，但 Stage 2 必须给出明确输出格式声明。

## Contradiction Policy

以下冲突必须追问确认：
- `Expected Output` 声称 JSON，但又禁止结构化输出。
- `Arguments` 与 `build_prompt` 变量引用不一致。
- `Constraints` 要求与算子接口冲突（如要求不存在的输入字段）。
- `run_output_key` 值与 KG 输出字段规范不符（例如声明 `entity_type` 但算子输出的是 `entity` 字段）：必须追问或标注风险。
- `build_prompt` 参数名与 `run_input_keys` 对应列名语义明显不符：必须追问。

## KG-Specific Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `KG_Category` | `str` | `"GENERAL_KG"` | GENERAL_KG / TEMPORAL_KG / HRKG / CSKG / GRAPH_RAG / GRAPH_REASONING / FinKG / MedKG / GeoKG / LegalKG / SchoKG |
| `run_input_keys` | `list[str]` | `[]` | DataFrame column names consumed by operator `run()`. Positionally maps to `build_prompt` parameters. Example: `["raw_chunk", "entity"]` |
| `run_output_key` | `str` | `""` | DataFrame column name written by `run()`. Constrains output JSON field names. |

## KG Field Mapping Rule

`run_input_keys[i]` maps positionally to `build_prompt` parameter i.
`run_output_key` constrains what top-level key name the prompt must instruct the LLM to output.

**FORBIDDEN** output field names (unless explicitly listed in `operator-compatibility-matrix.md`):
- Entity extraction → output is a JSON array of strings (NOT `entity_type`, NOT `source`)
- Triple extraction → top-level key must be `triple`, values use `<subj> X <obj> Y <rel> Z` format
- QA generation → top-level key must be `QA_pairs`
- Temporal extraction → top-level key must be `tuple`

Missing field policy (KG additions):
- 缺少 `OP_NAME` 且无法从 `KG_Category` 推断：必须追问。
- `run_input_keys` 与 `build_prompt` 参数语义明显不符：Stage 1 标注 `[INFERRED]` 并请求确认。
