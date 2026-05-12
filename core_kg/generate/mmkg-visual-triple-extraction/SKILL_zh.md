---
name: mmkg-visual-triple-extraction
description: >-
  MMKGVisualTripleExtraction 算子的参考文档。基于 VLM 抽取连接文本实体与 img_dict 图片的视觉三元组。
  适用场景：构建以本地图片为视觉证据的多模态 KG。

trigger_keywords:
  - MMKGVisualTripleExtraction
  - mmkg-visual-triple-extraction
  - 视觉三元组
  - 多模态 KG 抽取
  - VLM

version: 1.0.0
---

# MMKGVisualTripleExtraction 算子参考

基于 VLM 的抽取器：对每个 (候选实体 × 图片) 对，判断图片是否描绘了该实体，若是则输出 `depicted_in` 视觉三元组。

## 1. 导入

```python
from dataflow.operators.multi_model_kg import MMKGVisualTripleExtraction
```

## 2. 构造函数

```python
MMKGVisualTripleExtraction(
    llm_serving,                # 必需，须为 APIVLMServing_openai 实例
    quality_threshold=3,        # VLM quality_score 门限
    lang="en",
)
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `llm_serving` | 是 | None | VLM serving 后端；传 `APIVLMServing_openai` 实例 |
| `quality_threshold` | 否 | `3` | 整数 1-5；`quality_score < threshold` 的响应被丢弃 |
| `lang` | 否 | `"en"` | 提示语言 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="img_dict",
    input_key_meta="entity",
    output_key="vis_triple",
)
# 返回: [output_key]
```

| 参数 | 必需 | 默认 | 说明 |
|---|---|---|---|
| `storage` | 是 | None | 步骤存储 |
| `input_key` | 否 | `"img_dict"` | 图片字典列（`{img_id: local_path}`） |
| `input_key_meta` | 否 | `"entity"` | 候选实体列表列名 |
| `output_key` | 否 | `"vis_triple"` | 输出三元组列表列名 |

## 4. 真实执行逻辑

1. 每行读取 `img_dict`（支持字典对象或 JSON 字符串）和 `entity`（逗号分隔列表）
2. 对每张图片，用候选实体构造 VLM prompt 并调用 `generate_from_input_multi_images(...)`
3. 解析返回 JSON——预期包含 `quality_score` 与 `entity` 字段
4. 丢弃 `quality_score < quality_threshold` 的响应
5. 对匹配候选（大小写不敏感）的每个预测实体，输出 `"<subj> {entity} <obj> {img_id} <rel> depicted_in "`（末尾留一个空格）
6. 最终 `vis_triple` 列表通过 `set()` 去重

## 5. 重要规则

1. `llm_serving` 必须为 VLM（`APIVLMServing_openai`），**不能**用文本版 `APILLMServing_request`
2. `img_dict` 的 value 必须为**本地文件路径**——VLM serving 层用 `open(path, "rb")` 读字节，远程 URL 会抛 `FileNotFoundError`
3. 三元组格式硬编码为 `"<subj> entity <obj> img_id <rel> depicted_in "`（末尾空格是有意的，下游采样器会用到）
4. 图片扩展名必须为 `.jpg`、`.jpeg` 或 `.png`；`.webp` 等其他格式在 `_encode_image_to_base64` 中抛 `ValueError`
5. 行数保持不变；每行 `vis_triple` 是列表值（可能为空）

## 6. 常见用法

```python
from dataflow.serving import APIVLMServing_openai

self.vlm_serving = APIVLMServing_openai(
    api_url="https://api.openai.com/v1",
    key_name_of_api_key="DF_API_KEY",
    model_name="gpt-4o-mini",
    max_workers=4,
    temperature=0.0,
)

self.visual_triple_extractor = MMKGVisualTripleExtraction(
    llm_serving=self.vlm_serving,
    quality_threshold=3,
    lang="en",
)

self.visual_triple_extractor.run(
    storage=self.storage.step(),
    input_key="img_dict",
    input_key_meta="entity",
    output_key="vis_triple",
)
```

## 7. 返回值

```python
return [output_key]
```
