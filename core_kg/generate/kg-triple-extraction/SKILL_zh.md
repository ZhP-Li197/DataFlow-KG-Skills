---
name: kg-triple-extraction
description: >-
  KGTripleExtraction 算子的参考文档。基于候选实体列表，从文本中抽取关系或属性三元组。
  适用场景：在 KGEntityExtraction 产出 entity 列之后，pipeline 需要结构化三元组时使用。

trigger_keywords:
  - KGTripleExtraction
  - kg-triple-extraction
  - 三元组抽取
  - 关系三元组
  - 属性三元组

version: 1.0.0
---

# KGTripleExtraction 算子参考

基于预先抽取的候选实体列表，使用 LLM 从原始文本中抽取实体–关系–宾语（或实体–属性–值）三元组。

## 1. 导入

```python
from dataflow.operators.general_kg import KGTripleExtraction
```

## 2. 构造函数

```python
KGTripleExtraction(
    llm_serving,                # 必需
    seed=0,
    triple_type="attribute",    # "relation" 或 "attribute"
    lang="en",
    num_q=5,                    # 保留参数，未使用
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `triple_type` | 否 | `"attribute"` | `"relation"` 使用 `KGRelationTripleExtractionPrompt`；`"attribute"` 使用 `KGAttributeTripleExtractionPrompt` |
| `lang` | 否 | `"en"` | 提示语言 |
| `num_q` | 否 | `5` | 保留参数，当前未使用 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    input_key_meta="entity",
    output_key="triple",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 步骤存储 |
| `input_key` | 否 | `"raw_chunk"` | 源文本列名 |
| `input_key_meta` | 否 | `"entity"` | 实体列表列名（一般来自 `KGEntityExtraction`） |
| `output_key` | 否 | `"triple"` | 输出三元组列表的列名 |

## 4. 真实执行逻辑

1. 从 `storage` 读取 DataFrame；校验 `input_key` 与 `input_key_meta` 存在且 `output_key` 不存在
2. 逐行根据文本 + 实体列表构造 prompt，调用 `llm_serving.generate_from_input(...)`
3. 解析 LLM 返回 JSON 中的 `"triple"` 字段
4. 每行的 `output_key` 写入 `List[str]`，元素形如 `"<subj> X <obj> Y <rel> Z"`

## 5. 重要规则

1. `input_key` 与 `input_key_meta` 必须都存在；`output_key` 必须不存在
2. `entity` 列应为列表或逗号分隔字符串；算子不会自动转换其它类型
3. LLM 解析失败的行得到空列表 `[]`，不抛异常
4. 行数保持不变 —— 该算子**不扩展行数**，每行的 `triple` 是列表值

## 6. 常见用法

```python
self.triple_extractor = KGTripleExtraction(
    llm_serving=self.llm_serving,
    triple_type="relation",
    lang="en",
)

self.triple_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    input_key_meta="entity",
    output_key="triple",
)
```

## 7. 返回值

```python
return [output_key]
```
