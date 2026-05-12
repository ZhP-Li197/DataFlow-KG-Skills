---
name: mmkg-subgraph-base-qa-generation
description: >-
  MMKGSubgraphBaseQAGeneration 算子的参考文档。基于文本子图及其对齐的 vis_triple 与 vis_url，由 VLM 生成多模态 QA。
  适用场景：基于 MMKGEntityBasedSubgraphSampling 的输出生成多模态 QA。

trigger_keywords:
  - MMKGSubgraphBaseQAGeneration
  - mmkg-subgraph-base-qa-generation
  - 多模态 QA
  - VLM QA

version: 1.0.0
---

# MMKGSubgraphBaseQAGeneration 算子参考

多模态 QA 生成器。读取每行的 `vis_url` 列表与 `subgraph`，内部通过解析 `vis_triple` 重建 `img_id → url` 映射，然后用 VLM 处理对应图片 + 子图三元组。

## 1. 导入

```python
from dataflow.operators.multi_model_kg import MMKGSubgraphBaseQAGeneration
```

## 2. 构造函数

```python
MMKGSubgraphBaseQAGeneration(
    llm_serving,                # 必需，须为 APIVLMServing_openai
    lang="en",
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | VLM serving 后端 |
| `lang` | 否 | `"en"` | 提示语言 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="vis_url",
    input_key_meta="subgraph",
    output_key="QA_pairs",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | None | 步骤存储 |
| `input_key` | 否 | `"vis_url"` | 图片路径列表的列名 |
| `input_key_meta` | 否 | `"subgraph"` | 子图三元组列表的列名 |
| `output_key` | 否 | `"QA_pairs"` | 输出 QA 列表的列名 |

## 4. 真实执行逻辑

1. 读取 DataFrame；逐行取 `vis_url`、`vis_triple`（列名硬编码）、`subgraph`
2. 用正则 `r"<obj>\s*(.+?)\s*(?=<rel>)"` 从每条 `vis_triple` 解析 `img_id`
3. 按首次出现顺序去重 img_id，再与 `vis_url` 中的元素配对构造 `img_dict`
4. 若 `subgraph` 为字符串，按 `"\n"` 切分获取三元组列表
5. 对每张图片，将图片与子图上下文一起交给 VLM
6. 从每个 LLM JSON 响应中提取 `QA_pairs`，将所有图片级 QA 汇总为该行的输出

## 5. 重要规则

1. `llm_serving` 必须为 `APIVLMServing_openai`
2. `vis_triple` 列名硬编码——不要在上游改名
3. `vis_url` 与 `vis_triple` 必须保持 `MMKGEntityBasedSubgraphSampling` 输出的对齐顺序；中间手动改动会破坏映射
4. LLM 解析失败时该行得到 `[]`，行不会被删除
5. 行数保持不变；每行 `QA_pairs` 为列表值

## 6. 常见用法

```python
self.mm_qa_generator = MMKGSubgraphBaseQAGeneration(
    llm_serving=self.vlm_serving,
    lang="en",
)

self.mm_qa_generator.run(
    storage=self.storage.step(),
    input_key="vis_url",
    input_key_meta="subgraph",
    output_key="QA_pairs",
)
```

## 7. 返回值

```python
return [output_key]
```
