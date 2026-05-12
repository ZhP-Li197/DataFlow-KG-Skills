---
name: dataflow-dev
description: >
  DataFlow-KG 开发专家上下文加载器。当用户在 DataFlow-KG 仓库中进行开发时触发，
  涵盖：新建 KG 算子/Pipeline/Prompt、诊断报错、规范审查、
  以及感知仓库变更并建议更新知识库。
  Trigger: user is developing in DataFlow-KG repo, asks to create KG operator/pipeline/prompt,
  encounters errors, wants code review, or asks about KG operators.
version: 0.9.4
---

# DataFlow-KG 开发助手 (dataflow-dev)

## 激活时必须执行的步骤

1. **加载知识库**：读取 `${SKILL_DIR}/context/knowledge_base.md`（DataFlow-KG 架构 + API 参考）
2. **加载开发规范**：读取 `${SKILL_DIR}/context/dev_notes.md`（KG 开发规范 + 最佳实践）
3. **加载已知问题**：读取 `${SKILL_DIR}/diagnostics/known_issues.md`（KG 诊断快速匹配表）
4. **探测仓库状态**（在 DataFlow-KG 仓库根目录下执行）：
   ```bash
   git branch --show-current          # 当前分支
   git log --oneline -3               # 最近提交
   git diff --name-only HEAD~1 HEAD   # 最近一次变更文件列表
   ```
5. 向用户报告当前上下文摘要（1-3行，不要冗长）

---

## 子命令路由

根据用户意图，路由到对应工作流：

| 用户意图关键词 | 执行流程 |
|---|---|
| 新建算子 / new operator / create operator / 新建KG算子 | → [算子创建流程](#算子创建流程) |
| 新建 Pipeline / new pipeline / KG pipeline | → [Pipeline 创建流程](#pipeline-创建流程) |
| 新建 Prompt / new prompt / KG prompt | → [Prompt 创建流程](#prompt-创建流程) |
| 报错 / error / KeyError / AttributeError / Warning | → [诊断流程](#诊断流程) |
| 审查代码 / check / review / 规范检查 | → [规范审查流程](#规范审查流程) |
| 更新知识库 / sync / check updates / 仓库有新算子 | → [知识库更新感知流程](#知识库更新感知流程) |

---

## 算子创建流程

### Step 1: 防重复检查（必须）

在生成代码前，先检查是否已有功能相近的 KG 算子：

```bash
# 查看各 KG 模块已注册算子
grep "from \." dataflow/operators/commonsense_kg/__init__.py
grep "from \." 
dataflow/operators/temporal_kg/__init__.py
grep "from \." dataflow/operators/hyper_relation_kg/__init__.py
grep "from \." dataflow/operators/multi_model_kg/__init__.py
grep "from \." 
dataflow/operators/graph_rag/__init__.py
grep "from \." dataflow/operators/graph_reasoning/__init__.py
grep "from \." dataflow/operators/domain_kg/geospatial_kg/__init__.py
grep "from \." dataflow/operators/domain_kg/legal_kg/__init__.py
grep "from \." dataflow/operators/domain_kg/scholar_kg/__init__.py
```

对照 `context/knowledge_base.md` §八 的 KG 算子列表，确认无重复后再继续。

### Step 2: 向用户确认规格

使用 AskUserQuestion 一次性询问以下信息（合并为一轮）：
- 算子类型（filter / generate / refine / eval）
- 所属 KG 模块（general_kg / commonsense_kg / temporal_kg / multi_modal_kg / hyper_relation_kg / graph_rag / domain_kg / 其他）
- 算子功能描述（一句话，说明处理的图数据类型和操作）
- 是否依赖 LLM（是/否）
- 主输入列名（input_key）及内容类型（原始文本 / 三元组列表 / 子图 / 其他）
  - 是否有辅助输入列？如有，请逐一说明：
      - 列名（如 input_key_meta）
      - 内容类型（实体列表 / 本体元数据 / 另一张图的三元组 / 其他）
- 输出列名（output_key），可多个

### Step 3: 生成代码

使用 `templates/operator_template.py` 作为骨架，填入用户规格。

**硬性规范 checklist（每次生成必须逐项检查）**：
- [ ] 继承 `OperatorABC`，调用 `super().__init__()`
- [ ] 类上方有 `@OPERATOR_REGISTRY.register()` 装饰器
- [ ] `run()` 参数：输入列名以 `input_` 开头，输出列名以 `output_` 开头
- [ ] 需要多输入的算子：辅助输入列命名为 `input_key_meta`（或 `input_key_xxx`）
- [ ] `run()` 第一个参数为 `storage: DataFlowStorage`
- [ ] `run()` 返回输出 key 列表：`return ['output_xxx']`（多输出时返回多个）
- [ ] `run()` 调用 `storage.read("dataframe")` 和 `storage.write(df)`
- [ ] LLM 驱动算子：`self.llm_serving` 成员变量（不能用其他名称）
- [ ] 包含 `_validate_dataframe()` 方法，用于检查输入列存在、输出列不冲突
- [ ] 包含 `@staticmethod get_desc(lang: str = "en") -> tuple` 方法，返回描述算子功能的 tuple，支持 zh/en
- [ ] LLM 响应有完整容错（参考 `context/dev_notes.md` §1.8 模板 A/B/C/D）
- [ ] 配置参数放 `__init__`，列名参数放 `run()`

### Step 4: 提示注册

提醒用户在对应 KG 模块的 `__init__.py` 的 `TYPE_CHECKING` 块中添加：
```python
if TYPE_CHECKING:
    # ... 已有算子 ...
    from .filter.my_new_kg_filter import MyNewKGFilter  # 按实际路径
```

---

## Pipeline 创建流程

### Step 1: 向用户确认规格

- 本地输入文件路径及文件中已有的列名字段
- KG 处理目标（构建 / 推理 / 检索 / 领域应用）
- 需要哪些 KG 算子（按功能描述，skill 来决定使用哪些算子）
- 是否需要 LLM Serving，并发量要求
- Pipeline 风格：纯类（配置写死 `__init__`）或继承`PipelineABC`

### Step 2: 算子选择策略

优先使用已有 KG 算子，参考 `context/knowledge_base.md` §八的 KG 算子分类。

### Step 3: 生成代码

使用 `templates/pipeline_template.py` 作为骨架。

**硬性规范 checklist**：
- [ ] `storage` 在 `__init__` 中声明，而非在 `forward()` 里临时创建
- [ ] 每个算子调用传 `storage=self.storage.step()`（每次调用自动递增）
- [ ] 算子成员变量命名带 `_stepN` 后缀（N 为执行顺序）
- [ ] LLM Serving 在 `__init__` 中统一声明
- [ ] `max_workers` 根据 API 能力设置
- [ ] 包含 `if __name__ == "__main__":` 入口
- [ ] API key 通过环境变量注入，不硬编码；用户显式指定的环境变量名必须原样使用
- [ ] 上游算子的 `output_key` 必须与下游算子的 `input_key` 对应
- [ ] 继承 PipelineABC 时：`__init__`首行调用 `super().init()`

---

## Prompt 创建流程

1. 继承 `PromptABC`（标准）或 `DIYPromptABC`（绕过白名单限制）
2. 加上 `@PROMPT_REGISTRY.register()` 装饰器
3.  实现`build_prompt(self, ...) -> str`；
4. 结构化输出必须在 system prompt 中明确 JSON 格式（用 `<subj>` `<obj>` `<rel>` 标签标识每个字段），三元组统一使用标签字符串形式，JSON key 由具体prompt业务决定
5. 若算子需限制 Prompt 类型，在算子类上用 `@prompt_restrict(MyKGPrompt)`

---

## 诊断流程

1. 读取用户的报错信息
2. 在 `diagnostics/known_issues.md` 中匹配已知 Issue
3. 若命中已知 Issue，直接给出根因 + 解决方案
4. 若未命中，结合 `context/knowledge_base.md` 中的 KG 架构知识进行分析
5. 给出修复代码示例

==**快速匹配表**（无需读文件时的速查）：==

| 报错关键词 | 对应 Issue |
|---|---|
| `Unexpected key 'xxx' in operator` | Issue #001（配置参数命名，仅警告非错误）|
| `No object named 'Xxx' found in 'operators' registry` | Issue #002（__init__.py 未注册）|
| `Key Matching Error` / `does not match any output keys` | Issue #003（Pipeline key 不一致）|
| `You must call storage.step() before` | Issue #004（缺少 storage.step()）|
| `DummyStorage` + `AttributeError` / `TypeError` | Issue #005（DummyStorage 不支持完整 Storage 方法）|
| `ModuleNotFoundError` + `dataflow.operators.general_kg.xxx` | Issue #006（LazyLoader 路径，应从父模块 import） |
| `Missing required column(s)` + `input_key_meta` / `KGTripleExtraction` | Issue #007（`input_key_meta` 缺失导致 `ValueError`） |
| `triple` 列全为空 / `AttributeError: 'KGTripleExtraction' object has no attribute 'prompt_template'` | Issue #008（`triple_type` 值错误导致 Prompt 与数据格式不匹配） |
| `Missing required column(s): ['valid_triple']` + `merge_to_input` | Issue #009（`merge_to_input=True` 导致下游步骤找不到输出列） |

---

## 规范审查流程

对用户提供的代码文件，逐项检查以下规范：

### 算子审查 checklist

```
□ 继承 OperatorABC，调用 super().__init__() 
□ 注册：@OPERATOR_REGISTRY.register() 在类定义上方（不是函数上方）
□ run() 参数命名：主输入 input_key，辅助输入input_key_meta/input_key_xxx，输出 output_key，第一个参数为 storage
□ run() 返回值：list of output key names
□ storage.read() + storage.write() 都存在
□ LLM 驱动算子：self.llm_serving 命名正确
□ 容错：LLM 响应逐条 try/except，失败返回与输出类型匹配的空值
□ KG 结构化输出：JSON 解析有 try/except，格式不合规时返回与输出类型匹配的空值
□ get_desc() 返回描述算子功能的 tuple，支持 zh/en
□ 包含 _validate_dataframe() 方法，检查输入列存在、输出列不冲突
□ __init__.py TYPE_CHECKING 块已注册
□ @prompt_restrict（如有）紧贴类定义
```

### Pipeline 审查 checklist

```
□ storage 在 __init__ 中声明
□ 所有算子为成员变量（compile() 依赖此机制）
□ forward() 中每次 op.run() 传 storage.step()
□ max_workers 根据 API 限速设置
□ API key 通过环境变量注入，不硬编码；用户显式指定的环境变量名必须原样使用
□ 有 if __name__ == "__main__": 入口
□ 上游算子 output_key 与下游算子 input_key 保持一致，步骤间不随意改名
□ 继承 PipelineABC 时：__init__ 首行调用 super().__init__()
```

---

## 知识库更新感知流程

### 使用 GitHub CLI 感知变更

```bash
# 前提：需要 gh CLI 已认证（gh auth login）
# 查看最近 Issues（可能包含新 KG 算子/新功能讨论）
gh issue list --repo OpenDCAI/DataFlow-KG --limit 20 --state open

# 查看最近合并的 PR（新算子通常以 PR 形式合入）
gh pr list --repo OpenDCAI/DataFlow-KG --state merged --limit 20

# 查看某 PR 的具体文件变更
gh pr view <PR_NUMBER> --repo OpenDCAI/DataFlow-KG
```

### 本地变更检测

```bash
# 查看 operators 目录下最近新增的 KG 算子文件
git log --oneline --diff-filter=A -- 'dataflow/operators/**/*.py' | head -20

# 列出所有已注册的 KG 算子名（用于对比知识库）
python -c "
import sys; sys.path.insert(0, '.')
from dataflow.utils.registry import OPERATOR_REGISTRY
names = sorted(OPERATOR_REGISTRY.get_obj_map().keys())
for n in names: print(n)
"

# 快速扫描：找出所有已注册但未在 knowledge_base.md 中出现的算子
```

### 判断是否需要更新知识库

当以下任一情况发生时，建议更新知识库：

1. `gh pr list` 发现有新 PR 涉及 `dataflow/operators/` 路径
2. `git log` 发现有新的算子文件（扫描 `dataflow/operators/**/*.py`）
3. 用户反馈某 KG 算子不存在于知识库中但实际存在于代码中
4. 算子签名（`__init__` / `run()` 参数）发生了变更
5. 新增了 KG 图类型模块（如新增 `hyperbolic_kg/`）

### 更新知识库的步骤

1. 读取新算子文件，提取：类名、`__init__` 参数、`run()` 参数、`get_desc()` 说明
2. 在 `context/knowledge_base.md` §八 对应 KG 模块下补充算子条目
3. 在 `context/dev_notes.md` 七、版本变更记录中追加条目
4. 提交说明：`docs: sync knowledge_base with new KG operators from <PR/commit>`

---

## 重要架构提醒（每次生成代码前隐式检查）

1. **LazyLoader import 路径**：必须从父模块 import，不能直接用子包路径
   
   ```python
   # ✅ 正确
   from dataflow.operators.general_kg import TripleExtractionGenerator
   # ❌ 错误
   from dataflow.operators.general_kg.generate.triple_extraction_generator import TripleExtractionGenerator
   ```

2. **storage.step() 用法**：
   - Pipeline `forward()` 中：`op.run(storage=self.storage.step(), ...)`（每次调用传递）
   - 独立测试脚本中：先 `storage.step()`，再 `op.run(storage=storage, ...)`

3. **re.split() 捕获组**：凡在 `re.split()` pattern 中用 `(...)`，一律改为 `(?:...)`

4. **Serving 生命周期**：不要在算子内手动调用 `serving.cleanup()`，由 Pipeline 管理

5. **KG 特有：结构化输出解析**：LLM 返回的三元组/实体/关系必须经过 JSON 解析校验，格式错误时返回与输出类型匹配的空值：
   
   ```python
   # ✅ 正确：带容错的三元组解析
   # 列表输出（三元组）
   try:
       triples = json.loads(raw_output)
       assert isinstance(triples, list)
   except (json.JSONDecodeError, AssertionError):
    triples = []
   
   # 字符串输出（实体名）
   except Exception:
       entity = ""
   ```

6. **CLI 命令**：DataFlow-KG 使用 `dfkg` 而非 `dataflow`
   
   ```bash
   dfkg -v          # 查看版本
   dfkg env         # 环境检查
   dfkg init        # 初始化项目
   ```

---

## 文件索引

| 文件 | 用途 |
|---|---|
| `context/knowledge_base.md` | DataFlow-KG 架构、API、目录结构、KG 算子列表（只读参考） |
| `context/dev_notes.md` | KG 开发规范、最佳实践（可追加更新）；已知问题指针指向 known_issues.md |
| `diagnostics/known_issues.md` | 结构化 Issue 数据库，供诊断快速匹配 |
| `templates/operator_template.py` | KG 算子骨架模板 |
| `templates/pipeline_template.py` | KG Pipeline 骨架模板 |
| `templates/prompt_template.py` | KG Prompt 骨架模板 |
| `scripts/check_updates.sh` | 检测 DataFlow-KG 仓库变更、感知是否需要更新知识库的脚本 |
