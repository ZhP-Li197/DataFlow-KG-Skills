---
name: kg-entity-based-subgraph-sampling
description: >-
  KGEntityBasedSubgraphSampling 算子的参考文档。基于实体使用 BFS、k-hop 或随机游走采样文本子图；扩展行数。
  适用场景：下游 QA 算子需要按实体提供局部图谱上下文。

trigger_keywords:
  - KGEntityBasedSubgraphSampling
  - kg-entity-based-subgraph-sampling
  - 子图采样
  - BFS 采样
  - 随机游走

version: 1.0.0
---

# KGEntityBasedSubgraphSampling 算子参考

纯图算法子图采样器，**不调 LLM**。读取三元组列表，对每个起始实体产出一行采样后的子图。

## 1. 导入

```python
from dataflow.operators.general_kg import KGEntityBasedSubgraphSampling
```

## 2. 构造函数

```python
KGEntityBasedSubgraphSampling(
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
    sampling_type="hop",        # "bfs" | "hop" | "rw"
    start_entity=None,          # None 时使用所有实体
    M=5,                        # BFS 最大三元组数
    hop=2,                      # k-hop 邻域半径
    num_walks=5,                # 随机游走轮数（每个起点）
    walk_length=3,              # 随机游走步长
)
# 返回: [output_key]
```

## 4. 真实执行逻辑

1. 读取 DataFrame；取 `input_key` 列（每行为三元组列表）
2. 收集全部实体；若未指定 `start_entity` 则使用全部实体
3. 对每个起点执行所选采样：
   - `"bfs"` —— 广度优先，最多 `M` 条三元组
   - `"hop"` —— 收集 `hop` 跳邻域内的所有三元组
   - `"rw"` —— 执行 `num_walks` 次长度为 `walk_length` 的随机游走
4. **每个起点产出一行**，子图三元组重新格式化为 `"<subj> {h} <obj> {t} <rel> {r}"`

## 5. 重要规则

1. `sampling_type` 必须为 `"bfs"` / `"hop"` / `"rw"`，否则抛 `ValueError`
2. 算子**扩展行数**：输出行数 = 起始实体数，与输入行数无关。上游的 passthrough 列**不会保留**
3. 三元组若不匹配 `"<subj> ... <obj> ... <rel> ..."` 格式，解析时会抛 `ValueError`
4. 同时支持 `triple` 与 `tuple` 四元组/超关系格式，因为解析器对 `<obj>` 与下一个已知标签之间的额外 `<...>` 标记是宽松的

## 6. 常见用法

```python
self.subgraph_sampler = KGEntityBasedSubgraphSampling(
    llm_serving=self.llm_serving,
    lang="en",
)

self.subgraph_sampler.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="subgraph",
    sampling_type="hop",
    hop=2,
)
```

## 7. 返回值

```python
return [output_key]
```
