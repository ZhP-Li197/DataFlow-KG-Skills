---
name: kg-entity-extraction
description: >-
  KGEntityExtraction 算子的参考文档。使用 LLM 从原始文本中抽取实体表层形式。
  适用场景：所有 KG pipeline 在抽取三元组/四元组之前都需要 entity 列，此算子从自由文本列产出该列。

trigger_keywords:
  - KGEntityExtraction
  - kg-entity-extraction
  - 实体抽取
  - KG 实体

version: 1.0.0
---

# KGEntityExtraction 算子参考

`KGEntityExtraction` 是 DataFlow-KG pipeline 的标准入口算子。读取原始文本列，输出逗号分隔的实体字符串（每行一个）。

## 1. 导入

```python
from dataflow.operators.general_kg import KGEntityExtraction
```

## 2. 构造函数

```python
KGEntityExtraction(
    llm_serving,                # 必需
    seed=0,                     # 可选
    lang="en",                  # 可选；"en" 或 "zh"
    prompt_template=None,       # 可选；None 时使用默认 KGEntityExtractionPrompt(lang)
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 对象（如 `APILLMServing_request`） |
| `seed` | 否 | `0` | 随机种子；仅初始化内部 Random，推理过程中未使用 |
| `lang` | 否 | `"en"` | 提示词语言；`"en"` 或 `"zh"` |
| `prompt_template` | 否 | `None` | 自定义 `KGEntityExtractionPrompt` 或 `DIYPromptABC` 实例；为 `None` 时使用默认模板 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entity",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 当前算子步骤的存储对象 |
| `input_key` | 否 | `"raw_chunk"` | 从当前 DataFrame 读取的列名 |
| `output_key` | 否 | `"entity"` | 写回 DataFrame 的列名 |

## 4. 真实执行逻辑

1. 从 `storage` 读取 DataFrame
2. 校验 `input_key` 存在且 `output_key` 不存在
3. 逐行预处理文本，未通过质量检查则跳过：
   - 长度需 ≥ 10 且 ≤ 200000 字符
   - 需含 ≥ 2 个句子终止符（`.` 或 `。`）
   - 特殊字符比例 ≤ 30%
4. 通过模板生成 prompt，逐行调用 `llm_serving.generate_from_input(...)`
5. 解析 LLM 返回的 JSON 数组，用 `", "` 拼接成实体字符串
6. 规范化时会剥离常见英文停用词（`the / a / an / of / and / or / ...`）
7. 写回 `dataframe[output_key]` 并 `storage.write(...)`
8. 返回 `[output_key]`

## 5. 重要规则

1. `input_key` 必须在当前 DataFrame 中存在
2. `output_key` 必须不存在（不允许覆盖已有列）
3. 未通过文本质量检查的行得到空字符串 `""`，但不会被删除
4. LLM 解析失败的行同样得到 `""`；不抛异常

## 6. 常见用法

```python
from dataflow.operators.general_kg import KGEntityExtraction

self.entity_extractor = KGEntityExtraction(
    llm_serving=self.llm_serving,
    lang="en",
)

self.entity_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entity",
)
```

## 7. 返回值

```python
return [output_key]
```

用于下游算子链式调用与列追踪。
