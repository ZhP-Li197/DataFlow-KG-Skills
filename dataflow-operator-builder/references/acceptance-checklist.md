# Acceptance Checklist

提交前至少确认：

- `SKILL.md` frontmatter 存在且 `name: dataflow-operator-builder`
- 目录结构与 `DataFlow-Skills/dataflow-operator-builder` 基本一致
- 生成脚本支持 `--dry-run`
- 生成脚本支持真实写文件
- 能生成算子文件
- 能更新或创建父模块 `__init__.py`
- 能生成 `unit / registry / smoke` 三类测试
- 至少做过一轮本地 dry-run
- 至少做过一轮本地真实生成
