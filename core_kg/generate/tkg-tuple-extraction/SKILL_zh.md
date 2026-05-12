---
name: tkg-tuple-extraction
description: >-
  TKGTupleExtraction 算子的参考文档。从文本中抽取带时间锚点的 4 元组（关系或属性两种形态）。
  适用场景：输入文本带显式时间戳/日期/时间区间，pipeline 需要时序 KG。

trigger_keywords:
  - TKGTupleExtraction
  - tkg-tuple-extraction
  - 时序 KG
  - 四元组抽取
  - 时间锚点

version: 1.0.0
---

# TKGTupleExtraction 算子参考

时序 KG 抽取器。读取原始文本，输出带时间锚点的 4 元组——关系型（`subject → relation → object @ time`）或属性型（`subject → attribute → value @ time`）。

## 1. 导入

```python
from dataflow.operators.temporal_kg import TKGTupleExtraction
```

## 2. 构造函数

```python
TKGTupleExtraction(
    llm_serving,                # 必需
    triple_type="attribute",    # "relation" | "attribute"
    seed=0,
    lang="en",
    num_q=5,                    # 保留参数，未使用
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `triple_type` | 否 | `"attribute"` | `"relation"` → 时间锚点关系；`"attribute"` → 时间锚点属性 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |
| `num_q` | 否 | `5` | 保留参数，未使用 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="tuple",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 步骤存储 |
| `input_key` | 否 | `"raw_chunk"` | 源文本列名 |
| `output_key` | 否 | `"tuple"` | 输出 4 元组列表的列名 |

## 4. 真实执行逻辑

1. 读取 DataFrame；校验 `input_key` 存在且 `output_key` 不存在
2. 与 `KGEntityExtraction` 同样的文本质量门：长度 10-200000、≥2 个句子终止符、特殊字符比例 ≤30%
3. 逐行调用 `llm_serving.generate_from_input(...)`
4. 解析 JSON 中的 `"tuple"` 字段
5. 每行 `tuple` 写入一个 4 元组列表

## 5. 重要规则

1. `input_key` 必须存在；`output_key` 必须不存在
2. 输出列是 `tuple`，**不是** `triple`。下游算子（如 `KGRelationTuplePathGenerator`）需用 `input_key="tuple"` 读取
3. 行数保持不变；每行的元组列表作为值传递
4. LLM 解析失败的行得到空列表 `[]`

## 6. 常见用法

```python
self.tuple_extractor = TKGTupleExtraction(
    llm_serving=self.llm_serving,
    triple_type="relation",
    lang="en",
)

self.tuple_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="tuple",
)
```

## 7. 返回值

```python
return [output_key]
```
