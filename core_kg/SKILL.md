---
name: core_kg
description: Reference documentation for DataFlow-KG core operators (general / temporal / multimodal / hyper-relation KG and the path & subgraph samplers shared across them). Use when generating a pipeline that needs per-operator details beyond the planner summary, or when debugging field-flow / row-expansion issues.
version: 1.0.0
---

# DataFlow-KG Core Operators Skill

This sibling skill provides per-operator API references for DataFlow-KG. It is loaded by `generating-dataflow-kg-pipeline` when the planner needs:

- exact constructor / `run()` signatures
- column naming conventions (especially row-expanding sampler outputs)
- known caveats (e.g. the `qa_type="base"` typo in subgraph QA, `vis_triple` being hard-coded in MMKG QA)

## Layout

```
core_kg/
├── SKILL.md                    ← this file (operator index)
├── generate/
│   ├── kg-entity-extraction/
│   ├── kg-triple-extraction/
│   ├── kg-relation-triple-inference/
│   ├── kg-relation-triple-subgraph-qa-generation/
│   ├── kg-relation-triple-path-qa-generation/
│   ├── tkg-tuple-extraction/
│   ├── tkg-tuple-path-qa-generation/
│   ├── mmkg-visual-triple-extraction/
│   ├── mmkg-subgraph-base-qa-generation/
│   ├── hrkg-triple-extraction/
│   └── hrkg-relation-triple-path-qa-generation/
├── filter/
│   ├── kg-entity-based-subgraph-sampling/
│   ├── kg-relation-tuple-path-generator/
│   └── mmkg-entity-based-subgraph-sampling/
└── refine/
    └── kg-tuple-normalization/
```

Each operator directory contains:

- `SKILL.md` — English reference: import, constructor, `run()`, execution logic, mandatory rules
- `SKILL_zh.md` — Chinese version
- `examples/good.md` — a minimal working pipeline snippet that uses this operator

## Field Vocabulary

These field names are conventional across KG operators and should not be renamed unless the user has a strong reason:

| Field | Type | Producer |
|---|---|---|
| `raw_chunk` | `str` | input |
| `entity` | comma-separated `str` | `KGEntityExtraction` |
| `triple` | `List[str]` (`"<subj> X <obj> Y <rel> Z"`) | `KGTripleExtraction` |
| `tuple` | `List[Dict\|str]` (time-anchored or hyper-relation) | `TKGTupleExtraction` / `HRKGTripleExtraction` |
| `normalized_triple` | `List[str]` | `KGTupleNormalization` |
| `inferred_triple` | `List[str]` | `KGRelationTripleInference` |
| `subgraph` | `List[str]` | sampling operators |
| `{k}_hop_paths` | `List[str]` (e.g. `2_hop_paths`) | `KGRelationTuplePathGenerator` |
| `img_dict` | `Dict[str, str]` (img_id → local path) | input |
| `vis_url` | `List[str]` (local paths, aligned to `vis_triple`) | input / propagated by MMKG sampler |
| `vis_triple` | `List[str]` (`"<subj> X <obj> img_id <rel> depicted_in "`) | `MMKGVisualTripleExtraction` |
| `QA_pairs` | `List[Dict]` | any `*QAGeneration` |

## Operator Index

### Generate (11)

| Operator | Subdirectory | Status | Description |
|---|---|---|---|
| `KGEntityExtraction` | `generate/kg-entity-extraction/` | ✅ | Entity surface-form extraction from text — anchor for all KG triple/quadruple extractors |
| `KGTripleExtraction` | `generate/kg-triple-extraction/` | ✅ | Relation or attribute triple extraction given text + entity list |
| `KGRelationTripleInference` | `generate/kg-relation-triple-inference/` | ✅ | LLM-based KG closure inference; optional merge-back |
| `KGRelationTripleSubgraphQAGeneration` | `generate/kg-relation-triple-subgraph-qa-generation/` | ✅ | QA over sampled subgraphs (avoid `qa_type="base"`) |
| `KGRelationTriplePathQAGeneration` | `generate/kg-relation-triple-path-qa-generation/` | ✅ | QA over 1- or 2-hop paths from `KGRelationTuplePathGenerator` |
| `TKGTupleExtraction` | `generate/tkg-tuple-extraction/` | ✅ | Time-anchored 4-tuple extraction from text |
| `TKGTuplePathQAGeneration` | `generate/tkg-tuple-path-qa-generation/` | ✅ | Time-aware path QA (4 `qa_type` variants) |
| `MMKGVisualTripleExtraction` | `generate/mmkg-visual-triple-extraction/` | ✅ | VLM-based visual triple extraction from local images + entity list |
| `MMKGSubgraphBaseQAGeneration` | `generate/mmkg-subgraph-base-qa-generation/` | ✅ | Multimodal QA grounded in subgraph + images |
| `HRKGTripleExtraction` | `generate/hrkg-triple-extraction/` | ✅ | Hyper-relation tuple extraction with qualifiers |
| `HRKGRelationTriplePathQAGeneration` | `generate/hrkg-relation-triple-path-qa-generation/` | ✅ | Hyper-relation path QA |
| `KGAttributeTripleQAGeneration` | — | TODO | Attribute-triple QA generation (not yet documented per-operator) |
| `KGRelationTupleConversationGeneration` | — | TODO | Multi-turn KG dialogue generation |
| `MMKGPathBaseQAGeneration` | — | TODO | Multimodal path-based QA |
| `TKGTupleSubgraphQAGeneration` | — | TODO | Time-anchored subgraph QA |
| `TKGAttributeQAGeneration` | — | TODO | Time-anchored attribute QA |
| `HRKGRelationTripleSubgraphQAGeneration` | — | TODO | Hyper-relation subgraph QA |
| `CSKGTripleExtraction` | — | TODO | Commonsense KG triple extraction |
| `GraphRAGGetAnswer` / `GraphRAGPromptGenerator` / `GraphRAGQueryExtraction` | — | TODO | GraphRAG operator family |
| `ReasoningConstrainedPathSearch` / `ReasoningPathSearch` / `ReasoningRelationGenerator` | — | TODO | Graph reasoning operator family |
| Domain KG generators (`FinKG*`, `LegalKG*`, `MedKG*`, `SchoKG*`, `GeoKG*`) | — | TODO | Per-domain operators |

### Filter (3)

| Operator | Subdirectory | Status | Description |
|---|---|---|---|
| `KGEntityBasedSubgraphSampling` | `filter/kg-entity-based-subgraph-sampling/` | ✅ | BFS / hop / random-walk subgraph sampling per entity (**row-expanding**) |
| `KGRelationTuplePathGenerator` | `filter/kg-relation-tuple-path-generator/` | ✅ | k-hop path enumeration from any triple-format column (**row-expanding**) |
| `MMKGEntityBasedSubgraphSampling` | `filter/mmkg-entity-based-subgraph-sampling/` | ✅ | Multimodal subgraph sampling, also propagates `vis_url` / `vis_triple` |
| All `*Filter` / `*Sampling` operators in `general_kg/filter/` outside the 3 above | — | TODO | Quality / consistency / topology filters |
| `MMKGRelationTuplePathGenerator` | — | TODO | Multimodal variant of the path generator |
| `TKGTupleTimeFilter` | — | TODO | Time-based 4-tuple filter |
| Domain-specific filters | — | TODO | Per-domain quality filters |

### Refine (1)

| Operator | Subdirectory | Status | Description |
|---|---|---|---|
| `KGTupleNormalization` | `refine/kg-tuple-normalization/` | ✅ | LLM-based synonym normalization + direction canonicalization for triples |
| `KGEntityAlignment` / `KGEntityClassification` / `KGEntityDisambiguation` / `KGEntityNormalization` / `KGTripleDisambiguation` | — | TODO | Other refinement operators |
| `TKGTupleDisambiguation` | — | TODO | Temporal tuple disambiguation |
| `MMKGImgDictLink2WikiSimple` / `MMKGEntityLink2ImgUrl` | — | TODO | Multimodal entity refinement |

### Eval (0)

All evaluation operators (`KGQA*Evaluator`, `KGRelationTriple*Evaluator`, `KGSubgraph*Evaluator`, `HRKGTriple*Evaluator`, `GraphRAG*Eval`, etc.) are listed in the source repository but not yet documented at the per-operator level here. When the planner needs an eval operator, it should refer the user to the source path directly (`dataflow/operators/<family>/eval/`) until per-operator docs are added.

## How the Planner Uses This Skill

1. The planner (`../generating-dataflow-kg-pipeline/SKILL.md`) decides KG type and operator chain
2. For any operator with a ✅ row above, the planner reads the matching subdirectory's `SKILL.md` (or `SKILL_zh.md` if the user wrote Chinese) for verified signatures
3. The `examples/good.md` files show the minimal valid integration pattern for each operator
4. For TODO operators, the planner falls back to the operator's `get_desc()` docstring in the source code and writes a best-effort signature, flagging it as "not yet validated"
