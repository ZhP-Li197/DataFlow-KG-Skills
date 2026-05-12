---
name: tkg-tuple-path-qa-generation
description: >-
  TKGTuplePathQAGeneration 算子的参考文档。基于时序元组（hop=1）或采样的时序路径（hop>1）使用 LLM 生成时间感知 QA。
  适用场景：构造时间锚点 QA 数据（时间点、事件顺序、时间区间等）。

trigger_keywords:
  - TKGTuplePathQAGeneration
  - tkg-tuple-path-qa-generation
  - 时序 QA
  - 时间顺序 QA
  - 时间区间 QA

version: 1.0.0
---

# TKGTuplePathQAGeneration 算子参考

四种时间感知 prompt 的 QA 生成器，覆盖时间点、事件顺序、时间排序、时间区间等问题。

## 1. 导入

```python
from dataflow.operators.temporal_kg import TKGTuplePathQAGeneration
```

## 2. 构造函数

```python
TKGTuplePathQAGeneration(
    llm_serving,                # 必需
    seed=0,
    lang="en",
    hop=2,                      # 路径跳数，决定输入/输出列名前缀
    qa_type="time_point",       # "time_point" | "event_order" | "time_order" | "time_interval"
    num_q=5,                    # 保留参数，未使用
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |
| `hop` | 否 | `2` | 路径边数；同时作为输入与输出列前缀 |
| `qa_type` | 否 | `"time_point"` | 4 种时间感知 prompt 之一；非法值会抛 `ValueError` |
| `num_q` | 否 | `5` | 保留参数，未使用 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key_meta="QA_pairs",
)
# 返回: [<actual_output_column>]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 步骤存储 |
| `input_key_meta` | 否 | `"hop_paths"` | 输入列名**后缀**；实际列名为 `"{hop}_{input_key_meta}"`，如 `"2_hop_paths"` |
| `output_key_meta` | 否 | `"QA_pairs"` | 输出列名**后缀**；实际列名为 `"{hop}_{output_key_meta}"`，如 `"2_QA_pairs"` |

## 4. 真实执行逻辑

1. 决定 `input_key`：
   - `hop=1` → 读取 `"tuple"` 列，忽略 `input_key_meta`
   - `hop>1` → 读取 `"{hop}_{input_key_meta}"`
2. 逐行用所选 `qa_type` 的 prompt 调用 LLM
3. 解析响应，取 `"QA_pairs"` 字段
4. 输出列名为 `"{hop}_{output_key_meta}"`

## 5. 重要规则

1. `qa_type` 必须为 4 个支持值之一，否则抛 `ValueError`
2. 输出列名带 `{hop}_` 前缀——无法固定为像 `QA_pairs` 这样的平铺名
3. 当 `hop=1` 时，输入列为 `"tuple"`，与 `input_key_meta` 无关
4. 行数保持不变；空 QA 列表会原样保留

## 6. 常见用法

```python
self.path_qa_generator = TKGTuplePathQAGeneration(
    llm_serving=self.llm_serving,
    hop=2,
    qa_type="time_order",
    lang="en",
)

self.path_qa_generator.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key_meta="QA_pairs",
)
# 写入 "2_QA_pairs"
```

## 7. 返回值

```python
return [<actual_output_column>]
```
