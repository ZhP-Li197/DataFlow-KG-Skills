---
name: kg-relation-tuple-path-generator
description: >-
  KGRelationTuplePathGenerator 算子的参考文档。从任意三元组格式列中枚举 k-hop 无向路径，纯图算法，不调 LLM；扩展行数。
  适用场景：为基于路径的 QA 算子（通用/时序/超关系）提供输入。

trigger_keywords:
  - KGRelationTuplePathGenerator
  - kg-relation-tuple-path-generator
  - 路径采样
  - 路径枚举
  - k-hop 路径

version: 1.0.0
---

# KGRelationTuplePathGenerator 算子参考

纯图路径枚举器。解析值为三元组字符串的任意列（`<subj> X <obj> Y <rel> Z` 或带时间、属性等额外字段），构建无向图后写出所有长度为 k 的不同路径。

## 1. 导入

```python
from dataflow.operators.general_kg import KGRelationTuplePathGenerator
```

## 2. 构造函数

```python
KGRelationTuplePathGenerator(
    seed=0,
    lang="en",                  # 接受但未使用
    k=2,                        # 路径长度（k 条边）
    max_paths_per_group=100,    # 每个输入行最多生成的路径数
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `seed` | 否 | `0` | 路径排序的随机种子 |
| `lang` | 否 | `"en"` | 接受但未使用 |
| `k` | 否 | `2` | 路径边数；输出列名以该值作为前缀 |
| `max_paths_per_group` | 否 | `100` | 单组路径数上限 |

**注意**：本算子**不接受** `llm_serving` 参数。

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key_meta="hop_paths",
)
# 返回: [<actual_output_column>]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | None | 步骤存储 |
| `input_key` | 否 | `"triple"` | 源三元组列表的列名（时序/超关系传 `"tuple"`） |
| `output_key_meta` | 否 | `"hop_paths"` | 输出列名**后缀**；实际列名为 `"{k}_{output_key_meta}"`，例如 `"2_hop_paths"` |

## 4. 真实执行逻辑

1. 对每行输入解析三元组为 `(subject, object, relation_payload)` 元组
2. 构建无向图（每个三元组 → `subject` 与 `object` 之间一条边）
3. DFS 枚举长度为 `k` 的不同路径
4. 通过边集合规范化去重（反转或顺序不同但边集相同的路径会被合并）
5. **每条路径产出一行**，序列化为 `"triple1 || triple2 || ..."`（用 `" || "` 连接）
6. 每行输入最多生成 `max_paths_per_group` 条路径

## 5. 重要规则

1. 输出列名为 `"{k}_{output_key_meta}"`——无法自定义平铺名；下游 path-QA 算子通过其 `hop` 参数读取该列
2. **扩展行数**：输出行数 = 各行路径数之和；上游 passthrough 列**不会保留**
3. 同时支持 `triple`（通用 KG）和 `tuple`（时序四元组、超关系元组）格式——通过 `input_key` 指定
4. 解析失败的三元组在建图阶段被静默丢弃
5. 路径按边集合去重，因此遍历顺序不同但边集相同的路径会被合并

## 6. 常见用法

```python
self.path_sampler = KGRelationTuplePathGenerator(
    k=2,
    max_paths_per_group=100,
)

# 通用 KG
self.path_sampler.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key_meta="hop_paths",
)
# 产生 "2_hop_paths" 列

# 时序或超关系 KG
self.path_sampler.run(
    storage=self.storage.step(),
    input_key="tuple",
    output_key_meta="hop_paths",
)
```

## 7. 返回值

```python
return [<actual_output_column>]
```
