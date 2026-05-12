---
name: mmkg-entity-based-subgraph-sampling
description: >-
  MMKGEntityBasedSubgraphSampling 算子的参考文档。多模态版本的子图采样：按起始实体产出 subgraph + 过滤后的 vis_triple + 对齐的 vis_url。
  适用场景：为多模态 QA 生成器产出（文本子图，视觉三元组，图片路径）对齐的三元组合。

trigger_keywords:
  - MMKGEntityBasedSubgraphSampling
  - mmkg-entity-based-subgraph-sampling
  - 多模态子图采样
  - vis_url 传播

version: 1.0.0
---

# MMKGEntityBasedSubgraphSampling 算子参考

多模态子图采样器。读取 `triple`、`vis_triple` 和 `img_dict`，按起始实体输出包含以下三项的对齐结果：

- 文本子图 `subgraph`
- 仅覆盖该子图实体的过滤后 `vis_triple`
- 与过滤后 `vis_triple` 对齐（按首次出现顺序去重）的 `vis_url`

## 1. 导入

```python
from dataflow.operators.multi_model_kg import MMKGEntityBasedSubgraphSampling
```

## 2. 构造函数

```python
MMKGEntityBasedSubgraphSampling(
    llm_serving,                # 接受但未实际使用
    seed=0,
    lang="en",                  # 接受但未实际使用
    num_q=5,                    # 保留参数，未使用
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是（签名要求） | None | 为接口兼容性保留，运行时未被调用 |
| `seed` | 否 | `0` | 随机游走与平局打破的随机种子 |
| `lang` | 否 | `"en"` | 接受但未使用 |
| `num_q` | 否 | `5` | 保留参数，未使用 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="subgraph",
    vis_triple_key="vis_triple",
    sampling_type="hop",        # "bfs" | "hop"（不支持 "rw"）
    start_entity=None,
    M=5,
    hop=2,
)
# 返回: [output_key, vis_triple_key, "vis_url"]
```

## 4. 真实执行逻辑

1. 读取 DataFrame，取 `triple`、`vis_triple`、`img_dict`（后两者列名按约定硬编码）
2. 决定起点实体（`start_entity=None` 时使用所有实体）
3. 对每个起点：
   - 通过 BFS 或 k-hop 采样 `subgraph`
   - 过滤 `vis_triple`，仅保留主语在子图实体中的视觉三元组
   - 根据过滤后视觉三元组提到的 img_id，从 `img_dict` 取出 `vis_url`，按首次出现顺序去重
4. 每个起点产出一行，三项相互对齐

## 5. 重要规则

1. `sampling_type` ∈ {`"bfs"`, `"hop"`}——多模态版**不支持** `"rw"`
2. **扩展行数**：输出行数 = 起始实体数；上游 passthrough 列**不会保留**
3. `img_dict` 列名硬编码；`vis_triple` 列名通过 `vis_triple_key` 可配置，但默认值应与 `MMKGVisualTripleExtraction` 的输出一致
4. 输出的 `vis_url` 与**过滤后**的 `vis_triple` 在首次出现去重后对齐；这种对齐正是下游 `MMKGSubgraphBaseQAGeneration` 依赖的
5. 视觉三元组主语解析使用正则 `r"<subj>\s*(.+?)\s*(?=<obj>)"`，与 `MMKGVisualTripleExtraction` 的输出格式一致

## 6. 常见用法

```python
self.mm_subgraph_sampler = MMKGEntityBasedSubgraphSampling(
    llm_serving=self.llm_serving,
    lang="en",
)

self.mm_subgraph_sampler.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="subgraph",
    vis_triple_key="vis_triple",
    sampling_type="hop",
    hop=2,
)
```

## 7. 返回值

```python
return [output_key, vis_triple_key, "vis_url"]
```
