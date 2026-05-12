---
name: generating-dataflow-kg-pipeline
description: Reasoning-guided pipeline planner that generates standard DataFlow-KG pipeline code for knowledge-graph extraction and KG-based QA generation
version: 1.0.0
---
# DataFlow-KG Pipeline Code Generator

## Goal

This skill is invoked when users provide:

- **Target**: what the KG pipeline should achieve (e.g. "extract a temporal KG from news text", "generate path-based QA from a hyper-relation KG")
- **Sample data file**: a `.json` file containing 1-5 representative records (KG pipelines use JSON arrays by default, not JSONL)

The skill must:

1. Read and analyze the sample file to infer fields, KG type signals, and modality
2. Pick the matching KG operator chain from the decision table below
3. Validate field dependencies across the chain
4. Output a Stage 1 operator decision (JSON) followed by Stage 2 complete pipeline code
5. The generated code must follow `dataflow.pipeline.PipelineABC` style (see `templates/pipeline_template.py`)

## User Input Format

```
Target: [clear KG task description]
Sample file: [path to JSON file, e.g. ./data/input.json]
Expected outputs: [optional field list, e.g. "QA_pairs"]
```

**Important**: KG sample files are JSON arrays (one top-level `[...]`), not JSONL. Default `cache_type` is `"json"`.

## KG Type Detection Rule (MANDATORY)

Inspect the sample data and select KG type by signal:

| Signal in sample | KG type | Operator family |
|---|---|---|
| Plain text only (`raw_chunk`) | **general** | `general_kg` |
| Text with explicit timestamps / dates / time spans | **temporal** | `temporal_kg` |
| Text + image dict (`img_dict`, `vis_url`) | **multimodal** | `multi_model_kg` |
| Text with multi-argument relations (attribute / qualifier per fact) | **hyper-relation** | `hyper_relation_kg` |

If the user explicitly names a KG type, that overrides signals.

## Operator Selection Decision Table (MANDATORY)

Look up the (KG type, task) pair and use the listed chain in order. Do NOT substitute operators.

| KG type | Task | Operator chain (in order) |
|---|---|---|
| general | text → KG triples | `KGEntityExtraction` → `KGTripleExtraction` → `KGTupleNormalization` |
| general | path-based QA | extraction chain → `KGRelationTuplePathGenerator` → `KGRelationTriplePathQAGeneration` |
| general | subgraph-based QA | extraction chain → `KGEntityBasedSubgraphSampling` → `KGRelationTripleSubgraphQAGeneration` |
| general | inference enrichment | extraction chain → `KGRelationTripleInference(merge_to_input=True)` |
| temporal | text → 4-tuples | `TKGTupleExtraction(triple_type="relation")` |
| temporal | path-based time QA | `TKGTupleExtraction` → `KGRelationTuplePathGenerator(input_key="tuple")` → `TKGTuplePathQAGeneration` |
| multimodal | text + image → multimodal KG + QA | `KGEntityExtraction` → `KGTripleExtraction` → `MMKGVisualTripleExtraction` → `MMKGEntityBasedSubgraphSampling` → `MMKGSubgraphBaseQAGeneration` |
| hyper-relation | text → hyper-tuples | `KGEntityExtraction` → `HRKGTripleExtraction` |
| hyper-relation | path-based QA | `KGEntityExtraction` → `HRKGTripleExtraction` → `KGRelationTuplePathGenerator(input_key="tuple")` → `HRKGRelationTriplePathQAGeneration` |
| (extension) | GraphRAG / graph reasoning / commonsense / domain (financial, legal, medical, scholar, geospatial) | consult `../core_kg/SKILL.md` for the extended operator list; this planner does not enumerate those chains |

**Key principle**: always start KG extraction with `KGEntityExtraction` — every triple/quadruple extractor expects an `entity` column to anchor the LLM extraction.

## Field Dependency Rules (MANDATORY)

DataFlow-KG fields are passed through the DataFrame across `storage.step()` boundaries. Required field invariants:

| Field | Type | Producer |
|---|---|---|
| `raw_chunk` | `str` | input |
| `entity` | comma-separated `str` | `KGEntityExtraction` |
| `triple` | `List[str]` (each `"<subj> X <obj> Y <rel> Z"`) | `KGTripleExtraction` |
| `tuple` | `List[Dict]` or `List[str]` | `TKGTupleExtraction` / `HRKGTripleExtraction` |
| `normalized_triple` | `List[str]` | `KGTupleNormalization` |
| `inferred_triple` | `List[str]` | `KGRelationTripleInference` |
| `subgraph` | `List[str]` | sampling operators |
| `{k}_hop_paths` | `List[str]` (e.g. `2_hop_paths`) | `KGRelationTuplePathGenerator` |
| `img_dict` | `Dict[str, str]` (img_id → local path) | input |
| `vis_url` | `List[str]` (local paths) | input + propagated by `MMKGEntityBasedSubgraphSampling` |
| `vis_triple` | `List[str]` (`"<subj> X <obj> img_id <rel> depicted_in "`) | `MMKGVisualTripleExtraction` |
| `QA_pairs` | `List[Dict]` (`{"question", "answer", ...}`) | any `*QAGeneration` |

Rules:

1. **Existence check**: if step N reads field X, X must exist in the sample OR be produced by an earlier step in the same pipeline
2. **No-overwrite**: every KG operator's `run()` validates that `output_key` does NOT already exist; do not reuse an output_key
3. **VLM image paths**: `img_dict` values and `vis_url` entries must be **local file paths**. `APIVLMServing_openai` opens files with `open(path, "rb")` and does not fetch remote URLs

## Path Sampling Output Column Convention (MANDATORY)

`KGRelationTuplePathGenerator` writes paths into a column named `"{k}_{output_key_meta}"` (default `"2_hop_paths"` when `k=2`). Downstream QA generators (`KGRelationTriplePathQAGeneration`, `TKGTuplePathQAGeneration`, `HRKGRelationTriplePathQAGeneration`) read this column via the matching `hop` + `input_key_meta` parameters. If `hop=1`, the QA generators read `triple` / `tuple` directly and ignore `input_key_meta`.

## Hyper-Relation / Temporal Path-QA Reuses the General Sampler (MANDATORY)

`KGRelationTuplePathGenerator` is generic over the input column name — it parses any `"<subj> ... <obj> ... <rel> ..."` triple format including 4-tuples and hyper-tuples. When wiring temporal or hyper-relation path QA, pass `input_key="tuple"` to the sampler so it reads the upstream extractor's output.

## Subgraph QA `qa_type` Caveat (MANDATORY)

`KGRelationTripleSubgraphQAGeneration` supports `qa_type` ∈ {`"num"`, `"set"`, `"base"`}. The `"base"` branch has a typo bug (`self.promt_template`) in the current codebase — pick `"num"` or `"set"` until the upstream operator is fixed.

## Image Path Convention (MANDATORY for multimodal)

When generating an MMKG pipeline, image paths in `img_dict` / `vis_url` must be resolvable from the script's working directory. The shipped example uses paths relative to `api_pipelines/` (the CWD when running `python multimodal_kg_pipeline.py`), e.g. `"../example_data/MultimodalKGPipeline/images/cyber.jpg"`. Generated code should keep paths as the user provided them — do not rewrite them.

## Output Contract (MANDATORY)

Output is two stages, in this order.

### Stage 1: Intermediate Operator Decision (JSON)

```json
{
  "kg_type": "general | temporal | multimodal | hyper-relation",
  "task": "extraction | path_qa | subgraph_qa | inference | multimodal_qa",
  "ops": ["KGEntityExtraction", "KGTripleExtraction", "..."],
  "field_flow": "raw_chunk -> entity -> triple -> ...",
  "reason": "Why this KG type and chain match the user's target and sample data."
}
```

### Stage 2: Complete Response (5 sections)

1. **Field Mapping** — sample fields → semantic role; fields each step will create
2. **Ordered Operator List** — each op's `run()` call with input_key / output_key
3. **Reasoning Summary** — why this chain, KG type evidence, any tradeoffs
4. **Complete Standard Pipeline Code** — full executable Python, follow `templates/pipeline_template.py`
5. **Adjustable Parameters / Caveats** — `lang`, `triple_type`, `hop`, `sampling_type`, `qa_type`, model selection

## Standard Code Generation Rule (MANDATORY)

All generated code must follow `templates/pipeline_template.py`:

- Class extends `dataflow.pipeline.PipelineABC`, calls `super().__init__()`
- `FileStorage` with `cache_type="json"` (KG default), `first_entry_file_name` = user-provided file path
- `APILLMServing_request` with `key_name_of_api_key="DF_API_KEY"`
- `forward()` runs each step as `op.run(storage=self.storage.step(), input_key=..., output_key=...)`
- `__main__` calls `pipeline.compile()` then `pipeline.forward()`

**DO NOT**: generate JSONL input, dynamic dispatch engines, or `forward(plan)` style runtimes.

## Operator Parameter Signature Rule (MANDATORY)

Below are the verified signatures for the 15 core KG operators in scope. Other operators (eval, refinement variants, GraphRAG, reasoning, domain KGs) live in `../core_kg/` — consult that skill for details.

### Base Components

```python
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request, APIVLMServing_openai

FileStorage(
    first_entry_file_name="...json",
    cache_path="./cache",
    file_name_prefix="kg_pipeline_step",
    cache_type="json",   # KG default; "jsonl" supported but not idiomatic
)

APILLMServing_request(
    api_url="https://api.openai.com/v1/chat/completions",
    key_name_of_api_key="DF_API_KEY",
    model_name="gpt-4o-mini",
    max_workers=4,
    temperature=0.0,
)

APIVLMServing_openai(   # for MMKG only
    api_url="https://api.openai.com/v1",
    key_name_of_api_key="DF_API_KEY",
    model_name="gpt-4o-mini",
    max_workers=4,
    temperature=0.0,
)
```

### General KG (8)

**`KGEntityExtraction`**

- Constructor: `KGEntityExtraction(llm_serving, seed=0, lang="en", prompt_template=None)`
- Run: `run(storage, input_key="raw_chunk", output_key="entity")`
- Reads `raw_chunk` (str). Writes `entity` as a comma-separated string. Drops rows whose text is <10 or >200000 chars, has <2 sentence terminators, or special-char ratio >30%.

**`KGTripleExtraction`**

- Constructor: `KGTripleExtraction(llm_serving, seed=0, triple_type="attribute", lang="en", num_q=5)`
- Run: `run(storage, input_key="raw_chunk", input_key_meta="entity", output_key="triple")`
- `triple_type`: `"relation"` (subject–relation–object) or `"attribute"` (subject–attribute–value). Both produce `triple` formatted as a list of `"<subj> X <obj> Y <rel> Z"` strings.

**`KGRelationTripleInference`**

- Constructor: `KGRelationTripleInference(llm_serving, seed=0, lang="en", with_text=False, merge_to_input=False)`
- Run: `run(storage, input_key="triple", output_key="inferred_triple")`
- If `with_text=True`, also reads `raw_chunk`. If `merge_to_input=True`, dedupes inferred triples back into the `triple` column.

**`KGTupleNormalization`**

- Constructor: `KGTupleNormalization(llm_serving, seed=0, lang="en", attribute_prompt=None, relation_prompt=None, num_q=5)`
- Run: `run(storage, input_key="triple", output_key="normalized_triple")`
- Detects triple type by inspecting `<rel>` vs `<attribute>` markers in the first triple. LLM canonicalizes synonyms and directions.

**`KGEntityBasedSubgraphSampling`**

- Constructor: `KGEntityBasedSubgraphSampling(llm_serving, seed=0, lang="en", num_q=5)` *(llm_serving is accepted but unused)*
- Run: `run(storage, input_key="triple", output_key="subgraph", sampling_type="hop", start_entity=None, M=5, hop=2, num_walks=5, walk_length=3)`
- `sampling_type` ∈ {`"bfs"`, `"hop"`, `"rw"`}. **Row-expanding**: outputs one row per starting entity, not per input row.

**`KGRelationTuplePathGenerator`**

- Constructor: `KGRelationTuplePathGenerator(seed=0, lang="en", k=2, max_paths_per_group=100)` *(no `llm_serving` argument)*
- Run: `run(storage, input_key="triple", output_key_meta="hop_paths")`
- Writes output column named `"{k}_{output_key_meta}"`, e.g. `"2_hop_paths"`. **Row-expanding**: outputs one row per enumerated path.

**`KGRelationTripleSubgraphQAGeneration`**

- Constructor: `KGRelationTripleSubgraphQAGeneration(llm_serving, seed=0, lang="en", qa_type="num", num_q=5)`
- Run: `run(storage, input_key="subgraph", output_key="QA_pairs")`
- `qa_type` ∈ {`"num"`, `"set"`}. **Avoid `"base"`** — has a typo bug in the current code.

**`KGRelationTriplePathQAGeneration`**

- Constructor: `KGRelationTriplePathQAGeneration(llm_serving, seed=0, lang="en", hop=1, num_q=5)`
- Run: `run(storage, input_key_meta="hop_paths", output_key="QA_pairs")`
- When `hop=1`, reads `triple` (ignores `input_key_meta`); when `hop=2`, reads `2_hop_paths`. Output column is always `QA_pairs`.

### Temporal KG (2)

**`TKGTupleExtraction`**

- Constructor: `TKGTupleExtraction(llm_serving, triple_type="attribute", seed=0, lang="en", num_q=5)`
- Run: `run(storage, input_key="raw_chunk", output_key="tuple")`
- `triple_type="relation"` for time-anchored relations (subject–relation–object–time); `"attribute"` for time-anchored attributes.

**`TKGTuplePathQAGeneration`**

- Constructor: `TKGTuplePathQAGeneration(llm_serving, seed=0, lang="en", hop=2, qa_type="time_point", num_q=5)`
- Run: `run(storage, input_key_meta="hop_paths", output_key_meta="QA_pairs")`
- `qa_type` ∈ {`"time_point"`, `"event_order"`, `"time_order"`, `"time_interval"`}. Output column is `"{hop}_{output_key_meta}"`, e.g. `"2_QA_pairs"`.

### Multimodal KG (3)

**`MMKGVisualTripleExtraction`**

- Constructor: `MMKGVisualTripleExtraction(llm_serving, quality_threshold=3, lang="en")` *(llm_serving must be `APIVLMServing_openai`)*
- Run: `run(storage, input_key="img_dict", input_key_meta="entity", output_key="vis_triple")`
- Reads `img_dict` (`{img_id: local_path}`) and `entity` (comma-separated). Writes `vis_triple` as `"<subj> {entity} <obj> {img_id} <rel> depicted_in "`. Drops VLM responses with `quality_score < quality_threshold`.

**`MMKGEntityBasedSubgraphSampling`**

- Constructor: `MMKGEntityBasedSubgraphSampling(llm_serving, seed=0, lang="en", num_q=5)` *(llm_serving accepted but unused)*
- Run: `run(storage, input_key="triple", output_key="subgraph", vis_triple_key="vis_triple", sampling_type="hop", start_entity=None, M=5, hop=2)`
- Reads `triple`, `vis_triple`, and `img_dict`. **Row-expanding**: emits one row per starting entity, each with `subgraph` / `vis_triple` / `vis_url` properly aligned.

**`MMKGSubgraphBaseQAGeneration`**

- Constructor: `MMKGSubgraphBaseQAGeneration(llm_serving, lang="en")` *(`APIVLMServing_openai`)*
- Run: `run(storage, input_key="vis_url", input_key_meta="subgraph", output_key="QA_pairs")`
- Internally rebuilds `img_dict` from `vis_triple` (column name hard-coded) + `vis_url` by first-appearance order. The two upstream lists must already be aligned by `MMKGEntityBasedSubgraphSampling`.

### Hyper-Relation KG (2)

**`HRKGTripleExtraction`**

- Constructor: `HRKGTripleExtraction(llm_serving, seed=0, lang="en")`
- Run: `run(storage, input_key="raw_chunk", output_key="tuple")`
- Writes hyper-tuples (subject + relation + object + qualifier/attribute map) to the `tuple` column.

**`HRKGRelationTriplePathQAGeneration`**

- Constructor: `HRKGRelationTriplePathQAGeneration(llm_serving, seed=0, lang="en", hop=1)` *(`hop` accepts only `1` or `2`)*
- Run: `run(storage, input_key_meta="hop_paths", output_key="QA_pairs")`
- When `hop=1`, reads `tuple`; when `hop=2`, reads `2_hop_paths`. Rows with `len(QA_pairs) < 2` are emptied to `[]`.

### Correct Import Paths (MANDATORY)

```python
# Base
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request, APIVLMServing_openai

# General KG
from dataflow.operators.general_kg import (
    KGEntityExtraction,
    KGTripleExtraction,
    KGRelationTripleInference,
    KGTupleNormalization,
    KGEntityBasedSubgraphSampling,
    KGRelationTuplePathGenerator,
    KGRelationTripleSubgraphQAGeneration,
    KGRelationTriplePathQAGeneration,
)

# Temporal KG
from dataflow.operators.temporal_kg import (
    TKGTupleExtraction,
    TKGTuplePathQAGeneration,
)

# Multimodal KG
from dataflow.operators.multi_model_kg import (
    MMKGVisualTripleExtraction,
    MMKGEntityBasedSubgraphSampling,
    MMKGSubgraphBaseQAGeneration,
)

# Hyper-relation KG
from dataflow.operators.hyper_relation_kg import (
    HRKGTripleExtraction,
    HRKGRelationTriplePathQAGeneration,
)
```

## Extended Operator Reference: core_kg Skill

The sibling skill **`core_kg`** (at `../core_kg/`) provides per-operator API documentation that supplements the summary signatures above.

**Each operator directory contains**:

- `SKILL.md` — Full English reference: constructor, `run()`, execution logic, mandatory rules, return value
- `SKILL_zh.md` — Chinese translation
- `examples/good.md` — A working pipeline snippet using only this operator and its immediate dependencies

**When to consult `core_kg`**:

- Generating a pipeline that uses an operator beyond the 15 listed above (e.g. KG evaluation, entity alignment, GraphRAG, graph reasoning, domain KGs, commonsense KG)
- Verifying row-expansion behavior, parameter ranges, or output column naming for any of the 15 core operators
- Debugging field-flow issues in generated code

## Examples

See `examples/`:

1. `general_kg_extraction.md` — text → entity + triple + normalize
2. `general_kg_subgraph_qa.md` — extraction → subgraph sampling → subgraph QA
3. `temporal_kg_path_qa.md` — time-stamped news → 4-tuples → path → path QA
4. `multimodal_kg.md` — text + local images → visual triples → subgraph → multimodal QA
5. `hyper_relation_kg_path_qa.md` — multi-argument facts → hyper-tuples → path → hyper path QA

These are strategy guidance, not templates to copy verbatim.
