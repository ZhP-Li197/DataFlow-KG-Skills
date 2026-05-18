# DataFlow-KG Operator Contract

所有生成算子至少要满足以下结构：

```python
@OPERATOR_REGISTRY.register()
class XxxOperator(OperatorABC):
    @staticmethod
    def get_desc(lang: str = "en") -> tuple:
        ...

    def run(self, storage: DataFlowStorage, ...) -> list[str]:
        ...
```

## Required Behavior

- 继承 `OperatorABC`
- `__init__()` 中调用 `super().__init__()`
- `run()` 中调用 `storage.read("dataframe")`
- `run()` 中调用 `storage.write(dataframe)`
- `run()` 返回输出 key 列表，如 `return [output_key]`
- 实现 `_validate_dataframe()`，检查输入列存在且输出列不冲突
- `get_desc()` 同时支持 `zh` 和 `en`，返回 tuple

## LLM Rule

若 `uses_llm == true`：

- 成员变量必须命名为 `self.llm_serving`
- 需要对 LLM 输出做 JSON/字符串容错
- 失败时返回与输出类型兼容的空值

## Meta Input Rule

若存在辅助输入列：

- 使用 `input_key_meta` 命名
- `_validate_dataframe()` 中必须一并检查
- `run()` 中显式传递并赋给实例属性
