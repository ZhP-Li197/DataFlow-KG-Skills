---
name: prompt-template-builder
description: Build reusable DataFlow-KG DIYPromptABC prompt_template classes for existing KG operators. Generates both build_prompt() and build_system_prompt() methods aligned to operator interface contracts, with two-round AskUserQuestion intake, two-stage auditable outputs, and KG-specific static acceptance checks. Trigger when users ask to generate/rewrite/optimize prompt_template for KG operators including GENERAL_KG, TEMPORAL_KG, GRAPH_RAG, HRKG, COMMONSENSE_KG, and domain KG operators (FinKG, MedKG, GeoKG, LegalKG, SchoKG).
version: 1.1.0
---

# Prompt Template Builder

生成可复用、可审计的 DataFlow-KG `prompt_template` 初版产物，聚焦"KG算子契约对齐 + 提示词定制 + 静态验收"。

## Goal

当用户给出 `Target` 与 `OP_NAME` 时，本 skill 必须：
1. 查阅 `references/operator-compatibility-matrix.md`，解析目标算子的接口契约（`build_prompt` 参数、`run_input_keys`、`run_output_key`、输出 schema）。
2. 生成同时实现 `build_system_prompt()` 与 `build_prompt(**fields)` 的 `DIYPromptABC` 子类。
3. 输出可审计的两阶段结果（决策 JSON + 完整产物）。
4. 使用含 KG 专属检查项的静态验收清单完成质量门控。

## Usage

```bash
/prompt-template-builder
/prompt-template-builder --spec path/to/prompt_spec.json
```

## Scope

### In Scope

- 针对已有 KG 算子的 prompt_template 新建或改写。
- 通过 AskUserQuestion 两轮结构化采集需求。
- 生成标准化 DIYPromptABC 子类（含 `build_system_prompt` 和 `build_prompt`）、集成示例、静态验收结果。
- 接收用户反馈并进行定向改写（`revise_with_feedback` 风格）。

### Out of Scope (v1)

- 自动子进程执行测试脚本。
- 自动运行 Gradio UI 或流水线脚本。
- 自动提交代码或发布。

## Backward Compatibility Note

v1.1 将 `binding_mode` 统一为 `DIYPromptABC`，移除 `FormatStrPrompt` 和 `system_user_prompt` 作为生成目标。
原有非 KG 算子（如 `PromptedGenerator`、`ReasoningQuestionFilter`）仍可使用本 skill，但模板类型统一为 `DIYPromptABC`。

## Input Contract (MANDATORY)

按结构化字段接收输入：

```text
Target: [业务目标/场景]
OP_NAME: [目标算子类名]
KG_Category: [可选，如 GENERAL_KG / TEMPORAL_KG / GRAPH_RAG 等]
run_input_keys: [可选，DataFrame列名列表，如 raw_chunk, entity]
run_output_key: [可选，DataFrame输出列名]
Constraints: [可选，边界/禁用项/风格约束]
Expected Output: [可选，输出格式约束]
Arguments: [可选，build_prompt参数列表]
Sample Cases: [可选，1-3条输入/期望行为]
```

详细字段定义见：
- `references/input-schema.md`

## Working Modes

### Mode A: AskUserQuestion Interview (default)

固定两阶段批量提问：
- Round 1: 结构层（目标、算子、输出契约、约束、KG类别）
- Round 2: 实现层（参数签名、DataFrame列名映射、边界样例、验收偏好）

规则：
- 每个问题块提供推荐选项 + 简短理由。
- 若 OP_NAME 在矩阵中，直接使用矩阵填充接口字段，不追问接口细节。
- 只在高影响缺失/冲突时追问（包括 OP_NAME 不在矩阵中时追问 run_input_keys）。
- 能映射到结构化字段就不提"游离问题"。

详见：
- `references/askuserquestion-rounds.md`

### Mode B: Direct Spec

若用户已提供完整 spec，跳过采访，直接进入生成与验收。

## Required Workflow

```text
Prompt Template Builder Progress:
- [ ] Step 1: Load references (含 operator-compatibility-matrix.md) 并解析用户输入
- [ ] Step 2: 选择模式（Interview 或 Direct Spec）
- [ ] Step 3: 查阅矩阵解析算子契约（build_prompt 参数、run_input_keys、output schema）
- [ ] Step 4: 基于契约构建 prompt 草稿
- [ ] Step 5: 输出 Stage 1 决策 JSON（含 kg_category、binding_mode、run_input_keys、run_output_key）
- [ ] Step 6: 输出 Stage 2 完整产物（含 build_system_prompt 和 build_prompt 两个方法）
- [ ] Step 7: 执行静态验收清单（含 Section F KG 专属检查）
- [ ] Step 8: 如有用户反馈，执行定向改写并重新验收
```

## Mandatory Rules

1. **Operator Interface Alignment**
   - 必须查阅 `references/operator-compatibility-matrix.md`。
   - 若 OP_NAME 在矩阵中，以矩阵为单一真源，不得与矩阵冲突。
   - 不得虚构 `OP_NAME` 的构造参数或 `run` 参数。
   - 当不同文档冲突时，以矩阵（或目标算子签名说明）作为单一真源。

2. **Prompt Class Contract**
   - 所有输出统一为 `DIYPromptABC` 子类（`from dataflow.core.prompt import DIYPromptABC`）。
   - **必须同时实现 `build_system_prompt(self) -> str` 和 `build_prompt(self, ...) -> str`**。
   - `build_system_prompt` 承载：角色定义、任务说明、边界约束、输出格式约束（系统级内容）。
   - `build_prompt` 仅渲染用户输入数据，不重复系统约束。
   - 保留 `__all__` 导出。
   - DIY 类名使用 `PascalCase + Prompt`。

3. **Output Determinism**
   - 若用户指定输出格式，Prompt 中必须给出明确强约束（字段名、类型、取值范围）。
   - 禁止仅描述"尽量输出 JSON"而不定义 schema。
   - 输出 schema 必须与矩阵中的 Output Schema 列一致（不允许自行发明字段名）。

4. **Field/Argument Safety**
   - `build_prompt` 中引用的变量必须来自显式参数或常量。
   - 不允许在模板中引用未声明变量。
   - 不允许虚构 KG 输出字段（如 `entity_type`、`source`、`evidence` 等），除非矩阵明确列出。

5. **Two-Stage Output (Required)**
   - 必须先输出 Stage 1 决策 JSON（含新增 KG 字段）。
   - 再输出 Stage 2 完整产物。

6. **Validation Gate**
   - Stage 2 必须包含静态验收结果，引用 `references/acceptance-checklist.md`（含 Section F）。

## Output Contract (MANDATORY)

详见：
- `references/output-contract.md`
- `templates/decision_json_template.md`
- `templates/final_response_template.md`

## Progressive Disclosure Assets

- `references/input-schema.md`: 输入字段、默认值、归一化规则
- `references/operator-compatibility-matrix.md`: KG 算子接口契约矩阵（单一真源）
- `references/output-contract.md`: 两阶段输出规范与失败态
- `references/gotchas.md`: 常见失败模式（含 KG 专属 G7-G10）
- `references/acceptance-checklist.md`: 静态验收门槛（含 Section F KG 专属检查）
- `references/askuserquestion-rounds.md`: 两轮采访模板
- `templates/diy_prompt_kg_template.py.tmpl`: KG 版 DIYPromptABC 模板（含 build_system_prompt）
- `templates/prompt_class_template.py.tmpl`: 通用 DIYPromptABC 模板（兼容非 KG 算子）
- `examples/`: 典型场景走查（含 KG 专属示例）

## Notes

- v1.1 新增 KG 算子矩阵支持，`build_system_prompt` 强制实现，Section F 验收检查。
- v1 使用"静态验收 + 示例走查"闭环；后续版本可扩展为自动子进程测试。
- 若用户反馈不满意，执行定向改写并重复 Stage 1/Stage 2 + 静态验收。
