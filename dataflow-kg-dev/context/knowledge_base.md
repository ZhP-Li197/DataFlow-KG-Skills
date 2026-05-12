# DataFlow-KG 知识库（Knowledge Base）

> 仓库：https://github.com/OpenDCAI/DataFlow-KG.git
> 官方文档：https://zhp-li197.github.io/DataFlow-KG-Doc/zh/
> 本文件用于在无上下文情况下理解、使用和开发 DataFlow-KG。
> **此文件为只读参考**，如需更新请通过 SKILL.md 的"知识库更新感知流程"操作。

---

## 一、项目总体概述

DataFlow-KG 是面向**知识图谱（Knowledge Graph）**的 LLM 驱动数据处理系统，基于 DataFlow 生态构建，核心定位：

- 从原始文本**抽取、验证、精化、评估**结构化知识图谱数据
- 支持通用 KG、常识 KG、时序 KG、超关系 KG、多模态 KG、Graph RAG、图推理及多种领域 KG（金融/医学/地理/法律/学术）
- Python 要求：`>= 3.10`
- 当前版本：`0.9.4`（`dataflow/version.py`）
- CLI 命令：`dfkg`
- 包名：`dataflow-kg`（PyPI ）（`pip install dataflow-kg`）

### 四大核心组成

| 组件 | 说明 |
|------|------|
| **算子（Operator）** | 原子性 KG 处理单元，支持 generate / filter / refine/ eval 四类（各模块按需包含） |
| **流水线（Pipeline）** | 有序连接算子，针对具体 KG 场景（构建/推理/检索/领域应用） |
| **提示词（Prompt）** | KG 结构化输出专用模板，支持三元组/四元组/QA 等多种格式 |
| **LLM Serving** | 统一封装本地模型和 API 推理 |

---

## 二、目录结构

```
DataFlow-KG/
├── dataflow/
    ├── __init__.py              # 包入口；导出 utils、version、logger、operators、prompts
    ├── version.py               # 版本号 0.9.4
    ├── logger.py                # 日志系统（colorlog，自定义 SUCCESS 级别）
    ├── cli.py                   # CLI 入口（argparse）
    ├── core/					 # 抽象基类层
    │   ├── operator.py          # OperatorABC, get_operator()
    │   ├── llm_serving.py       # LLMServingABC
    │   ├── prompt.py            # PromptABC, DIYPromptABC, @prompt_restrict 装饰器
    │   ├── wrapper.py           # WrapperABC
    │   └── __init__.py          # 导出 OperatorABC, LLMServingABC, OPERATOR_CLASSES等
    ├── pipeline/
    │   ├── Pipeline.py          # PipelineABC（op_runtimes, logger, op_nodes_list等）
    │   ├── nodes.py             # OperatorNode, KeyNode（DAG 节点）
    │   └── __init__.py          # 导出 PipelineABC
    ├── wrapper/
    │   ├── auto_op.py           # AutoOP, OPRuntime（Pipeline compile() 核心）
    │   ├── batch_wrapper.py     # BatchWrapper（批处理包装器）
    │   └── __init__.py
    ├── utils/
    │   ├── registry.py          # Registry + LazyLoader（核心注册机制）
    │   ├── storage.py           # DataFlowStorage(ABC), FileStorage, DummyStorage 等
    │   ├── utils.py             # pipeline_step(), merge_yaml()
    │   ├── __init__.py          # 导出 OPERATOR_REGISTRY
    │   ├── core_kg/
    │   │   └── embedding_serving.py   # KG 专用向量检索 Serving
    │   └── diverse_kg/
    │       └── wikidata_client.py     # Wikidata 外部知识库查询客户端
    ├── serving/						# LLM/VLM 服务封装
    │   ├── api_llm_serving_request.py      # 通用 HTTP API（OpenAI 兼容）
    │   ├── api_vlm_serving_openai.py        # VLM OpenAI API
    │   ├── api_google_vertexai_serving.py   # Google Vertex AI
    │   ├── lite_llm_serving.py              # LiteLLM 多提供商
    │   ├── local_model_llm_serving.py       # vLLM / SGLang 本地 LLM
    │   ├── local_model_vlm_serving.py       # 本地 VLM（视觉语言模型）
    │   ├── localmodel_lalm_serving.py       # 本地 LALM（大型音频语言模型）
    │   ├── localhost_llm_api_serving.py     # 本地 HTTP API 转发
    │   ├── LocalSentenceLLMServing.py       # sentence-transformers Embedding
    │   ├── light_rag_serving.py             # LightRAG 集成
    │   ├── google_api_serving.py            # Google PerspectiveAPI
    │   └── __init__.py                      # 导出全部 Serving 类
    ├── operators/
    │   ├── __init__.py
    │   ├── general_kg/          # 通用 KG 算子
    │   │   ├── generate/        # 实体/三元组抽取、推理、QA 生成、tuple→text
    │   │   ├── filter/          # 实体/三元组验证、去重、采样、子图过滤
    │   │   ├── eval/            # 三元组一致性/强度/拓扑评估，子图评估，QA 质量评估
    │   │   └── refinement/      # 实体对齐/分类/消歧/归一化，三元组消歧
    │   ├── commonsense_kg/      # 常识 KG 算子
    │   │   ├── generate/        # 三元组抽取、关系 QA 生成
    │   │   ├── filter/          # 适应性/合理性过滤、集合采样
    │   │   ├── eval/            # 适应性/合理性评估
    │   │   └── refine/          # 概念泛化
    │   ├── temporal_kg/         # 时序 KG 算子
    │   │   ├── generate/        # 四元组抽取/合并、对话/路径/子图 QA 生成
    │   │   ├── filter/          # 时间采样
    │   │   ├── eval/            # 时间统计
    │   │   └── refinement/      # 四元组消歧
    │   ├── hyper_relation_kg/   # 超关系 KG 算子
    │   │   ├── generate/        # 超关系三元组抽取、路径/子图 QA 生成
    │   │   ├── filter/          # 属性/完整性/一致性过滤
    │   │   └── eval/            # 一致性/完整性/属性频率评估
    │   ├── multi_model_kg/      # 多模态 KG 算子
    │   │   ├── generate/        # 视觉三元组抽取、路径/子图 QA 生成
    │   │   ├── filter/          # 路径/子图采样
    │   │   └── refine/          # 实体链接至数据库/图片 URL
    │   ├── pdf2text/           # KG pipeline 的上游预处理层
    │   │   ├── generate/        # 原始文档（PDF/URL）转结构化文本算子
    │   ├── graph_rag/           # Graph RAG 算子
    │   │   ├── generate/        # 子图 Prompt 生成、查询实体抽取、答案生成
    │   │   ├── filter/          # 答案合理性/token 数过滤
    │   │   └── eval/            # 答案真实性/合理性/token 数/问题难度评估
    │   ├── graph_reasoning/     # 图推理算子
    │   │   ├── generate/        # 推理路径搜索、约束路径搜索、关系生成
    │   │   ├── filter/          # 路径长度/冗余过滤
    │   │   └── eval/            # 路径长度/冗余评估
    │   └── domain_kg/		     # 领域KG算子
    │       ├── financial_kg/    # 金融 KG
    │       ├── geospatial_kg/   # 地理时序 KG
    │       ├── legal_kg/        # 法律 KG
    │       ├── medical_kg/      # 医学 KG
    │       ├── scholar_kg/      # 学术 KG
    │       └── utils/           # 各领域本体加载工具（load_*_ontology, ontology_filtering）
    ├── prompts/
    │   ├── core_kg/                         # 通用 KG Prompt
    │   ├── application_kg/                  # 应用型 Prompt
    │   ├── diverse_kg/                      # 领域 Prompt
    │   └── __init__.py
    ├── statics/
    │   └── pipelines/
    │       ├── __init__.py
    │       └── api_pipelines/               # 开箱即用 Pipeline 脚本（可直接 python 运行）
    ├── example/                             # Pipeline 示例输入数据（（json）
    └── cli_funcs/                           # CLI 子命令实现
```

---

## 三、核心抽象层（`dataflow/core/`）

### 3.1 OperatorABC

所有 KG 算子的抽象基类（`dataflow/core/operator.py`）：

```python
class OperatorABC(ABC):
    def __init__(self):
        self.logger = get_logger()
        self.ALLOWED_PROMPTS = tuple([type[DIYPromptABC | PromptABC]])
    
    @abstractmethod
    def run(self) -> None:
        pass
```

**KG 算子实现规范**：

1. 继承 `OperatorABC`，调用 `super().__init__()` 
2. ，用 `@OPERATOR_REGISTRY.register()` 装饰器注册（必须在类定义上方）
3. `__init__` 接收配置参数（如 `llm_serving`, `lang`, `triple_type` 等）
4. 实现 `run(self, storage: DataFlowStorage, input_key: str, ...)` 方法
5. `run()` 参数命名：主输入 `input_key`，辅助输入 `input_key_meta`/`input_key_xxx`，输出 `output_key`
6. `run()` 必须调用 `storage.read("dataframe")` 和 `storage.write(df)`
7. `run()` 返回输出 key 列表
8. 包含 `@staticmethod get_desc(lang: str = "en") -> tuple` 方法，返回描述算子功能的 tuple，支持 zh/en
9. 实现 `_validate_dataframe()` 方法，检查输入列存在、输出列不冲突
10. LLM 驱动算子持有 Serving 的成员变量必须命名为 `self.llm_serving`

### 3.2 LLMServingABC

所有 LLM 服务的抽象基类（`dataflow/core/llm_serving.py`）：

```python
class LLMServingABC(ABC):
    @abstractmethod
    def generate_from_input(self, user_inputs: List[str], system_prompt: str) -> List[str]: ...
    @abstractmethod
    def start_serving(self): ...
    @abstractmethod
    def cleanup(self): ...
    def load_model(self, model_name_or_path: str, **kwargs): ...
```

### 3.3 WrapperABC

包装器的抽象基类，用于对算子进行包装增强（`dataflow/core/wrapper.py`）。

### 3.4 Prompt 系统

```python
# PromptABC：标准 KG Prompt 基类
class PromptABC:
    def build_prompt(self): ...

# DIYPromptABC：用户自定义 Prompt 基类，继承 PromptABC，子类可绕过 @prompt_restrict 白名单检查
class DIYPromptABC(PromptABC): ...

# @prompt_restrict装饰器：限制算子允许使用的 Prompt 类型
# 注意：使用时必须在类定义上方，不能放在其他函数上方
@prompt_restrict(
    KGRelationTripleExtractionPrompt,
    KGAttributeTripleExtractionPrompt
)
@OPERATOR_REGISTRY.register()
class KGTripleExtraction(OperatorABC):
```

---

## 四、Pipeline 系统（`dataflow/pipeline/`）

### 4.1 一种 Pipeline 基类

 `pipeline/__init__.py` 只导出 `PipelineABC`，`forward()` 运行一次

### 4.2 两种合法开发风格

DataFlow -KG存在两种合法风格，不可混用。

**风格 A：继承 PipelineABC（适合需要 compile() / DAG 可视化的场景）**

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
import os

class MyPipeline(PipelineABC):
    def __init__(self, first_entry_file_name: str, llm_serving, lang: str = "en"):
        super().__init__()   # ← PipelineABC 子类必须调用
        self.storage = FileStorage(
            first_entry_file_name=first_entry_file_name,
            cache_path="./cache",
            file_name_prefix="graph_rag_pipeline_step",
            cache_type="json",
        )
        self.op_step1 = KGGraphRAGQueryExtraction(llm_serving=llm_serving, lang=lang)
        self.op_step2 = KGGraphRAGSubgraphRetrieval()

    def forward(self):
        self.op_step1.run(storage=self.storage.step(), input_key="question", ...)
        self.op_step2.run(storage=self.storage.step(), ...)

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

**风格 B：纯类封装（不继承任何基类 **）

```python
# 对标kg_extaction_pipeline.py / KGExtractionPipeline
class KGExtractionPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="input.json",
            cache_path="./cache",
            file_name_prefix="pipeline_step",
            cache_type="json",
        )
        self.op1 = KGTripleExtraction(llm_serving=llm_serving)
        self.op2 = KGEntityExtraction(llm_serving=llm_serving)

    def forward(self):
        self.op1.run(storage=self.storage.step(), input_key="text")
        self.op2.run(storage=self.storage.step(), input_key="text")

if __name__ == "__main__":
    pipeline = KGExtractionPipeline()
    pipeline.forward()
```

**选择建议**：
-  需要 `compile()` 工作流（key 合法性校验、`draw_graph()` DAG 可视化、  多 LLM Serving 自动切换释放、`resume_step` 断点续传） → 风格 A
- 单一 LLM Serving、快速实验、配置简单固定 → 风格 B

### 4.3 Pipeline 编译机制（风格 A 专用）

`compile()` 过程：

1. 将所有 `OperatorABC` 成员变量替换为 `AutoOP` 包装
2. 执行 `forward()` 记录所有 `OPRuntime`（不实际运行算子）
3. 调用 `_build_operator_nodes_graph()` 构建有向无环图（DAG）
4. 验证 key 完整性：每个算子的 `input_*` key 必须在上游算子的 `output_*` key 或初始数据集列中存在
5. Key 验证失败会抛出 `KeyError` 并打印详细信息

### 4.4 DAG 可视化（风格A专用）

```python
pipeline.compile()
pipeline.draw_graph(port=8080, hide_no_changed_keys=True)
# 需要安装: pip install pyvis
```

---

## 五、存储系统（`dataflow/utils/storage.py`）

### 5.1 存储类型

| 类名 | 说明 | 适用场景 |
|------|---------|------|
| `FileStorage` | 每次 read/write 立即落盘 | 通用，简单可靠 |
| `DummyStorage` | 纯内存，不落盘 | **仅供 BatchWrapper 内部使用**，不要用于 Pipeline |
| `LazyFileStorage` | 内存中操作，进程退出时落盘（原子写） | 高性能，防止部分写 |

### 5.2 FileStorage 使用

```python
from dataflow.utils.storage import FileStorage

storage = FileStorage(
    first_entry_file_name="./data/input.jsonl",   # 初始数据文件
    cache_path="./cache",                          # 中间结果目录
    file_name_prefix="dataflow_cache_step",        # 缓存文件前缀
    cache_type="jsonl"                             # 缓存格式: json/jsonl/csv/parquet/pickle
)
```

`first_entry_file_name` 支持：

- 本地文件路径：`./data/input.jsonl`
- HuggingFace：`hf:openai/gsm8k:main:train`
- ModelScope：`ms:modelscope/gsm8k:train`

KG 扩展参数：

```python
# 指定路径读取，绕过 step 机制
storage.read(output_type="dataframe", file_path="./some/other.jsonl")

# 写入到指定路径，或写当前 step 而非 step+1
storage.write(df, file_path="./output/custom.jsonl")
storage.write(df, use_current_step=True)

```

### 5.3 storage.step() 正确用法

```python
# Pipeline forward() 中：每次 op.run() 时传入（自动递增）
self.op1.run(storage=self.storage.step(), ...)   # -1 → 0
self.op2.run(storage=self.storage.step(), ...)   # 0 → 1

# 独立测试脚本中：手动推进一次再传 storage 本身
storage = FileStorage("input.jsonl", cache_path="./cache")
storage.step()                                   # 手动推进：-1 → 0
op.run(storage=storage, input_key="raw_chunk")   # 不要再传 storage.step()
```

### 5.4 LazyFileStorage 推荐配置

```python
from dataflow.utils.storage import LazyFileStorage

storage = LazyFileStorage(
    first_entry_file_name="input.jsonl",
    cache_path="./cache",
    file_name_prefix="pipeline_cache",
    cache_type="jsonl",
    save_on_exit=True,      # 进程退出时自动 flush
    flush_all_steps=False   # 只保留最新步骤（节省磁盘）
)
```

***

## 六、LLM Serving 系统（`dataflow/serving/`）

### 6.1 可用 Serving 实现：

| 类名 | 说明 |
|------|------|
| `APILLMServing_request` | 通用 HTTP API，支持 OpenAI 兼容接口，多线程并发 |
| `LiteLLMServing` | 基于 LiteLLM，支持多提供商 |
| `LocalModelLLMServing_vllm` | 本地 vLLM 推理 |
| `LocalModelLLMServing_sglang` | 本地 SGLang 推理 |
| `LocalHostLLMAPIServing_vllm` | 本地已启动的 vLLM API |
| `LocalModelLALMServing_vllm` | 本地 LALM（大型音频语言模型）推理 |
| `APIVLMServing_openai` | 视觉语言模型 API |
| `LocalVLMServing_vllm` | 本地 VLM（vLLM）服务 |
| `LocalEmbeddingServing` | 本地 Sentence Embedding |
| `LightRAGServing` | LightRAG 服务 |
| `APIGoogleVertexAIServing` | Google Vertex AI API |
| `PerspectiveAPIServing` | Google Perspective API |

### 6.2 APILLMServing_request 使用

```python
import os
os.environ["DF_API_KEY"] = "your-api-key"  # API key 必须通过环境变量注入，禁止硬编码

from dataflow.serving import APILLMServing_request

serving = APILLMServing_request(
    api_url="https://api.openai.com/v1/chat/completions",
    key_name_of_api_key="DF_API_KEY",   # 环境变量名
    model_name="gpt-4o",
    temperature=0.0,
    max_workers=10,      # KG pipeline 实际用 8–20，根据 API 限速调整
    max_retries=5,
)

responses = serving.generate_from_input(
    user_inputs=["问题1", "问题2"],
    system_prompt="You are a helpful assistant",
    json_schema=None   # 可选，结构化输出
)
```

**max_workers 选择指南**：

| API 情况                          | 推荐 max_workers |
| --------------------------------- | ---------------- |
| 官方 OpenAI / DeepSeek（有限速）  | 8-20             |
| 自建/代理 API（无严格限速）       | 20-30            |
| 本地 vLLM / VLM（多模态，推理重） | 4-10             |

默认值 10 在 KG 场景下基本合理，KG pipeline 最高只用到 30，KG 算子的 LLM 调用通常比文本过滤算子更重（需要结构化输出解析），并发过高容易导致 API 超时或响应质量下降。

### 6.3 Serving 生命周期

- Pipeline 使用引用计数（`llm_serving_counter`）管理 Serving 生命周期
- **不要在算子中手动调用 `serving.cleanup()`**，由 Pipeline 自动管理
- 算子中持有 Serving 的成员变量**必须命名为 `self.llm_serving`**

---

## 七、算子注册系统（`dataflow/utils/registry.py`）

### 7.1 Registry 机制

```python
from dataflow.utils.registry import OPERATOR_REGISTRY
from dataflow.utils.registry import PROMPT_REGISTRY

@OPERATOR_REGISTRY.register()
class MyKGFilter(OperatorABC): ...

@PROMPT_REGISTRY.register()
class MyKGPrompt(PromptABC): ...
```

### 7.2 LazyLoader 机制与 import 路径

每个算子子模块的 `__init__.py` 采用 LazyLoader 模式，将所有子包算子**扁平注册**到父模块命名空间：

```python
# ✅ 正确：从父模块 import
from dataflow.operators.graph_rag import KGGraphRAGGetAnswer
from dataflow.operators.commonsense_kg import CSKGTripleAdaptabilityEvaluator

# ❌ 错误：直接用子包路径（会绕过 LazyLoader，报 ModuleNotFoundError）
from dataflow.operators.general_kg.generate.kg_entity_extractor import KGEntityExtraction
```

**新增算子必须**在对应模块 `__init__.py` 的 `TYPE_CHECKING` 块中声明：

```python
if TYPE_CHECKING:
    from .filter.my_new_filter import MyNewFilter
```

**验证已注册的算子**：

```python
import dataflow.operators.graph_reasoning as r
print(r._import_structure)  # 查看 LazyLoader 管理的所有类名
```

---

## 八、KG 算子分类与功能概述

### 8.1 `general_kg`（通用 KG）

```python
from dataflow.operators.general_kg import KGEntityExtraction, KGTripleExtraction, ...
```

**Generate**：`KGEntityExtraction`、`KGTripleExtraction`、`KGRelationTripleInference`、`KGAttributeTripleQAGeneration`、`KGRelationTripletDialogueQAGeneration`、`KGRelationTriplePathQAGeneration`、`KGRelationTripleSubgraphQAGeneration`、`KGTripleMerger`、`KGTupleTextGeneration`

**Filter**：`KGTupleRemoveRepeated`、`KGTupleValidity`、`KGTupleSubjectObjectCleaner`、`KGTupleIsolatedNodeFilter`、`KGTupleRelationNormalizer`、`KGTupleEntityLinker`、`KGTupleEntityLinkerByID`、`KGTupleEntityTypeFilter`、`KGTupleRelationTypeFilter`、`KGTupleAttributeFilter`、`KGTupleTemporalFilter`、`KGTupleConfidenceFilter`、`KGTupleLanguageFilter`

**Refinement**：`KGTripleSchemaAlignment`、`KGTripleAmbiguityResolver`、`KGTripleTextualRepresentation`、`KGTupleTranslation`、`KGTripleCanonicalization`、`KGTripleDecontextualization`、`KGTripleSelfContained`

**Eval**：`KGTripleHallucinationEvaluator`、`KGTripleHallucinationEvaluatorV2`、`KGTripleLogicalConsistencyEvaluator`、`KGTripleNoveltyEvaluator`、`KGTripleRelationSimilarityEvaluator`、`KGTripleSubgraphDensityEvaluator`、`KGTripleTemporalConsistencyEvaluator`、`KGTripleTypeConsistencyEvaluator`、`KGTripleUniquenessEvaluator`、`KGTripleHallucinationEvalPipeline`

---

### 8.2 `commonsense_kg`（常识 KG）

```python
from dataflow.operators.commonsense_kg import CSKGTripleExtraction, CSKGTripleFilter, ...
```

**Generate**：`CSKGTripleExtraction`、`CSKGTripleConceptExpansion`

**Filter**：`CSKGTripleFilter`、`CSKGTripleLanguageConsistencyFilter`、`CSKGTripleAdaptabilityEvaluator`

**Eval**：`CSKGTripleCoherenceEvaluator`、`CSKGTripleContextualRelevanceEvaluator`、`CSKGTripleLanguageConsistencyEvaluator`

---

### 8.3 `temporal_kg`（时序 KG）

```python
from dataflow.operators.temporal_kg import TKGTupleExtraction, TKGTupleMerger, ...
```

**Generate**：`TKGTupleExtraction`、`TKGAttributeQAGeneration`、`TKGTupleSubgraphQAGeneration`、`TKGTuplePathQAGeneration`、`TKGRelationTupleDialogueQAGeneration`、`TKGTupleMerger`

**Refinement**：`TKGTupleDisambiguation`

**Filter**：`TKGTupleTimeFilter`

**Eval**：`TKGTemporalStatistics`

---

### 8.4 `graph_reasoning`（图推理）

```python
from dataflow.operators.graph_reasoning import KGReasoningTripleExtraction, KGReasoningPathSampling, ...
```

**Generate**：`KGReasoningTripleExtraction`、`KGReasoningPathSampling`、`KGReasoningQuestionGeneration`

**Filter**：`KGReasoningPathFilter`、`KGReasoningConstrainedPathSearch`、`KGReasoningPathRedundancyFilter`

**Eval**：`KGReasoningAnswerEvaluation`

---

### 8.5 `graph_rag`（Graph RAG）

```python
from dataflow.operators.graph_rag import KGGraphRAGTripleExtraction, KGGraphRAGEntityExtraction, ...
```

**Generate**：`KGGraphRAGTripleExtraction`、`KGGraphRAGEntityExtraction`、`KGGraphRAGAnswerGeneration`

**Filter**：`KGGraphRAGNodeFilter`、`KGRAGAnswerTokenFilter`

**Eval**：`KGGraphRAGAnswerEvaluation`、`KGGraphRAGAnswerLLMEvaluation`

---

### 8.6 其他算子模块

| 模块 | 内容 |
|------|------|
| `pdf2text` | PDF/URL 转 Markdown 及文本分块预处理（MinerU、trafilatura、chonkie） |
| `hyper_relation_kg` | 超关系（N-ary）KG 四元组抽取、限定词过滤与一致性评估 |
| `multi_model_kg` | 多模态 KG 图像描述生成、跨模态三元组抽取与实体链接 |
| `domain_kg/financial_kg` | 金融领域相关算子 |
| `domain_kg/medical_kg` | 医学领域 相关算子 |
| `domain_kg/geospatial_kg` | 地理空间 相关算子 |
| `domain_kg/legal_kg` | 法律领域相关算子 |
| `domain_kg/scholar_kg` | 学术领域相关算子 |

---
## 九、Prompt 系统（`dataflow/prompts/`）

### 9.1 注册与使用

```python
from dataflow.utils.registry import PROMPT_REGISTRY
from dataflow.core.prompt import PromptABC

@PROMPT_REGISTRY.register()
class MyPrompt(PromptABC):
    def __init__(self, custom_param="default"):
        self.custom_param = custom_param

    def build_prompt(self, content: str) -> str:
        return f"System: {self.custom_param}\nUser: {content}"
```

### 9.2 `@prompt_restrict` 装饰器与 `DIYPromptABC`

```python
from dataflow.core.prompt import prompt_restrict, DIYPromptABC

# 限制算子只能接受特定 Prompt 类型
@prompt_restrict(MyPrompt)          # ← 必须紧贴类定义上方
@OPERATOR_REGISTRY.register()       # ← 两个装饰器顺序可互换，但都要紧贴
class MyOperator(OperatorABC): ...

# 用户自定义 Prompt，可绕过白名单
class MyCustomPrompt(DIYPromptABC):
    def build_prompt(self, content: str) -> str:
        return f"Custom: {content}"
```

### 9.3 KG 输出格式约定

- 三元组/四元组 → 标签字符串列表，`<标签> 值` 拼接
- QA → 对象列表，`{"question": ..., "answer": ...}`
- key 名由具体 Prompt 的业务语义决定（`triple` / `inferred_triple` / `tuple` / `QA_pairs`

**① 关系三元组 / 属性三元组 → `triple`**

统一格式：`<标签> 值` 依次拼接，空格分隔。关系三元组和属性三元组共用同一 key：

```json
{"triple": [
    "<subj> Henry <obj> Maria Rodriguez <rel> is_trained_by",
    "<subj> AlphaFold <obj> protein structure <rel> predicts"
]}

```

**② 推理三元组 → `inferred_triple`**

格式与 `triple` 完全相同，仅 key 不同，语义上表示"从已有三元组逻辑推断出的新三元组"：

```python
{"inferred_triple": [
    "<subj> subject <obj> object <rel> relation"
]}
```

**③ 时序四元组 → `tuple`**

在三元组基础上追加 `<time>` 标签；若文本中无明确时间则填 `NA`：

```python
{"tuple": [
    "<subj> Entity <obj> Entity <rel> Relation <time> 2025-03-03",
    "<subj> Entity <obj> Entity <rel> Relation <time> 2025-01-01|2025-01-03",
    "<subj> Entity <obj> Entity <rel> Relation <time> NA"
]}
```

**④ 问答对 → `QA_pairs`**

**对象列表**，每个对象包含 `question` 和 `answer` 两个 key：

```python
{"QA_pairs": [
    {"question": "Who trained Henry?", "answer": "Maria Rodriguez"},
    {"question": "What does AlphaFold predict?", "answer": "protein structure"}
]}
```

---

## 十、日志系统

```python
from dataflow import get_logger
logger = get_logger()

logger.info("info")
logger.warning("warning")
logger.error("error")
```

---

## 十一、CLI 系统

DataFlow-KG 使用 `dfkg` 命令:

```bash
dfkg  --version               
dfkg env                          
dfkg init                         
dfkg eval init / api / local
dfkg pdf2model init/train               
dfkg text2model init/train              
dfkg webui --host 0.0.0.0 --port 7862       
```

---

## 十二、KG 常见设计模式

### 模式 1：纯规则过滤

```python
@OPERATOR_REGISTRY.register()
class MyKGFilter(OperatorABC):
    def __init__(self, lang: str = "en"):
        self.logger = get_logger()
        self.lang = lang

    def run(self, storage: DataFlowStorage,
            input_key: str = "triple",
            output_key: str = "triple") -> list:
        self.input_key = input_key
        self.output_key = output_key
        df = storage.read("dataframe")
        self._validate_dataframe(df)
        df[output_key] = df[input_key].apply(lambda x: ...)
        storage.write(df)
        return [output_key]
```

### 模式 2： LLM 驱动算子

```python
@prompt_restrict(MyKGPrompt)
@OPERATOR_REGISTRY.register()
class MyKGOperator(OperatorABC):
    def __init__(self, llm_serving: LLMServingABC, lang: str = "en"):
        self.logger = get_logger()
        self.llm_serving = llm_serving    # 必须用此名
        self.prompt_template = MyKGPrompt(lang=lang)

    def run(self, storage: DataFlowStorage,
            input_key: str = "raw_chunk",
            output_key: str = "triple") -> list:
        df = storage.read("dataframe")
        prompts = [self.prompt_template.build_prompt(text=row[input_key])
                   for _, row in df.iterrows()]
        raw_outputs = self.llm_serving.generate_from_input(
            prompts, system_prompt=self.prompt_template.system_text)
        # KG 输出为 JSON，必须解析
        df[output_key] = [json.loads(r).get("triple", []) if r else []
                          for r in raw_outputs]
        storage.write(df)
        return [output_key]

```

### 模式 3：多输出 key 算子

```python
def run(self, storage, input_key, output_key1="triple", output_key2="entity_class") -> list:
    ...
    df[output_key1] = ...
    df[output_key2] = ...
    storage.write(df)
    return [output_key1, output_key2]
```

### 模式4：运行时本体传参（领域 KG 专用）

```python
 def run(self, storage, input_key="raw_chunk", output_key="triple") -> list:
        df = storage.read("dataframe")
        ontology = self._load_ontology(...)
        self.prompt_template.build_system_prompt(ontology)  # ← 领域 KG 独有
        prompts = [self.prompt_template.build_prompt(text=row[input_key])
                   for _, row in df.iterrows()]
        raw_outputs = self.llm_serving.generate_from_input(
            prompts, system_prompt=self.prompt_template.system_text)
        df[output_key] = [json.loads(r).get("triple", []) if r else []
                          for r in raw_outputs]
        storage.write(df)
        return [output_key]
```

***

## 十三、安装说明

```bash
# 用户安装
pip install dataflow-kg

# 开发者安装（可编辑模式）
git clone https://github.com/OpenDCAI/DataFlow-KG.git
cd DataFlow-KG
pip install -e .

# GPU 后端
pip install dataflow-kg[vllm]     # vLLM（>=0.7.0,<=0.9.2）
pip install dataflow-kg[vllm07]   # vLLM 0.7.x
pip install dataflow-kg[vllm08]   # vLLM 0.8.x
pip install dataflow-kg[sglang]   # SGLang
pip install dataflow-kg[litellm]  # LiteLLM
```

---

## 十四、项目来源与生态

- **主仓库**：https://github.com/OpenDCAI/DataFlow-KG
- **文档**：https://zhp-li197.github.io/DataFlow-KG-Doc/zh/

*最后同步：2026-05-09    如需更新算子列表，运行 SKILL.md 中的 "知识库更新感知流程 "*