# Stage 2 Complete Deliverable Template

## 1. Requirement Mapping
- Target:
- OP_NAME:
- KG Category:
- Constraints:
- Expected Output:
- run_input_keys (DataFrame 列名 → build_prompt 参数名):
  - `{col_name}` → `{param_name}` (type: {type})
- run_output_key (DataFrame 输出列): `{output_col}`
- Output JSON schema (来自矩阵 / INFERRED):
- Inferred Items (if any):

## 2. Prompt Design Summary
- Prompt structure: system prompt (角色 + 任务 + 约束 + 输出格式) + user prompt (仅渲染输入数据)
- build_system_prompt 返回内容: [描述角色定义与格式约束]
- build_prompt({params}) 返回内容: [描述如何渲染输入数据]
- Guardrails:
- Failure handling:
- Binding mode: DIYPromptABC（KG 算子均需 build_system_prompt + build_prompt 两个方法）
- Operator contract source: operator-compatibility-matrix.md 行 / INFERRED

## 3. Prompt Template/Config Code
```python
# full prompt template class code
```

## 4. Operator Integration Snippet + Walkthrough
```python
# operator init() snippet with prompt_template binding
```
- Sample case A (normal):
- Sample case B (edge):

## 5. Static Acceptance Result + Caveats
- [ ] input_completeness
- [ ] operator_interface_aligned
- [ ] build_system_prompt_implemented
- [ ] no_invented_params
- [ ] output_schema_explicit
- [ ] output_schema_matches_run_output_key
- [ ] output_format_matches_parser
- [ ] no_invented_kg_fields
- [ ] upstream_downstream_compatible
- [ ] walkthrough_consistent

Residual risks:
- 
