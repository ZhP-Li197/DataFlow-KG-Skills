# AskUserQuestion Rounds

本 skill 的默认采访模式固定为两轮，且每轮都应批量提问。

## Round 1: 结构字段

必须一次性采集：

- 算子类型：`generate / filter / eval / refine`
- KG 模块：`general_kg / commonsense_kg / temporal_kg / hyper_relation_kg / multi_model_kg / graph_rag / graph_reasoning / domain_kg`
- 若为 `domain_kg`，再问子模块：`financial_kg / legal_kg / medical_kg / geospatial_kg / scholar_kg`
- 主输入列名 `input_key`
- 是否有辅助输入列 `input_key_meta`
- 主输出列名 `output_key`
- 是否依赖 LLM

## Round 2: 实现字段

一次性采集：

- 算子的一句话功能描述
- 默认语言 `lang`
- 是否需要 `@prompt_restrict`
- 若需要，Prompt 的 import 语句和类名
- 测试文件前缀
- 覆盖策略

## Interaction Rule

- 每个问题块给出推荐项和一句原因。
- 不要只让用户输入“文件夹名”；要引导用户同时给出需求描述。
- 若用户已提供完整 spec，则不采访。
