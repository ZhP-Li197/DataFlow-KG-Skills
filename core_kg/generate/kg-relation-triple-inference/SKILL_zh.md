---
name: kg-relation-triple-inference
description: >-
  KGRelationTripleInference 算子的参考文档。基于已有三元组（可选包含原始文本），使用 LLM 推理隐含的关系三元组；可将结果合并回原列。
  适用场景：扩展知识图谱闭包，得到文本中没有直接陈述的隐含关系。

trigger_keywords:
  - KGRelationTripleInference
  - kg-relation-triple-inference
  - 三元组推理
  - KG 闭包

version: 1.0.0
---

# KGRelationTripleInference 算子参考

基于 LLM 的 KG 闭包推理。读取已有三元组（可选附带原始文本），输出文本中没有直接陈述的隐含三元组。

## 1. 导入

```python
from dataflow.operators.general_kg import KGRelationTripleInference
```

## 2. 构造函数

```python
KGRelationTripleInference(
    llm_serving,                # 必需
    seed=0,
    lang="en",
    with_text=False,            # True 时同时读取 raw_chunk
    merge_to_input=False,       # True 时将推理结果去重合并回 triple 列
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |
| `with_text` | 否 | `False` | 为 `True` 时同时读取 `raw_chunk` 并使用 `KGRelationGenerationPrompt`；否则使用 `KGInferredTripleGenerationPrompt` |
| `merge_to_input` | 否 | `False` | 为 `True` 时将去重后的推理三元组追加回 `triple` 列 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="inferred_triple",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 步骤存储 |
| `input_key` | 否 | `"triple"` | 源三元组列表的列名 |
| `output_key` | 否 | `"inferred_triple"` | 输出列名 |

## 4. 真实执行逻辑

1. 读取 DataFrame；校验 `input_key` 存在且 `output_key` 不存在
2. 若 `with_text=True`，还需要 `raw_chunk` 列存在
3. 逐行调用 `llm_serving.generate_from_input(...)` 传入三元组列表（如启用 with_text 则附带文本）
4. 解析返回 JSON 中的 `"inferred_triple"` 字段
5. 若 `merge_to_input=True`，将推理三元组去重后追加回原 `triple` 列（**原地覆盖**）
6. 推理结果写入 `dataframe[output_key]`

## 5. 重要规则

1. `input_key` 必须存在；`output_key` 必须不存在
2. `with_text=True` 时 `raw_chunk` 列必须存在，否则抛 `KeyError`
3. `merge_to_input=True` 会**原地覆盖** `triple` 列；如需非破坏性输出请保持 `False`
4. LLM 解析失败时该行得到空列表

## 6. 常见用法

```python
# 非破坏式
self.inferrer = KGRelationTripleInference(
    llm_serving=self.llm_serving, lang="en",
)
self.inferrer.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="inferred_triple",
)

# 合并回原列
self.closure = KGRelationTripleInference(
    llm_serving=self.llm_serving, lang="en",
    with_text=True, merge_to_input=True,
)
self.closure.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="inferred_triple",
)
```

## 7. 返回值

```python
return [output_key]
```
