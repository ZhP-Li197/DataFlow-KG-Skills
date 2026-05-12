# DataFlow-KG 开发规范、问题记录与最佳实践

> 来源：OpenDCAI/DataFlow-KG 主仓库开发经验（持续更新）
> **此文件为可追加文档**：发现新规范/新坑时，通过 SKILL.md 的更新流程在末尾追加条目。

---

## 一、开发规范

### 1.1 分支与版本管理

- **工作仓库**：`https://github.com/OpenDCAI/DataFlow-KG`（`main` 分支）
- 开发新特性请从 `main` 分支新建特性分支，PR 合并回 `main`

### 1.2 算子开发规范

#### 必须遵守

1. **继承 `OperatorABC`**，调用 `super().__init__()` 
2. **注册算子**：`@OPERATOR_REGISTRY.register()` 装饰器加在类定义上（不能错位到其他函数上）
3. **`run()` 参数命名约定**（Pipeline 编译依赖此规则）：
   - 输入 key 参数以 `input_` 开头，值为 DataFrame 列名字符串
   - 输出 key 参数以 `output_` 开头，值为 DataFrame 列名字符串
   - 辅助输入列命名为 `input_key_meta`（或 `input_key_xxx`）
   - `storage` 参数必须存在（第一个参数或关键字参数），类型为 `DataFlowStorage`
4. **`run()` 必须返回输出 key 列表**，如 `return [output_key]` 或 `return [output_key1, output_key2]`
5. **`run()` 必须调用 `storage.read("dataframe")` 和 `storage.write(df)`**
6. **在 `__init__.py` 的 `TYPE_CHECKING` 块声明导入**，否则 LazyLoader 无法发现算子
7. **LLM 驱动算子：`generate_from_input` 返回 `list[str]` 原始 JSON 字符串，必须逐条 `json.loads()` 解析后再赋值给 `df[output_key]`**

#### 强烈建议

8. 在 `run()` 中用 `self.logger.info(...)` 记录关键步骤

9. 实现 `@staticmethod get_desc(lang: str = "zh")` 方法，支持 `zh`/`en` 两种语言，返回**tuple**


#### 文件命名约定

- **Generate（抽取）** 文件名：`kg_xxx_extractor.py`，类名：`KGXxxExtraction`
- **Generate（生成）** 文件名：`kg_xxx_generator.py`，类名：`KGXxxGeneration`
- **Filter（过滤）** 文件名：`kg_xxx_filtering.py`，类名：`KGXxxFilter`
- **Filter（校验）** 文件名：`kg_xxx_validation.py`，类名：`KGXxxValidity`
- **Filter（采样）** 文件名：`kg_xxx_sampling.py`，类名：`KGXxxSampler`
- **Refinement** 文件名：`kg_xxx_normalization.py` / `kg_xxx_alignment.py` / `kg_xxx_disambiguation.py`，类名同义
- **Eval** 文件名：`kg_xxx_eval.py`，类名：`KGXxxEvaluator`

### 1.3 Pipeline 开发规范

1. 两种合法风格（**不要混用**）：
   - **风格 A**：继承 `PipelineABC`（适合需要 `compile()` / DAG 可视化）
   - **风格 B**：纯类封装（适合快速实验，KG 现有 example 实际采用此风格）
2. `storage` 在 `__init__` 中声明（不在 `forward()` 里临时创建）
3. 所有算子在 `__init__` 中实例化为**成员变量**（`compile()` 依赖此机制）
4. `forward()` 中每个算子调用使用独立的 `storage.step()` 副本
5. 推荐使用 `LazyFileStorage`替代 `FileStorage` 以获得原子落盘和更好的中断安全性
6. Pipeline 文件建议放在 `dataflow/statics/pipelines` 对应子目录或项目根目录下

### 1.4 Prompt 开发规范

1. 继承 `PromptABC`（标准）或 `DIYPromptABC`（绕过白名单限制）
2. 加上 `@PROMPT_REGISTRY.register()` 装饰器
3. 实现`build_prompt(self, ...) -> str`；
4. 结构化输出必须在 system prompt 中明确 JSON 格式（用 `<subj>` `<obj>` `<rel>` 标签标识每个字段），三元组统一使用标签字符串形式，JSON key 由具体prompt业务决定
5. 若算子需限制 Prompt 类型，在算子类上用 `@prompt_restrict(MyKGPrompt)`

### 1.5 LLM Serving 使用规范

1. **API key 必须通过环境变量注入**，禁止硬编码在代码中
   - 推荐环境变量名：`DF_API_KEY`（也可自定义）
2. 算子中持有 `llm_serving` 对象的成员变量**必须命名为 `self.llm_serving`**（Pipeline 通过此字段管理 Serving 生命周期）
3. 不要在算子内手动调用 `serving.cleanup()`，由 Pipeline 自动管理
4. **KG  `max_workers` 推荐值**：官方/受限 API 建议 8–20；自建/代理 API 可用 20–30。KG 算子结构化输出解析较重，并发过高容易导致 API 超时或响应质量下降

### 1.6 代码风格

- Python 3.10+，可使用 `X | Y` 类型注解语法
- 使用 type hints
- 日志使用 `self.logger`（`get_logger()` 获取），不使用 `print()`（开发调试可临时用 `print`）
- 异常处理中记录详细日志

### 1.7 算子复用原则（避免重复造轮子）

> **核心原则：开发新算子前，必须先检查仓库中是否已有功能相同或相近的 KG 算子，优先复用，而非重复实现。**

#### 检查已有算子的方法

1. **查阅各模块 `__init__.py` 的 `TYPE_CHECKING` 块**
2. **通过 OPERATOR_REGISTRY 动态查询**：
   ```python
   from dataflow.utils.registry import OPERATOR_REGISTRY
   OPERATOR_REGISTRY._get_all()
   print(OPERATOR_REGISTRY.get_obj_map())
   ```
3. **查阅 `knowledge_base.md` §八KG 算子分类与功能概述**

#### 复用示例

| 需求 | 不要重写 | 复用 |
|------|---------|------|
| 通用三元组抽取 | ❌ 新写 LLM 抽取逻辑 | ✅ 复用 `KGTripleExtraction` |
| 去除重复三元组 | ❌ 新写 | ✅ 复用 `KGTupleRemoveRepeated` |
| 三元组有效性校验 | ❌ 新写 | ✅ 复用 `KGTupleValidity` |
| 通用三元组 QA 生成 | ❌ 新写 | ✅ 复用 `KGAttributeTripleQAGeneration` |
| 时序四元组抽取 | ❌ 新写时序逻辑 | ✅ 复用 `TKGTupleExtraction` |
| 子图 QA 生成 | ❌ 新写 | ✅ 复用 `KGRelationTripleSubgraphQAGeneration` |

### 1.8 算子健壮性与容错规范

> **KG 算子依赖 LLM 输出结构化 JSON，必须做好充分的容错处理。**

#### 核心原则

1. **逐条容错**：对每个 LLM 返回值单独 try/except
2. **失败时记录日志**：使用 `self.logger.warning()` 记录原始输出和错误信息
3. **失败时给出合理默认值**：列表输出返回 `[]`，字符串输出返回 `""`，评估分数返回 `0`
4. **类型前置检查**：先检查 `response is None` 和 `isinstance(response, str)`

#### 标准容错模板

**模板 A：KG generate/filter 类算子——JSON 解析失败则返回空列表**
```python
def _parse_llm_response(self, response: str) -> list:
    try:
        # 推荐方式1：正则提取 {} 块（鲁棒性更强）
        json_str = re.search(r"\{.*\}", response, re.DOTALL).group()
        return json.loads(json_str).get("triple", [])   # key 由 Prompt 决定
    except Exception as e:
        self.logger.warning(f"Failed to parse LLM response: {e}")
        return []

# 推荐方式2：re.sub 清除代码块标记
def _parse_llm_response(self, response: str) -> list:
    try:
        cleaned = re.sub(r"```json|```", "", response).strip()
        return json.loads(cleaned).get("triple", [])
    except Exception as e:
        self.logger.warning(f"Failed to parse LLM response: {e}")
        return []

```

**模板 B：KG eval 类算子——解析失败则返回默认值（0/None）**

```python
def _parse_score(self, response: str) -> float:
    try:
        res_json = json.loads(...)
        judgment = res_json.get("judgment", "").upper()
        if judgment == "CONSISTENT":
            return 1.0
        return 0.0
    except Exception:
        return 0.0

```

**模板 C：JSON 清理辅助函数**
```python
def _clean_json_block(self, item: str) -> str:
    """去除模型输出中可能包裹的 ```json ... ``` 代码块标记"""
    return item.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
```

**模板 D：多层级正则降级策略（非结构化输出）**

```python
def _extract_json(self, response: str) -> dict:
    if not isinstance(response, str):
        return {}
    # 层级 1：严格匹配 ```json 代码块
    blocks = re.findall(r"```json\s*(.*?)\s*```", response, re.DOTALL)
    if blocks:
        try:
            return json.loads(blocks[-1].strip())
        except Exception:
            pass
    # 层级 2：匹配任意 ``` 代码块
    blocks = re.findall(r"```\s*(.*?)\s*```", response, re.DOTALL)
    if blocks:
        try:
            return json.loads(blocks[-1].strip())
        except Exception:
            pass
    # 层级 3：宽松匹配裸 JSON 对象
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {}

```

### 1.9 推理模型（CoT 模型）输出处理规范

> DeepSeek-R1 等 CoT 模型的 API 响应，DataFlow-KG Serving 层会自动包装为 `<think>...</think>\n<answer>...</answer>` 格式返回给算子。

#### 何时需要剥离 CoT

| 算子类型 | 是否需要剥离 |
|---------|------------|
| 三元组/实体/关系抽取（写入结构化字段） | ✅ 必须剥离 |
| QA 对生成（写入 `QA_pairs`） | ✅ 必须剥离 |
| 推理数据生成（写入 `generated_cot` 字段） | ❌ 不要剥离 |
| 评估算子（数值打分） | ✅ 必须剥离 |
| 分类/判别算子 | ✅ 必须剥离 |

#### 标准 CoT 剥离函数

```python
import re

def _strip_cot(self, response: str) -> str:
    """
    剥离 DeepSeek R1 等 CoT 模型输出中的 <think>...</think> 部分。
    若符合格式，返回 <answer> 内容；否则原样返回（兼容普通模型）。
    """
    if not isinstance(response, str) or response is None:
        return response
    pattern = r"<think>.*?</think>\s*<answer>(.*?)</answer>"
    match = re.search(pattern, response, re.DOTALL)  # 必须加 re.DOTALL
    if match:
        return match.group(1).strip()
    return response
```

### 1.10 KG 结构化输出格式规范

LLM 返回的 KG 数据统一使用**标签字符串**格式，`<标签> 值` 依次拼接，空格分隔：

| 输出类型 | JSON key | 格式示例 |
|---------|---------|---------|
| 关系三元组 | `triple` | <subj> X <obj> Y <rel> Z |
| 属性三元组 | `triple` | <entity> X <attribute> Y <value> Z |
| 推理三元组 | `inferred_triple` | 同关系三元组标签 |
| 时序四元组 | `tuple` | `<subj> X <obj> Y <rel> Z <time> T`（无时间填 `NA`） |
| 实体列表 | `entity` | `["entity1", "entity2", ...]`（无标签） |
| QA 对（基础/多跳） | `QA_pairs` | `[{"question": "...", "answer": "..."}]` |
| QA 对（集合型） | `QA_pairs` | `[{"question": "...", "answer": ["v1", "v2"]}]` |
| 多轮对话 | `dialogue` | `{constructed_path: [...], turns: [{turn_id, question, answer}]}` |
| 过滤/规范化后结果 | 各 Prompt 自定义（`valid_triple` / `normalized_triple` / `resolved_attribute`） | 与输入格式一致 |
| 自然语言文本 | 无 key | 纯文本字符串 |

---

## 二、已知问题

> 诊断用快速匹配表和根因分析统一维护在 `diagnostics/known_issues.md`，不在此处重复。
> 本文件 §一 的开发规范中已内联了最关键的注意事项（如 Issue #002 的 `__init__.py` 声明、Issue #004 的 `storage.step()` 用法等）。

---

## 三、开发经验与最佳实践

### 3.1 调试 Pipeline 编译（风格 A）

```python
pipeline = MyKGPipeline()
pipeline.compile()
for i, keys in enumerate(pipeline.accumulated_keys):
    print(f"After step {i}: {keys}")
pipeline.draw_graph()  # 需要 pip install pyvis；默认 port=0，可传 port=8080
```

### 3.2 快速测试 KG 算子（不走 Pipeline）

```python
from dataflow.operators.general_kg import KGTupleValidity
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

llm_serving = APILLMServing_request(...)
op = KGTupleValidity(llm_serving=llm_serving, triple_type="relation")
storage = FileStorage("test_data.json", cache_path="./test_cache")
storage.step()
op.run(storage, input_key="triple", output_key="valid_triple")

```

### 3.3 DummyStorage 用于单元测试

```python
from dataflow.utils.storage import DummyStorage
from dataflow.operators.general_kg import KGTupleRemoveRepeated
import pandas as pd

storage = DummyStorage()
storage.set_data(pd.DataFrame({
    "triple": [
        ["<subj> Alice <obj> Bob <rel> knows",
         "<subj> Alice <obj> Bob <rel> knows",   # 重复条目
         "<subj> Alice <obj> Carol <rel> works_with"]
    ]
}))
storage.operator_step = 0

op = KGTupleRemoveRepeated()
op.run(storage, input_key="triple", output_key="triple")
result = storage.read("dataframe")
```

### 3.4 LazyLoader import 路径速查

```python
# ✅ 正确：从父模块 import
from dataflow.operators.graph_rag import KGGraphRAGGetAnswer
from dataflow.operators.commonsense_kg import CSKGTripleAdaptabilityEvaluator

# ❌ 错误：直接用子包路径（会绕过 LazyLoader，报 ModuleNotFoundError）
from dataflow.operators.general_kg.generate.kg_entity_extractor import KGEntityExtraction
```

### 3.5 环境变量配置模板

```bash
export DF_API_KEY=sk-xxxxxxxxxxxx
export DF_API_URL=http://your-api/v1/chat/completions
export DF_MODEL_NAME=gpt-4o
export DF_MAX_WORKERS=10        # KG 场景推荐 8-20，自建 API 可适当提高
export DF_LOGGING_LEVEL=INFO    # DEBUG / INFO / WARNING / ERROR
```

---

## 四、待办与开发计划

- [ ] `dfkg init operator` CLI 命令尚未实现（目前输出 "not implemented yet"）
- [ ] `dfkg init pipeline` CLI 命令尚未实现
- [ ] `dfkg init prompt` CLI 命令尚未实现

---

## 五、KG Pipeline 开发实战指南

### 5.1 DataFlow-KG Pipeline 的标准风格（风格 B）

DataFlow-KG 现有 Pipeline 均采用**"类封装 + forward 串行调用"**风格：

```python
import os
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import KGEntityExtraction, KGTripleExtraction

class KGExtractionPipeline:
    def __init__(self, first_entry_file_name: str, lang: str = "en"):
        self.storage = FileStorage(
            first_entry_file_name=first_entry_file_name,
            cache_path="./cache",
            file_name_prefix="kg_pipeline_step",
            cache_type="jsonl",
        )
        self.llm_serving = APILLMServing_request(
            api_url=os.environ.get("DF_API_URL", "https://api.openai.com/v1/chat/completions"),
            key_name_of_api_key="DF_API_KEY",
            model_name=os.environ.get("DF_MODEL_NAME", "gpt-4o"),
            max_workers=20,   # KG 场景推荐 8-20
        )
        self.op_step1 = KGEntityExtraction(llm_serving=self.llm_serving, lang=lang)
        self.op_step2 = KGTripleExtraction(llm_serving=self.llm_serving, lang=lang)

    def forward(self):
        self.op_step1.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="entity",
        )
        self.op_step2.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            input_key_meta="entity",
            output_key="triple",
        )

if __name__ == "__main__":
    pipeline = KGExtractionPipeline(first_entry_file_name="./input.jsonl")
    pipeline.forward()
```

| 要点 | 说明 |
|------|------|
| `storage` 声明在 `__init__` | 不在 `forward()` 里临时创建 |
| `storage.step()` 在 `forward()` 里调用 | 每个算子调用传一次，自动递增 |
| 算子成员变量命名 | `self.op_stepN`，N 为执行顺序 |
| LLM Serving 统一声明 | 多个算子共享同一个 serving 实例 |

### 5.2 storage.step() 的正确用法

```python
# Pipeline forward() 中：每次 op.run() 时传入（自动递增）
self.op1.run(storage=self.storage.step(), ...)   # -1 → 0
self.op2.run(storage=self.storage.step(), ...)   # 0 → 1

# 独立测试脚本中：手动推进一次再传 storage 本身
storage = FileStorage("input.jsonl", cache_path="./cache")
storage.step()                                   # 手动推进：-1 → 0
op.run(storage=storage, input_key="raw_chunk")   # 不要再传 storage.step()
```

### 5.3  LazyLoader 与 import 路径

```python
# 从父模块 import
from dataflow.operators.general_kg import KGTripleExtraction, KGTupleValidity
from dataflow.operators.general_kg import KGAttributeTripleQAGeneration


# 验证 LazyLoader 管理的类名
import dataflow.operators.general_kg as kg
print(kg._import_structure)
```

### 5.4 领域 KG Pipeline（运行时本体模式）

医学/法律/金融等领域 KG 需要运行时传入本体，模式如下：

```python
from dataflow.operators.domain_kg.medical_kg import MedKGTripleExtraction
import json

class MedicalKGPipeline:
    def __init__(self, ontology_path: str, ...):
        ...
        self.op_step1 = MedKGTripleExtraction(llm_serving=self.llm_serving)
        self.ontology = json.load(open(ontology_path))

    def forward(self):
        # ontology_lists 直接传入本体 dict，算子内部调用 build_system_prompt(ontology_lists)
        self.op_step1.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="triple",
            ontology_lists=self.ontology,   # 传本体数据
        )

```

---

### 5.5  APILLMServing_request 并发配置

​     默认值 10 在 KG 场景下基本合理，KG pipeline 最高只用到 20，KG 算子的 LLM 调用通常比文本过滤算子更重（需要结构化输出解析），并发过高容易导致 API 超时或响应质量下降。

---

## 六、版本变更记录

| 日期 | 事件 |
|------|------|
| 2026-05-09 | 初始化 DataFlow-KG 开发规范文件，基于 DataFlow-KG v0.9.4 |
| 2026-05-09 | 新增 §1.10 KG 结构化输出格式规范（triple/inferred_triple/tuple/QA_pairs）|

---

*追加新条目时请在对应章节末尾添加，并在 §七 版本变更记录中注明日期和内容。*