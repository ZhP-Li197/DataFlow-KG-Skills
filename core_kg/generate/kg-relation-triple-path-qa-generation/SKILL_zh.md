---
name: kg-relation-triple-path-qa-generation
description: >-
  KGRelationTriplePathQAGeneration 算子的参考文档。基于单个三元组（hop=1）或 KGRelationTuplePathGenerator 产出的 2-hop 路径生成问答对。
  适用场景：基于路径形态 KG 上下文构造推理型 QA。

trigger_keywords:
  - KGRelationTriplePathQAGeneration
  - kg-relation-triple-path-qa-generation
  - 路径 QA
  - 1-hop QA
  - 2-hop QA

version: 1.0.0
---

# KGRelationTriplePathQAGeneration 算子参考

针对单个三元组（`hop=1`）或 2-hop 路径（`hop=2`）的 QA 生成器。输入列名根据 `hop` 动态决定。

## 1. 导入

```python
from dataflow.operators.general_kg import KGRelationTriplePathQAGeneration
```

## 2. 构造函数

```python
KGRelationTriplePathQAGeneration(
    llm_serving,                # 必需
    seed=0,
    lang="en",
    hop=1,                      # 1 或 2
    num_q=5,                    # 保留参数，未使用
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |
| `hop` | 否 | `1` | `1` 使用 `KGOneHopQAPathGenerationPrompt`；`2` 使用 `KGTwoHopPathQAGenerationPrompt` |
| `num_q` | 否 | `5` | 保留参数，未使用 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key="QA_pairs",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | `None` | 步骤存储 |
| `input_key_meta` | 否 | `"hop_paths"` | 仅在 `hop>1` 时使用；输入列名解析为 `"{hop}_{input_key_meta}"`（如 `"2_hop_paths"`） |
| `output_key` | 否 | `"QA_pairs"` | 输出列名 |

## 4. 真实执行逻辑

1. 决定 `input_key`：
   - `hop=1` → 直接读取 `"triple"` 列（忽略 `input_key_meta`）
   - `hop>1` → 读取 `"{hop}_{input_key_meta}"`（如 `"2_hop_paths"`）
2. 逐行调用 LLM 传入路径字符串
3. 解析响应，将 `QA_pairs` 列表写入输出列
4. 输出列名**始终**为 `output_key`，**不**包含 `{hop}_` 前缀

## 5. 重要规则

1. `hop` 仅支持 1 或 2；其它值未被 prompt 选择逻辑覆盖
2. 当 `hop=1` 时，输入列硬编码为 `"triple"`，与 `input_key_meta` 无关
3. 算子不会按 `len(QA_pairs)` 过滤行；空列表会保留
4. 行数保持不变

## 6. 常见用法

```python
# 1-hop QA（基于单个三元组）
self.qa_generator = KGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=1, lang="en",
)
self.qa_generator.run(
    storage=self.storage.step(),
    output_key="QA_pairs",
)

# 2-hop QA（基于采样路径）
self.qa_generator = KGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=2, lang="en",
)
self.qa_generator.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key="QA_pairs",
)
```

## 7. 返回值

```python
return [output_key]
```
