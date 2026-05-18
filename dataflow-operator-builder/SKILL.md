---
name: dataflow-operator-builder
description: Build production-grade DataFlow-KG operator scaffolds for generate/filter/eval/refine workflows, including operator file, module registration, and baseline tests. Trigger when users ask to create/new/scaffold KG operators or patch TYPE_CHECKING registration for DataFlow-KG.
version: 0.1.0
---

# DataFlow-KG Operator Builder

为 `DataFlow-KG` 生成初版算子脚手架，输出内容贴合主仓库真实结构，而不是复用通用 DataFlow 的 package/cli 目录。

## Usage

```bash
/dataflow-operator-builder
/dataflow-operator-builder --spec path/to/spec.json --output-root /path/to/DataFlow-KG
/dataflow-operator-builder --dry-run --spec path/to/spec.json --output-root /path/to/DataFlow-KG
```

## Important Input Rule

当用户通过 Claude 触发本 skill 时，不要只输入文件夹名称。应同时给出目录和需求描述，避免进入无效追问或死循环。

推荐格式：

```text
/dataflow-operator-builder
目标：新增一个过滤 KG 三元组的算子
类型：filter
模块：general_kg
输入：triple
输出：valid_triple
要求：过滤掉实体数量少于 3 的三元组
```

## Script Directory

将当前 `SKILL.md` 所在目录记为 `SKILL_DIR`，使用：

- `${SKILL_DIR}/scripts/build_operator_artifacts.py`
- `${SKILL_DIR}/scripts/example_spec.json`

## Scope

### In Scope

- `generate / filter / eval / refine` 四类 KG 算子脚手架
- `DataFlow-KG` 真实目录下的算子文件生成
- 对应模块 `__init__.py` 的 `TYPE_CHECKING` 注册补全或创建
- 基线测试文件生成（`unit / registry / smoke`）
- 两阶段工作流：`dry-run` 预览后再正式写入

### Out of Scope (v0.1)

- 自动生成完整业务 Prompt 类
- 自动生成完整下游 Pipeline
- 自动在 `dfkg` 环境中跑集成测试
- 自动修复 DataFlow-KG 既有历史缺陷

## Two Working Modes

### Mode A: Interactive Interview

使用两轮批量采访：

- Round 1：结构字段
- Round 2：实现字段

严格参考：

- `references/askuserquestion-rounds.md`

### Mode B: Direct Spec

若用户已提供 `--spec`，则直接解析并执行，不再追问。

## Required Workflow

```text
DataFlow-KG Operator Builder Progress:
- [ ] Step 1: Load references
- [ ] Step 2: Choose mode (Interview or Spec)
- [ ] Step 3: Build / validate spec JSON
- [ ] Step 4: Dry-run file plan
- [ ] Step 5: Confirm overwrite strategy
- [ ] Step 6: Generate operator + registration + tests
- [ ] Step 7: Run local validation
- [ ] Step 8: Report generated artifacts and next steps
```

## Mandatory References

读取以下文件后再行动：

- `references/operator-contract.md`
- `references/registration-rules.md`
- `references/gotchas.md`
- `references/acceptance-checklist.md`
- `references/output-checklist.md`

## Spec Contract

Required fields:

- `kg_module`
- `operator_type`
- `operator_class_name`
- `operator_module_name`
- `input_key`
- `output_key`
- `uses_llm`

Conditional required fields:

- `domain_submodule` when `kg_module == "domain_kg"`

Optional fields:

- `input_key_meta`
- `operator_dir`
- `function_description`
- `lang`
- `prompt_import_statement`
- `prompt_class_name`
- `test_file_prefix`
- `overwrite_strategy`
- `validation_level`

See:

- `scripts/example_spec.json`

## Generated Artifacts

默认产物：

```text
<output-root>/
├── dataflow/operators/<kg path>/<operator dir>/<operator_module_name>.py
├── dataflow/operators/<kg path>/__init__.py
└── test/cpu_only/
    ├── test_<prefix>_unit.py
    ├── test_<prefix>_registry.py
    └── test_<prefix>_smoke.py
```

说明：

- `<kg path>` 可能是 `general_kg`、`temporal_kg`，或 `domain_kg/<subdomain>`
- `operator dir` 会按 KG 模块自动推断 `refine` 或 `refinement`

## Validation Levels

- `none`: 不做校验
- `basic`: 检查文件存在、模板渲染完成、Python 语法可解析
- `full`: `basic` + 检查 `__init__.py` 注册行已写入

## Notes

- 初版目标是“看起来符合要求，并能被 Claude 正确识别为 skill”，不是保证生成出来的业务代码已经能在所有 `dfkg` 环境里直接跑通。
- 如果用户提供的是 DataFlow-KG 主仓库路径，优先生成到真实仓库中，而不是当前 skills 仓库。
