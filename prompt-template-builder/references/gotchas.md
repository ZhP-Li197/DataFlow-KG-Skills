# Gotchas (Prompt Template Builder)

统一结构：现象 / 根因 / 检测 / 修复 / 预防。

## G1: build_prompt 参数与算子调用不一致

- 现象: 运行时报 `TypeError`（参数个数或命名不匹配）。
- 根因: 未对齐 `OP_NAME` 实际调用 `prompt_template.build_prompt(...)` 的参数。
- 检测: 静态检查“参数名一致性”失败。
- 修复: 按算子调用点重写 `build_prompt` 签名。
- 预防: 先做接口对齐再写 prompt 文案。

## G2: 输出格式描述模糊

- 现象: 模型输出字段漂移，难以稳定解析。
- 根因: Prompt 只写“返回 JSON”，但没有 schema。
- 检测: 验收清单 `output_schema_explicit` 失败。
- 修复: 明确字段名、类型、取值约束与错误字段。
- 预防: 在 Stage 1 固定 `output_contract` 并在 Stage 2 对齐。

## G3: 模板中引用未声明变量

- 现象: prompt 字符串格式化时报 `NameError` 或内容为空。
- 根因: 使用了不在 `build_prompt` 参数中的变量。
- 检测: 静态检查 `no_undefined_template_vars` 失败。
- 修复: 将变量纳入函数参数或改成常量。
- 预防: 代码生成后逐项对照参数与模板变量。

## G4: 机械拆分多个 prompt 类

- 现象: 产物过度复杂，维护困难。
- 根因: 将可在单个模板内完成的任务拆成多个类。
- 检测: Stage 1 策略解释无法给出必要性。
- 修复: 合并为一个职责清晰的模板类。
- 预防: 仅在语义职责显著不同时才拆分。

## G5: 忽略用户约束优先级

- 现象: 代码可运行但不满足业务约束（语气、禁用词、返回长度等）。
- 根因: 约束未进入 Prompt 明确段落。
- 检测: 验收清单 `constraints_applied` 失败。
- 修复: 在 `# Task` 或 `# Output Format` 区域显式落约束。
- 预防: Requirement Mapping 中先列约束，再映射到代码。

## G6: `prompt_template` 类型与算子不匹配

- 现象: 代码看似完整，但运行时报类型/属性错误，或算子不识别模板。
- 根因: 未按 `OP_NAME` 真实签名选择模板类型（例如该用 `FormatStrPrompt` 却生成了 `DIYPromptABC`）。
- 检测: 静态检查 `prompt_template_type_aligned` 失败；集成片段与算子签名不一致。
- 修复: 以算子签名说明为准，重写模板类型与集成代码。
- 预防: 先确认 `OP_NAME` 的构造参数与 `prompt_template` 类型，再生成 Prompt 产物。

## G7: build_system_prompt 未实现导致 AttributeError

- 现象: 算子调用 `self.prompt_template.build_system_prompt()` 时报 `AttributeError`。
- 根因: 生成的 `DIYPromptABC` 子类只实现了 `build_prompt`，未实现 `build_system_prompt`。
- 检测: 验收清单 Section F `build_system_prompt_implemented` 失败；所有 KG 算子均调用此方法。
- 修复: 在类中添加 `def build_system_prompt(self) -> str:` 并返回角色/任务/格式约束的系统 prompt。
- 预防: 始终从 `diy_prompt_kg_template.py.tmpl` 生成，该模板强制包含此方法。

## G8: 输出字段名虚构（与 KG 解析器不兼容）

- 现象: LLM 被要求返回 `{"entity_type": ..., "source": ...}` 等字段，但算子只读取 `entity`（字符串数组）。
- 根因: 凭直觉设计了输出 schema，而非对照矩阵中算子真实读取的字段。
- 检测: 验收清单 Section F `output_schema_matches_run_output_key` 和 `no_invented_kg_fields` 失败。
- 修复: 对照 `operator-compatibility-matrix.md` 的 Output Schema 列，严格使用矩阵中指定的顶层字段名。
- 预防: Stage 1 的 `output_contract` 必须直接引用矩阵 schema，不允许自行设计字段名。

## G9: build_prompt 参数顺序与 run_input_keys 顺序不一致

- 现象: 运行时 `entity_list` 和 `text` 互换传入，导致实体列表被当作文本处理。
- 根因: 未对照 `run_input_keys` 列表顺序对齐 `build_prompt` 参数声明顺序。
- 检测: Stage 2 集成片段中的调用顺序与 `build_prompt` 签名不一致时可发现。
- 修复: 对照 `operator-compatibility-matrix.md` 的 `build_prompt params` 列，保持参数顺序与 `run_input_keys` 一一对应。
- 预防: Stage 1 中显式列出参数顺序，并在 Requirement Mapping 做列名→参数名的一一映射。

## G10: Triple/tuple 输出未使用 `<subj>/<obj>/<rel>` 标签语法

- 现象: 生成的 prompt 要求 LLM 输出 `{"subject": ..., "relation": ..., "object": ...}` 字典格式，但 DataFlow-KG 解析器按 `<subj> X <obj> Y <rel> Z` 格式解析，导致解析失败。
- 根因: 使用了直觉上合理但与实际解析器不兼容的 JSON 格式。
- 检测: 验收清单 Section F `output_format_matches_parser` 失败。
- 修复: 严格使用矩阵中规定的格式字符串，例如 `"<subj> {entity_a} <obj> {entity_b} <rel> {relation}"`。
- 预防: Stage 2 Prompt Design Summary 中必须引用矩阵给出的 schema，不允许自行设计标签语法。
