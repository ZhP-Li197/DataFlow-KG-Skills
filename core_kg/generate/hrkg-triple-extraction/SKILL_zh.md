---
name: hrkg-triple-extraction
description: >-
  HRKGTripleExtraction 算子的参考文档。抽取携带多个 qualifier/attribute 槽位的超关系元组。
  适用场景：文本含多元关系（一个事实超出 subject-relation-object 三元组）。

trigger_keywords:
  - HRKGTripleExtraction
  - hrkg-triple-extraction
  - 超关系
  - n-ary KG
  - 超关系元组

version: 1.0.0
---

# HRKGTripleExtraction 算子参考

超关系 KG 抽取器。读取原始文本，输出可带属性/限定符槽位的元组（超出基本 (subject, relation, object)），例如 "Obama 从 2009 到 2017 任 President"。

## 1. 导入

```python
from dataflow.operators.hyper_relation_kg import HRKGTripleExtraction
```

## 2. 构造函数

```python
HRKGTripleExtraction(
    llm_serving,                # 必需
    seed=0,
    lang="en",
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |

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
| `output_key` | 否 | `"tuple"` | 输出超关系元组列表的列名 |

## 4. 真实执行逻辑

1. 读取 DataFrame；校验 `input_key` 存在且 `output_key` 不存在
2. 与 `KGEntityExtraction` 同样的文本质量门（长度、句数、特殊字符）
3. 逐行用 `HRKGHyperRelationExtractorPrompt` 调用 `llm_serving.generate_from_input(...)`
4. 解析 JSON 中的 `"tuple"` 字段
5. 每行 `tuple` 写入超关系元组对象列表（具体 JSON 结构由 LLM 决定，算子原样保留）

## 5. 重要规则

1. 输出列名为 `tuple`，**不是** `triple`——下游算子从 `tuple` 列读取
2. 算子不会规范化超关系 JSON schema；下游代码应宽容对待额外的 `<attribute>` / `<qualifier>` 标记
3. 行数保持不变；LLM 解析失败的行得到空列表 `[]`

## 6. 常见用法

```python
self.hrkg_extractor = HRKGTripleExtraction(
    llm_serving=self.llm_serving,
    lang="en",
)

self.hrkg_extractor.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="tuple",
)
```

## 7. 返回值

```python
return [output_key]
```
