---
name: kg-tuple-normalization
description: >-
  KGTupleNormalization 算子的参考文档。通过 LLM 规范化三元组/元组中的同义关系/属性并就地去重。
  适用场景：在 KGTripleExtraction 或 KGRelationTripleInference 产出原始三元组（可能含同义词或方向不一致）之后。

trigger_keywords:
  - KGTupleNormalization
  - kg-tuple-normalization
  - 三元组规范化
  - 同义归一

version: 1.0.0
---

# KGTupleNormalization 算子参考

基于 LLM 的三元组/元组规范化。同义关系会被合并（如 `is_married_to` ↔ `was_married_to`），方向被统一，重复条目被去除。

## 1. 导入

```python
from dataflow.operators.general_kg import KGTupleNormalization
```

## 2. 构造函数

```python
KGTupleNormalization(
    llm_serving,                # 必需
    seed=0,
    lang="en",
    attribute_prompt=None,      # None 时使用默认 KGAttributeNormalizationPrompt(lang)
    relation_prompt=None,       # None 时使用默认 KGRelationNormalizationPrompt(lang)
    num_q=5,                    # 保留参数，未使用
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |
| `attribute_prompt` | 否 | `None` | 自定义属性三元组规范化 prompt |
| `relation_prompt` | 否 | `None` | 自定义关系三元组规范化 prompt |
| `num_q` | 否 | `5` | 保留参数，未使用 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="normalized_triple",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 步骤存储 |
| `input_key` | 否 | `"triple"` | 源三元组/元组列表的列名 |
| `output_key` | 否 | `"normalized_triple"` | 输出列名 |

## 4. 真实执行逻辑

1. 从 `storage` 读取 DataFrame；校验 `input_key` 存在且 `output_key` 不存在
2. 检查**首行的第一个三元组**判断列表是 `<rel>` 型（关系）还是 `<attribute>` 型（属性）；都不匹配时抛 `ValueError`
3. 根据类型选用对应 prompt
4. 逐行调用 `llm_serving.generate_from_input(...)`
5. 解析响应（去掉 ```` ```json ```` 围栏，JSON-load）取出 `"normalized_triple"` 字段
6. 写回 `dataframe[output_key]`

## 5. 重要规则

1. `input_key` 必须存在；`output_key` 必须不存在
2. 单行内不支持混合类型（部分关系三元组 + 部分属性三元组）；首条三元组决定 prompt
3. LLM 解析失败的行得到空字符串 `""`（不是空列表）
4. 不扩展行数

## 6. 常见用法

```python
self.normalizer = KGTupleNormalization(
    llm_serving=self.llm_serving,
    lang="en",
)

self.normalizer.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="normalized_triple",
)
```

## 7. 返回值

```python
return [output_key]
```
