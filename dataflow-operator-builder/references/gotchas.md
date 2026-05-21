# Gotchas

## 1. `refine` vs `refinement`

`DataFlow-KG` 不同模块历史上并不统一：

- `general_kg` / `temporal_kg` 常见目录名是 `refinement`
- `multi_model_kg` / `domain_kg/*` 常见目录名是 `refine`

builder 不能把所有 refine 类算子一律写进同一个目录名。

## 2. 父模块 `__init__.py` 可能缺失

例如部分 KG 模块没有现成的 `__init__.py`。此时应创建新文件，而不是只给出提醒。

## 3. `input_key_meta` 经常遗漏

若用户需求明显依赖实体列表、路径列、本体元数据等辅助输入，应在采访阶段主动确认是否存在 `input_key_meta`。

## 4. 不要沿用通用 DataFlow 的 `cli/` 结构

本 skill 面向 `DataFlow-KG`，初版不生成 `cli/` 包，避免产物与主仓库风格脱节。

## 5. 测试目标是“结构正确”

当前阶段本地测试重点：

- Claude 能识别并加载 skill
- builder 能生成符合路径规则和注册规则的文件

不是强制要求业务逻辑已在 `dfkg` 环境跑通。
