---
name: hrkg-relation-triple-path-qa-generation
description: >-
  HRKGRelationTriplePathQAGeneration 算子的参考文档。基于超关系元组（hop=1）或采样后的超关系 2-hop 路径生成 QA。
  适用场景：构造涉及多元事实的 QA 数据集。

trigger_keywords:
  - HRKGRelationTriplePathQAGeneration
  - hrkg-relation-triple-path-qa-generation
  - 超关系 QA
  - n-ary QA

version: 1.0.0
---

# HRKGRelationTriplePathQAGeneration 算子参考

针对超关系元组或采样后的 2-hop 路径的 QA 生成器。内置质量门：`len(QA_pairs) < 2` 的行被重置为 `[]`。

## 1. 导入

```python
from dataflow.operators.hyper_relation_kg import HRKGRelationTriplePathQAGeneration
```

## 2. 构造函数

```python
HRKGRelationTriplePathQAGeneration(
    llm_serving,                # 必需
    seed=0,
    lang="en",
    hop=1,                      # 仅支持 1 或 2
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | LLM serving 后端 |
| `seed` | 否 | `0` | 随机种子 |
| `lang` | 否 | `"en"` | 提示语言 |
| `hop` | 否 | `1` | 必须为 `1` 或 `2`，其他值抛 `ValueError` |

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
| `storage` | 是 | None | 步骤存储 |
| `input_key_meta` | 否 | `"hop_paths"` | 仅在 `hop>1` 时使用；输入列名解析为 `"{hop}_{input_key_meta}"` |
| `output_key` | 否 | `"QA_pairs"` | 输出列名（平铺，不带 `{hop}_` 前缀） |

## 4. 真实执行逻辑

1. 决定 `input_key`：
   - `hop=1` → 读取 `"tuple"` 列，忽略 `input_key_meta`
   - `hop=2` → 读取 `"{hop}_{input_key_meta}"`（如 `"2_hop_paths"`）
2. 将每行输入转为字符串（列表值用 `"\n".join`）
3. 用 `HRKGOneHopQAPathGenerationPrompt` 或 `HRKGTwoHopPathQAGenerationPrompt` 调用 LLM
4. 解析 JSON 响应中的 `QA_pairs`
5. `len(QA_pairs) < 2` 时该行被重置为 `[]`（质量门）

## 5. 重要规则

1. `hop` 仅支持 `1` 或 `2`，其它值抛 `ValueError`
2. 当 `hop=1` 时，输入列硬编码为 `"tuple"`，与 `input_key_meta` 无关
3. 输出列名为平铺的 `output_key`，**不带** `{hop}_` 前缀
4. `len(QA_pairs) < 2` 的行被清空为 `[]`；预期会有部分空行
5. LLM 解析失败也得到 `[]`

## 6. 常见用法

```python
# 1-hop 超关系元组 QA
self.hrkg_qa = HRKGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=1, lang="en",
)
self.hrkg_qa.run(
    storage=self.storage.step(),
    output_key="QA_pairs",
)

# 2-hop 路径 QA
self.hrkg_qa = HRKGRelationTriplePathQAGeneration(
    llm_serving=self.llm_serving, hop=2, lang="en",
)
self.hrkg_qa.run(
    storage=self.storage.step(),
    input_key_meta="hop_paths",
    output_key="QA_pairs",
)
```

## 7. 返回值

```python
return [output_key]
```
