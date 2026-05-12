---
name: kg-relation-triple-subgraph-qa-generation
description: >-
  KGRelationTripleSubgraphQAGeneration 算子的参考文档。基于采样子图列，使用 LLM 生成问答对。
  适用场景：子图采样算子已为每行提供局部 KG 上下文，需要 QA 数据用于训练或评测时。

trigger_keywords:
  - KGRelationTripleSubgraphQAGeneration
  - kg-relation-triple-subgraph-qa-generation
  - 子图 QA
  - KG QA 生成

version: 1.0.0
---

# KGRelationTripleSubgraphQAGeneration 算子参考

基于 LLM 的子图 QA 生成器。读取每行的三元组列表（子图），输出 `{"question", "answer"}` 列表。

## 1. 导入

```python
from dataflow.operators.general_kg import KGRelationTripleSubgraphQAGeneration
```

## 2. 构造函数

```python
KGRelationTripleSubgraphQAGeneration(
    llm_serving,                # 必需
    seed=0,
    lang="en",
    qa_type="num",              # "num" | "set" | "base"
    num_q=5,                    # 保留参数，未使用
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |
| `qa_type` | 否 | `"num"` | `"num"` → 计数/数值型 QA；`"set"` → 集合型 QA；`"base"` → **请避免**（当前代码 `self.promt_template` 有拼写错误） |
| `num_q` | 否 | `5` | 保留参数，未使用 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="subgraph",
    output_key="QA_pairs",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 步骤存储 |
| `input_key` | 否 | `"subgraph"` | 源子图列表的列名 |
| `output_key` | 否 | `"QA_pairs"` | 输出列名 |

## 4. 真实执行逻辑

1. 读取 DataFrame；校验 `input_key` 存在且 `output_key` 不存在
2. 逐行根据子图三元组构造 prompt，调用 `llm_serving.generate_from_input(...)`
3. 解析 LLM 返回 JSON 的 `"QA_pairs"` 字段
4. 解析失败的行得到空列表 `[]`，不抛异常

## 5. 重要规则

1. `qa_type="base"` 会走到含 `self.promt_template` 拼写错误的内部分支，运行时会抛 `AttributeError`——仅使用 `"num"` 或 `"set"`
2. 行数保持不变；每行的 `QA_pairs` 为列表
3. 算子不会校验子图字符串格式；格式异常的字符串会原样传给 LLM

## 6. 常见用法

```python
self.qa_generator = KGRelationTripleSubgraphQAGeneration(
    llm_serving=self.llm_serving,
    qa_type="set",
    lang="en",
)

self.qa_generator.run(
    storage=self.storage.step(),
    input_key="subgraph",
    output_key="QA_pairs",
)
```

## 7. 返回值

```python
return [output_key]
```
