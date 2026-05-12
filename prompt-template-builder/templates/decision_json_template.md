# Stage 1 Decision JSON Template

```json
{
  "op_name": "{{OP_NAME}}",
  "kg_category": "{{KG_CATEGORY}}",
  "prompt_class": "{{PROMPT_CLASS_NAME}}",
  "binding_mode": "DIYPromptABC",
  "arguments": ["{{ARG_1}}", "{{ARG_2}}"],
  "run_input_keys": ["{{DF_COL_1}}", "{{DF_COL_2}}"],
  "run_output_key": "{{DF_OUTPUT_COL}}",
  "output_contract": "{{OUTPUT_CONTRACT}}",
  "operator_contract_source": "{{operator-compatibility-matrix.md | INFERRED}}",
  "strategy": "{{STRATEGY}}",
  "reason": "{{WHY_THIS_DESIGN}}",
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

## Fill Rules

- `kg_category` 必须是以下之一：GENERAL_KG、TEMPORAL_KG、HRKG、CSKG、GRAPH_RAG、GRAPH_REASONING、FinKG、MedKG、GeoKG、LegalKG、SchoKG。
- `binding_mode` 在本 skill 版本中固定为 `"DIYPromptABC"`。
- `arguments` 必须与 `build_prompt` 实际参数完全一致（参数名和顺序）。
- `run_input_keys` 必须是 DataFrame 列名（不是 `build_prompt` 参数名），与 `arguments` 位置一一对应。
- `run_output_key` 必须是 `run()` 写入 DataFrame 的列名。
- `operator_contract_source`：OP_NAME 在矩阵中时填 `"operator-compatibility-matrix.md"`，否则填 `"INFERRED"`。
- `output_contract` 必须直接引用矩阵中的 Output Schema，不得使用模糊描述或自行设计字段名。
- `reason` 需覆盖"算子复用依据 + 约束映射 + 风险处理 + 推断项说明（如有）"。
