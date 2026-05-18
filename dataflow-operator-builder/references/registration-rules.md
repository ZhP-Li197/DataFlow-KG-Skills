# Registration Rules

## Rule 1: Class Registration

每个算子类都必须带：

```python
@OPERATOR_REGISTRY.register()
```

## Rule 2: Parent Module Registration

`DataFlow-KG` 的 LazyLoader 依赖父模块 `__init__.py` 中的 `TYPE_CHECKING` import。

例如：

```python
if TYPE_CHECKING:
    from .filter.kg_entity_count_filtering import KGEntityCountFilter
```

若父模块的 `__init__.py` 不存在，builder 应创建一个最小可用版本。

## Rule 3: Public Import Path

优先使用父模块导入：

```python
from dataflow.operators.general_kg import KGTripleExtraction
from dataflow.operators.domain_kg.medical_kg import MedKGTripleExtraction
```

避免在对外交付中要求用户直接从深层子路径 import。
