# DataFlow-KG-Skills

用于 DataFlow-KG 知识图谱工作流的可复用 Agent Skills。

---

## 概览

本仓库包含针对 **DataFlow-KG** 知识图谱场景的专项技能集，覆盖 KG Pipeline 生成、算子引用、算子开发、Prompt 模板构建四大能力模块。

| Skill | 斜杠命令 | 核心能力 |
|---|---|---|
| `generating-dataflow-kg-pipeline` | `/generating-dataflow-kg-pipeline` | 从任务描述生成完整 KG Pipeline 代码 |
| `core_kg` | 被 Pipeline 生成器加载 | 所有核心 KG 算子的 API 参考文档 |
| `dataflow-kg-dev` | `/dataflow-dev` | KG 算子/Pipeline/Prompt 开发专家 |
| `prompt-template-builder` | `/prompt-template-builder` | 为 KG 算子生成 DIYPromptABC 模板类 |

---

## 前置条件：安装 Claude Code

### 安装 CLI

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# 或通过 npm
npm install -g @anthropic-ai/claude-code
# 网络较慢时使用国内镜像
npm install -g @anthropic-ai/claude-code --registry=https://registry.npmmirror.com
```

验证安装：

```bash
claude --version
```

### 添加本仓库中的 Skills

```bash
git clone https://github.com/haolpku/DataFlow-KG-Skills.git
mkdir -p ~/.claude/skills   # 个人级，所有项目可用

# 按需复制所需 skill
cp -r DataFlow-KG-Skills/generating-dataflow-kg-pipeline ~/.claude/skills/
cp -r DataFlow-KG-Skills/core_kg                         ~/.claude/skills/
cp -r DataFlow-KG-Skills/dataflow-kg-dev                 ~/.claude/skills/
cp -r DataFlow-KG-Skills/prompt-template-builder         ~/.claude/skills/
```

> Claude Code 从 `.claude/skills/<skill-name>/SKILL.md` 自动发现 Skills，`SKILL.md` frontmatter 中的 `name` 字段即斜杠命令名。

---

## `generating-dataflow-kg-pipeline`

推理引导式 KG Pipeline 规划工具，根据任务目标和样本数据自动生成标准 DataFlow-KG Pipeline 代码。

### 功能说明

给定**目标描述**和**样本 JSON 文件**（1–5 条代表性数据），该 Skill 将：

1. 读取并分析样本数据，推断字段类型、KG 类型信号与数据模态
2. 从决策表中选取匹配的 KG 算子链（通用 / 时序 / 多模态 / 超关系）
3. 校验算子间的字段依赖
4. 输出两阶段结果：算子决策 JSON → 完整可运行的 Python Pipeline 代码

### 快速上手

#### 1. 准备样本数据

KG Pipeline 使用 JSON 数组格式（而非 JSONL），每条记录为一个 JSON 对象：

```json
[
  {"raw_chunk": "2024年，苹果公司在旧金山发布了iPhone16。"},
  {"raw_chunk": "特斯拉于2023年在德克萨斯州开设新工厂。"}
]
```

#### 2. 调用 Skill

```
/generating-dataflow-kg-pipeline
Target: 从新闻文本中抽取时序知识图谱四元组，并生成路径问答对
Sample file: ./data/news.json
Expected outputs: QA_pairs
```

#### 3. 查看输出

1. **Stage 1 算子决策**：KG 类型、算子链、字段流转、选型理由（JSON）
2. **字段映射**：区分样本已有字段与需生成字段
3. **有序算子列表**：每个算子的 `run()` 调用与 `input_key`/`output_key`
4. **推理总结**：链路设计原因与权衡说明
5. **完整 Pipeline 代码**：遵循 `PipelineABC` 标准结构的可执行 Python 代码
6. **可调参数/注意事项**：`lang`、`triple_type`、`hop`、`qa_type` 等调优建议

### KG 类型检测规则

| 样本信号 | KG 类型 | 算子族 |
|---|---|---|
| 纯文本（`raw_chunk`） | 通用 KG | `general_kg` |
| 文本含时间戳/日期 | 时序 KG | `temporal_kg` |
| 文本 + 图像（`img_dict`/`vis_url`） | 多模态 KG | `multi_model_kg` |
| 含多元关系/属性限定词 | 超关系 KG | `hyper_relation_kg` |

### 算子选用决策表

| KG 类型 | 任务 | 算子链（按序） |
|---|---|---|
| 通用 | 文本 → KG 三元组 | `KGEntityExtraction` → `KGTripleExtraction` → `KGTupleNormalization` |
| 通用 | 路径问答 | 抽取链 → `KGRelationTuplePathGenerator` → `KGRelationTriplePathQAGeneration` |
| 通用 | 子图问答 | 抽取链 → `KGEntityBasedSubgraphSampling` → `KGRelationTripleSubgraphQAGeneration` |
| 通用 | 推理补全 | 抽取链 → `KGRelationTripleInference(merge_to_input=True)` |
| 时序 | 文本 → 四元组 | `TKGTupleExtraction(triple_type="relation")` |
| 时序 | 路径时序问答 | `TKGTupleExtraction` → `KGRelationTuplePathGenerator(input_key="tuple")` → `TKGTuplePathQAGeneration` |
| 多模态 | 文本+图像 → 多模态 KG + QA | `KGEntityExtraction` → `KGTripleExtraction` → `MMKGVisualTripleExtraction` → `MMKGEntityBasedSubgraphSampling` → `MMKGSubgraphBaseQAGeneration` |
| 超关系 | 文本 → 超元组 | `KGEntityExtraction` → `HRKGTripleExtraction` |
| 超关系 | 路径问答 | `KGEntityExtraction` → `HRKGTripleExtraction` → `KGRelationTuplePathGenerator(input_key="tuple")` → `HRKGRelationTriplePathQAGeneration` |

### 生成的 Pipeline 结构

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.general_kg import KGEntityExtraction, KGTripleExtraction

class MyKGPipeline(PipelineABC):
    def __init__(self):
        super().__init__()
        self.storage = FileStorage(
            first_entry_file_name="./data/input.json",
            cache_path="./cache",
            file_name_prefix="kg_pipeline_step",
            cache_type="json",
        )
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o-mini",
            max_workers=4,
        )
        self.step1_entity = KGEntityExtraction(self.llm_serving, lang="zh")
        self.step2_triple = KGTripleExtraction(self.llm_serving, triple_type="relation", lang="zh")

    def forward(self):
        self.step1_entity.run(storage=self.storage.step(), input_key="raw_chunk", output_key="entity")
        self.step2_triple.run(storage=self.storage.step(), input_key="raw_chunk", input_key_meta="entity", output_key="triple")

if __name__ == "__main__":
    pipeline = MyKGPipeline()
    pipeline.compile()
    pipeline.forward()
```

---

## `core_kg`

`generating-dataflow-kg-pipeline` 的扩展算子参考库，提供所有 DataFlow-KG 核心算子的逐算子 API 文档。

### 已文档化算子（✅）

**生成类（Generate）**

| 算子 | 说明 |
|---|---|
| `KGEntityExtraction` | 从文本中抽取实体，作为所有三元组抽取的锚点 |
| `KGTripleExtraction` | 给定文本与实体列表，抽取关系或属性三元组 |
| `KGRelationTripleInference` | 基于 LLM 的 KG 闭包推理，可合并回原三元组列 |
| `KGRelationTripleSubgraphQAGeneration` | 基于采样子图生成问答对 |
| `KGRelationTriplePathQAGeneration` | 基于 1/2 跳路径生成问答对 |
| `TKGTupleExtraction` | 从文本抽取带时间戳的四元组 |
| `TKGTuplePathQAGeneration` | 生成时序感知的路径问答（4 种 `qa_type`） |
| `MMKGVisualTripleExtraction` | 基于 VLM 从本地图像+实体列表抽取视觉三元组 |
| `MMKGSubgraphBaseQAGeneration` | 基于子图+图像生成多模态问答 |
| `HRKGTripleExtraction` | 抽取带限定词的超关系元组 |
| `HRKGRelationTriplePathQAGeneration` | 超关系路径问答生成 |

**过滤类（Filter）**

| 算子 | 说明 |
|---|---|
| `KGEntityBasedSubgraphSampling` | BFS/跳数/随机游走子图采样（行扩展算子） |
| `KGRelationTuplePathGenerator` | k 跳路径枚举（行扩展算子，泛化支持 triple/tuple 列） |
| `MMKGEntityBasedSubgraphSampling` | 多模态子图采样，同步传播 `vis_url`/`vis_triple` |

**精炼类（Refine）**

| 算子 | 说明 |
|---|---|
| `KGTupleNormalization` | 基于 LLM 的同义词归一化与方向规范化 |

### 目录结构

每个算子目录包含：

- `SKILL.md` — 英文 API 参考（构造函数、`run()` 签名、执行逻辑、必须遵守的规则）
- `SKILL_zh.md` — 中文版
- `examples/good.md` — 最小可运行 Pipeline 示例

### 字段命名约定

| 字段 | 类型 | 生产算子 |
|---|---|---|
| `raw_chunk` | `str` | 输入 |
| `entity` | 逗号分隔 `str` | `KGEntityExtraction` |
| `triple` | `List[str]`（`"<subj> X <obj> Y <rel> Z"` 格式） | `KGTripleExtraction` |
| `tuple` | `List[Dict\|str]`（时序或超关系） | `TKGTupleExtraction` / `HRKGTripleExtraction` |
| `normalized_triple` | `List[str]` | `KGTupleNormalization` |
| `inferred_triple` | `List[str]` | `KGRelationTripleInference` |
| `subgraph` | `List[str]` | 采样算子 |
| `{k}_hop_paths` | `List[str]`（如 `2_hop_paths`） | `KGRelationTuplePathGenerator` |
| `QA_pairs` | `List[Dict]` | 所有 `*QAGeneration` 算子 |

---

## `dataflow-kg-dev`

DataFlow-KG 开发专家技能，加载完整架构知识，路由到六个专项工作流，覆盖 KG 开发全生命周期。

### 功能说明

在 DataFlow-KG 仓库中调用 `/dataflow-dev` 后，该技能将：

1. 加载 `context/knowledge_base.md`——KG 架构、API 参考、所有已注册算子
2. 加载 `context/dev_notes.md`——KG 开发规范、最佳实践、LLM 响应容错模板
3. 加载 `diagnostics/known_issues.md`——结构化"症状 → 根因 → 修复"诊断数据库
4. 探测本地仓库状态（当前分支、最近提交、文件变更）
5. 输出 1–3 行上下文摘要，自动路由到对应工作流

### 快速上手

```bash
cd /path/to/DataFlow-KG    # 必须是仓库根目录
claude                     # 启动 Claude Code
```

```
/dataflow-dev
我需要一个新的 filter 算子，过滤掉实体数量少于 3 的三元组行。
```

### 六个子命令工作流

| 意图关键词 | 工作流 |
|---|---|
| 新建算子 / new operator / 新建 KG 算子 | 算子创建（防重复检查 → 规格确认 → 代码生成 → 注册提醒） |
| 新建 Pipeline / new pipeline / KG pipeline | Pipeline 创建（算子选择 → 按 `storage.step()` 模式生成代码） |
| 新建 Prompt / new prompt / KG prompt | Prompt 创建（`PromptABC`/`DIYPromptABC`、注册装饰器、`@prompt_restrict` 位置） |
| 报错 / error / KeyError / AttributeError | 诊断（匹配 known_issues.md → 根因 + 修复示例代码） |
| 审查 / review / check / 规范检查 | 代码审查（算子与 Pipeline 双 Checklist，逐项检查） |
| 更新知识库 / sync / check updates / 仓库有新算子 | 知识库更新（检测新算子文件、与 knowledge_base.md 对比、给出更新步骤） |

### 算子创建硬性规范 Checklist

```
✓ 继承 OperatorABC，调用 super().__init__()
✓ 类上方有 @OPERATOR_REGISTRY.register() 装饰器
✓ run() 第一个参数为 storage: DataFlowStorage
✓ run() 输入列名以 input_ 开头，输出列名以 output_ 开头
✓ run() 返回输出 key 列表
✓ storage.read("dataframe") 和 storage.write(df) 都存在
✓ 包含 _validate_dataframe() 方法，检查输入列存在、输出列不冲突
✓ LLM 驱动算子：成员变量必须命名为 self.llm_serving
✓ LLM 响应有完整 try/except 容错，失败返回与输出类型匹配的空值
✓ @staticmethod get_desc(lang: str = "en") 支持 zh/en
✓ __init__.py TYPE_CHECKING 块已注册
```

### 诊断速查表（KG 专项）

| 报错关键词 | 对应 Issue |
|---|---|
| `Unexpected key 'xxx' in operator` | #001 — 配置参数命名（仅警告） |
| `No object named 'Xxx' found in 'operators' registry` | #002 — `__init__.py` TYPE_CHECKING 块缺少声明 |
| `Key Matching Error` / `does not match any output keys` | #003 — Pipeline key 不一致 |
| `You must call storage.step() before` | #004 — 缺少 `storage.step()` 调用 |
| `DummyStorage` + `AttributeError` | #005 — DummyStorage API 限制 |
| `ModuleNotFoundError` + `dataflow.operators.general_kg.xxx` | #006 — LazyLoader 路径错误，应从父模块 import |
| `Missing required column(s)` + `input_key_meta` | #007 — `input_key_meta` 缺失 |
| `triple` 列全为空 / `prompt_template` 属性报错 | #008 — `triple_type` 值错误 |
| `Missing required column(s): ['valid_triple']` + `merge_to_input` | #009 — `merge_to_input=True` 导致下游步骤找不到输出列 |

### CLI 命令

DataFlow-KG 使用 `dfkg` 而非 `dataflow`：

```bash
dfkg -v      # 查看版本
dfkg env     # 环境检查
dfkg init    # 初始化项目
```

### 文件结构

```
dataflow-kg-dev/
├── SKILL.md
├── context/
│   ├── knowledge_base.md       # KG 架构、API、所有算子（只读参考）
│   └── dev_notes.md            # KG 开发规范、最佳实践
├── diagnostics/
│   └── known_issues.md         # 结构化 Issue 数据库 #001–#009
├── templates/
│   ├── operator_template.py    # KG 算子骨架
│   ├── pipeline_template.py    # KG Pipeline 骨架
│   └── prompt_template.py      # KG Prompt 骨架
└── scripts/
    └── check_updates.sh        # 仓库变更感知脚本
```

---

## `prompt-template-builder`

为已有 KG 算子构建/修订 `DIYPromptABC` prompt 模板类，按算子接口契约对齐，输出两阶段可审计结果。

### 功能说明

给定**目标算子**和**业务目标**，该 Skill 将：

1. 查阅算子兼容矩阵（`references/operator-compatibility-matrix.md`），解析目标算子的 `build_prompt` 参数、`run_input_keys`、输出 schema
2. 输出 Stage 1 决策 JSON：模板选型原因、参数映射、输出契约、静态检查项
3. 输出 Stage 2 最终产物：完整 `DIYPromptABC` 子类代码、集成代码片段、静态验收结果

### 快速上手

#### 方式 A：交互式采访（默认）

```
/prompt-template-builder
```

- **Round 1**：结构层（任务类型、目标算子、输出约束强度、Prompt 风格、约束来源）
- **Round 2**：实现层（`build_prompt` 入参、输出格式细节、样例覆盖策略、验收重点）

#### 方式 B：直接指定 Spec

```
/prompt-template-builder --spec path/to/prompt_spec.json
```

Spec 示例：

```json
{
  "Target": "从新闻文本中抽取实体关系三元组",
  "OP_NAME": "KGTripleExtraction",
  "KG_Category": "GENERAL_KG",
  "Arguments": ["text", "entities"],
  "Constraints": "仅抽取文本中明确存在的关系，禁止虚构"
}
```

必填字段：`Target`、`OP_NAME`。可选：`KG_Category`、`run_input_keys`、`Constraints`、`Expected Output`、`Arguments`、`Sample Cases`。

### 输出格式

**Stage 1 决策 JSON**

```json
{
  "op_name": "KGTripleExtraction",
  "prompt_class": "MyKGTripleExtractionPrompt",
  "arguments": ["text", "entities"],
  "output_contract": "JSON: {\"triple\": [\"<subj> X <obj> Y <rel> Z\", ...]}",
  "strategy": "DIYPromptABC with build_system_prompt + build_prompt(text, entities)",
  "reason": "算子调用 build_prompt(text) 和 build_system_prompt(ontology)，入参与契约一致",
  "static_checks": [
    "operator_interface_aligned",
    "no_invented_params",
    "output_schema_explicit",
    "kg_tag_format_correct"
  ]
}
```

**Stage 2 产物（5 段）**

1. Requirement Mapping — 输入字段映射与推断项说明
2. Prompt Design Summary — 结构、边界策略、失败处理
3. Prompt Template Code — 完整 Python 类代码
4. Operator Integration Snippet + Walkthrough — 集成示例与样例走查
5. Static Acceptance Result — 逐项 Checklist 结果与剩余风险

### 支持的 KG 算子类别

| KG 类别 | 代表算子 |
|---|---|
| `GENERAL_KG` | `KGEntityExtraction`、`KGTripleExtraction`、`KGRelationTripleInference` 等 |
| `TEMPORAL_KG` | `TKGTupleExtraction`、`TKGTuplePathQAGeneration` |
| `HYPER_RELATION_KG` | `HRKGTripleExtraction`、`HRKGRelationTriplePathQAGeneration` |
| `GRAPH_RAG` | `GraphRAGGetAnswer`、`GraphRAGQueryExtraction` 等 |
| `COMMONSENSE_KG` | `CSKGTripleExtraction` |
| 领域 KG | `FinKG*`、`MedKG*`、`GeoKG*`、`LegalKG*`、`SchoKG*` |

### Prompt 类规范

```python
from dataflow.utils.registry import PROMPT_REGISTRY
from dataflow.core.prompt import DIYPromptABC

__all__ = ["MyKGPrompt"]

@PROMPT_REGISTRY.register()
class MyKGPrompt(DIYPromptABC):
    def __init__(self, lang: str = "zh"):
        self.lang = lang

    def build_system_prompt(self) -> str:
        # 角色 + KG 格式规则 + 输出 schema
        ...

    def build_prompt(self, text: str) -> str:
        # 将输入字段嵌入 user prompt
        ...
```

核心规则：
- 必须继承 `DIYPromptABC`，加 `@PROMPT_REGISTRY.register()` 装饰器
- `build_system_prompt()` 无参数（由算子调用），`build_prompt(**fields)` 参数与算子调用契约一致
- KG 三元组输出统一使用 `<subj>`/`<obj>`/`<rel>` 标签字符串格式
- `build_prompt` 中引用的所有变量必须来自显式参数，禁止引用未声明变量

---

## 上游仓库

所有 Skills 中的知识对齐自 **[OpenDCAI/DataFlow-KG](https://github.com/OpenDCAI/DataFlow-KG)**（`main` 分支）。
