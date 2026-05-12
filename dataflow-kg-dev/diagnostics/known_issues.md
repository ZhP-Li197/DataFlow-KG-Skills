# DataFlow-KG 已知问题数据库

> **文件状态**：可追加更新**格式约定**：每条 Issue 包含：编号、标题、症状关键词、根因、解决方案、修复代码示例**使用方式**：诊断时先按"症状关键词"匹配，命中则直接给出根因和方案

---

## Issue #001 — 配置参数命名警告（非错误）

**标题**：`Unexpected key 'xxx' in operator` 警告

**症状关键词**：
- `Unexpected key`
- `in operator`
- `UserWarning`

**根因**：

`OPERATOR_REGISTRY.register()` 会校验 Pipeline 配置文件（YAML/JSON）中传入的 key 是否在算子的 `__init__` 参数列表中。若 key 不匹配（如大小写不同、多余参数），会抛出 `UserWarning`，但**不会中断执行**。

**解决方案**：

检查 Pipeline 配置文件中对应算子的参数名拼写，确保与算子 `__init__` 参数名完全一致（区分大小写）。

**修复示例**：

```yaml
# ❌ 错误
operators:
  - type: KGTripleExtraction
    Triple_Type: "relation"   # 大小写错误

# ✅ 正确
operators:
  - type: KGTripleExtraction
    triple_type: "relation"
```

---

## Issue #002 — 算子注册缺失

**标题**：`No object named 'Xxx' found in 'operators' registry`

**症状关键词**：
- `No object named`
- `found in 'operators' registry`
- `RegistryError`

**根因**：

新建算子文件后，未在对应模块的 `__init__.py` 的 `TYPE_CHECKING` 块中注册。LazyLoader 依赖此注册才能找到类。

**解决方案**：

在对应模块的 `__init__.py` 的 `TYPE_CHECKING` 块中添加 import：

```python
# dataflow/operators/<module>/__init__.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .filter.kg_my_new_filter import KGMyNewFilter  
```

**修复示例**：

```python
# dataflow/operators/general_kg/__init__.py
if TYPE_CHECKING:
    from .filter.my_new_filter import MyNewFilter  # ← 新增这行
```



---

## Issue #003 — Pipeline  key 不一致

**标题**：`Key Matching Error` / `does not match any output keys`

**症状关键词**：
- `Key Matching Error`
- `does not match any output keys`
- `KeyError` + Pipeline 上下文

**根因**：

Pipeline 中前一个算子的 `output_key` 与后一个算子的 `input_key` 不一致，DataFrame 中找不到对应列名。KG Pipeline 中尤其常见于 entity → triple 这一链路。

**解决方案**：

逐步检查 `forward()` 中每个算子调用的 `input_key` / `output_key`，确保相邻步骤的字段名严格一致。

**修复示例**：

```python
# ❌ 错误：step1 输出 "entities"，step2 读取 "entity"
self.entity_extractor_step1.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entities",      # 写入列名
)
self.triple_extractor_step2.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    input_key_meta="entity",    # 找不到 "entity" 列，实际是 "entities"
    output_key="triple",
)

# ✅ 正确：保持一致
self.entity_extractor_step1.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entity",
)
self.triple_extractor_step2.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    input_key_meta="entity",    # 与上一步 output_key 一致
    output_key="triple",
)
```

---

## Issue #004 — 缺少 storage.step()

**标题**：`You must call storage.step() before`

**症状关键词**：
- `You must call storage.step() before`
- `storage has not been stepped`
- `AssertionError` + storage 上下文

**根因**：

在 Pipeline `forward()` 中调用算子时，没有在每个 `run()` 调用时传递 `storage=self.storage.step()`，或使用了错误的用法（传 `self.storage` 而非 `self.storage.step()`）。

**解决方案**：

- Pipeline `forward()` 中：每次 `op.run()` 都传 `storage=self.storage.step()`
- 独立测试脚本中：先调用 `storage.step()`，再传 `storage` 本身给 `op.run()`

**修复示例**：

```python
# ❌ 错误（Pipeline 中）
self.op.run(storage=self.storage, input_key="triple")

# ✅ 正确（Pipeline 中）
self.op.run(storage=self.storage.step(), input_key="triple")

# ✅ 正确（独立测试脚本中）
storage = FileStorage(...)
storage.step()                                    # 手动推进一步
op.run(storage=storage, input_key="triple")       # 传 storage，不是 storage.step()
```

---

## Issue #005 — DummyStorage 不支持 get_keys_from_dataframe

**标题**：`DummyStorage` + `AttributeError` / `TypeError`

**症状关键词**：
- `DummyStorage`
- `AttributeError: 'DummyStorage' object has no attribute`
- `TypeError` + DummyStorage 上下文

**根因**：

`DummyStorage` 是一个测试用的 stub，不实现 `get_keys_from_dataframe()` 及其他完整 Storage 方法。在 Pipeline 中使用 `DummyStorage` 会导致算子调用这些方法时抛出错误。

**解决方案**：

- Pipeline 中**必须**使用 `FileStorage`，禁止使用 `DummyStorage`
- `DummyStorage` 仅用于极简单元测试，不涉及 dataframe 操作时才可使用

**修复示例**：

```python
# ❌ 错误（Pipeline 中使用 DummyStorage）
from dataflow.utils.storage import DummyStorage
storage = DummyStorage()

# ✅ 正确（Pipeline 中使用 FileStorage）
from dataflow.utils.storage import FileStorage
storage = FileStorage(
    first_entry_file_name="./data/input.json",
    cache_path="./cache",
    file_name_prefix="kg_pipeline_step",
    cache_type="json",
)

```

---

---

## Issue #006 — LazyLoader 子包路径 import 失败

**标题**：`ModuleNotFoundError` + KG 算子子包路径

**症状关键词**：
- `ModuleNotFoundError`
- `ImportError` + 算子类名
- `dataflow.operators.general_kg.xxx`

**根因**：

DataFlow-KG 使用 LazyLoader 机制，算子类通过父模块 `__init__.py` 注册并懒加载。直接 import 子包路径会绕过 LazyLoader，在部分场景下导致 `ModuleNotFoundError`。

**解决方案**：

必须从父模块 import：

```python
# ✅ 正确
from dataflow.operators.general_kg import KGTripleExtraction, KGTupleValidity
from dataflow.operators.domain_kg.medical_kg import MedKGTripleExtraction
from dataflow.operators.temporal_kg import TKGTupleExtraction

# ❌ 错误：直接用子包路径
from dataflow.operators.general_kg.generate.kg_triple_extractor import KGTripleExtraction
from dataflow.operators.general_kg.filter.kg_tuple_validation import KGTupleValidity
```

验证 LazyLoader 管理的类名：

```python
import dataflow.operators.general_kg as kg
print(kg._import_structure)
```

---

## Issue #007 — `input_key_meta` 缺失导致 `ValueError`

**标题**：`Missing required column(s): ['entity']` / `input_key_meta` 未正确传递

**症状关键词**：
- `Missing required column(s)`
- `input_key_meta`
- `ValueError` + `KGTripleExtraction`

**根因**：

`KGTripleExtraction.run()` 要求 DataFrame 中必须同时存在 `input_key`（原文列）和 `input_key_meta`（实体列）。`_validate_dataframe()` 会检查两列，**任一缺失都会立即抛出 `ValueError`**。

常见触发场景：
1. Pipeline 中 `entity_extractor_step1` 的 `output_key` 与 `triple_extractor_step2` 的 `input_key_meta` 名称不一致（参见 Issue #003）
2. 调用 `KGTripleExtraction.run()` 时遗漏了 `input_key_meta` 参数，使用了默认值 `"entity"`，而 DataFrame 中实体列名实际为其他名称
3. 独立测试脚本中手动构造 DataFrame 时漏加实体列

```python
# kg_triple_extractor.py _validate_dataframe()
required_keys = [self.input_key, self.input_key_meta]   # 两列都必须存在
missing = [k for k in required_keys if k not in dataframe.columns]
if missing:
    raise ValueError(f"Missing required column(s): {missing}")
```

**解决方案**：

```python
# ❌ 错误：entity_extractor 输出 "entities"，triple_extractor 读 "entity"（默认值）
self.entity_extractor_step1.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entities",     # 写入列名
)
self.triple_extractor_step2.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    # input_key_meta 默认为 "entity"，但列名实际是 "entities" → ValueError
    output_key="triple",
)

# ✅ 正确：显式传入 input_key_meta，保持与上一步 output_key 一致
self.entity_extractor_step1.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    output_key="entity",
)
self.triple_extractor_step2.run(
    storage=self.storage.step(),
    input_key="raw_chunk",
    input_key_meta="entity",   # 与 entity_extractor output_key 一致
    output_key="triple",
)
```

---

## Issue #008 — `triple_type` 值错误导致 Prompt 与数据格式不匹配

**标题**：三元组全部返回空列表 / LLM 输出格式与解析逻辑不符

**症状关键词**：
- `triple_type`
- `triple` 列全为空列表 `[]`
- `KGTripleExtraction` / `KGTupleValidity`
- 无报错但输出为空

**根因**：

`KGTripleExtraction` 和 `KGTupleValidity` 均通过 `triple_type` 参数在 `__init__` 中选择 Prompt 类

**解决方案**：

```python
# ❌ 错误：拼写错误，prompt_template 未初始化
self.triple_extractor = KGTripleExtraction(
    llm_serving=self.llm_serving,
    triple_type="Relation",   # 大小写错误，既不触发 "attribute" 也不触发 "relation"
)

# ✅ 正确：只接受 "relation" 或 "attribute"（全小写）
self.triple_extractor = KGTripleExtraction(
    llm_serving=self.llm_serving,
    triple_type="relation",   # 关系型三元组
)
# 或
self.triple_extractor = KGTripleExtraction(
    llm_serving=self.llm_serving,
    triple_type="attribute",  # 属性型三元组
)
```

Pipeline 中两个算子的 `triple_type` 必须一致，否则 Prompt 和解析逻辑错位。

---

## Issue #009 — `merge_to_input=True` 导致下游步骤找不到输出列

**标题**：下游算子报 `Missing required column` / `merge_to_input` 后列名未变更

**症状关键词**：
- `merge_to_input`
- `Missing required column(s)`
- `KGTupleValidity`
- 下游步骤找不到 `valid_triple` 列

**根因**：

`KGTupleValidity` 的 `merge_to_input=True` 模式会将验证结果**原地覆盖** `input_key` 列（如 `"triple"`），而**不会**创建 `output_key`（如 `"valid_triple"`）列

**解决方案**：

```python
# ❌ 错误：merge_to_input=True 但下游用 "valid_triple" 列
self.validity_step = KGTupleValidity(
    llm_serving=self.llm_serving,
    merge_to_input=True,       # 结果写回 "triple" 列
)
self.validity_step.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="valid_triple",
)
# ↑ 下游若读 "valid_triple" → KeyError，"valid_triple" 列不存在

# ✅ 方式1：不使用 merge_to_input，让结果写入 output_key 新列
self.validity_step = KGTupleValidity(
    llm_serving=self.llm_serving,
    merge_to_input=False,      # 默认，结果写入 "valid_triple" 新列
)
self.validity_step.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="valid_triple",
)
# 下游用 input_key="valid_triple" 正常读取

# ✅ 方式2：使用 merge_to_input，下游也用原列名 "triple"
self.validity_step = KGTupleValidity(
    llm_serving=self.llm_serving,
    merge_to_input=True,       # 结果写回 "triple" 列
)
self.validity_step.run(
    storage=self.storage.step(),
    input_key="triple",
    output_key="valid_triple",
)
# 下游用 input_key="triple"（已被覆盖为过滤后的结果）
```

---

## 快速匹配表

| 报错关键词 | Issue 编号 |
|---|---|
| `Unexpected key 'xxx' in operator` | #001 |
| `No object named 'Xxx' found in 'operators' registry` | #002 |
| `KeyError` / `Missing required column` + Pipeline 上下文 | #003 |
| `You must call storage.step() before` | #004 |
| `DummyStorage` + `AttributeError` / `TypeError` | #005 |
| `ModuleNotFoundError` + `dataflow.operators.general_kg.xxx` | #006 |
| `Missing required column(s)` + `input_key_meta` / `KGTripleExtraction` | #007 |
| `triple` 列全为空 / `AttributeError: 'KGTripleExtraction' object has no attribute 'prompt_template'` | #008 |
| `Missing required column(s): ['valid_triple']` + `merge_to_input` | #009 |

---

*本文件由 dataflow-kg-dev skill 维护，新增 Issue 时请同步更新快速匹配表。*