# Acceptance Checklist (Static + Walkthrough)

## A. Input & Interview Completeness

- [ ] `Target` 与 `OP_NAME` 已确认。
- [ ] 两阶段 AskUserQuestion 已执行（或明确走 Direct Spec）。
- [ ] 高影响缺失/冲突项已追问并解决。
- [ ] `run_input_keys` 与 `run_output_key` 已确认（来自矩阵或用户补充）。

## B. Interface Safety

- [ ] `build_prompt` 参数与算子调用契约一致（对照 `operator-compatibility-matrix.md`）。
- [ ] `build_prompt` 参数顺序与 `run_input_keys` 顺序一致。
- [ ] `build_system_prompt()` 已实现（所有 KG 算子均调用此方法）。
- [ ] `prompt_template` 类型为 `DIYPromptABC` 子类。
- [ ] 未虚构算子参数或字段。
- [ ] 模板变量全部已声明（无未定义引用）。

## C. Prompt Quality

- [ ] Prompt 包含角色、任务、边界条件（system prompt 中）。
- [ ] 输出格式可机器校验（字段名/类型明确）。
- [ ] 输出格式与矩阵中的 Output Schema 列一致（标签语法、字段名均匹配）。
- [ ] 失败场景有明确处理约束（例如 `error_type`）。

## D. Output Contract

- [ ] Stage 1 决策 JSON 完整（含 `binding_mode`, `kg_category`, `run_input_keys`, `run_output_key`, `operator_contract_source`）。
- [ ] Stage 2 五段产物完整。
- [ ] Stage 2 给出静态验收结果与剩余风险。

## E. Example Walkthrough

- [ ] 至少 1 条正常样例走查。
- [ ] 至少 1 条边界/失败样例走查。
- [ ] 示例行为与输出契约一致。

## Pass Rule

- A/B/C/D/F 全部通过才视为可交付（v1.1 新增 F）。
- E 至少通过前两项（v1 可选第 3 项为”建议通过”）。

## F. KG-Specific Checks

- [ ] `build_system_prompt_implemented`: 类定义了 `def build_system_prompt(self) -> str`。
- [ ] `output_schema_matches_run_output_key`: prompt 输出的 JSON 顶层字段名与算子 `run_output_key` 一致。
- [ ] `output_format_matches_parser`: triple/tuple 输出使用 `<subj>/<obj>/<rel>` 标签语法（若适用）。
- [ ] `no_invented_kg_fields`: 未虚构非矩阵字段（如 `entity_type`、`source`、`evidence`、`timestamp` 等）。
- [ ] `upstream_downstream_compatible`: `run_input_keys` 列名在典型 KG 流水线中由正确的上游算子输出（例如 `entity` 由 `KGEntityExtraction` 输出，`triple` 由 `KGTripleExtraction` 输出）。
