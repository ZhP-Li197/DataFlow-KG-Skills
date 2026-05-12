# DataFlow-KG Operator Compatibility Matrix

对应版本：prompt-template-builder v1.1.0

## 使用说明

当用户提供 `OP_NAME` 时，查找对应行以获取：
1. `build_prompt` 的参数签名（参数名与类型）
2. `run_input_keys`：DataFrame 中传入 `run()` 的列名（与 `build_prompt` 参数位置对应）
3. `run_output_key`：`run()` 写入 DataFrame 的输出列名
4. 输出 JSON schema：prompt 必须指示 LLM 返回的精确格式

**强制规则：**
- 所有 KG 算子均调用 `build_system_prompt()`，此方法必须实现（即使 OP_NAME 不在矩阵中）。
- 若 OP_NAME 不在矩阵中，所有接口字段标注 `[INFERRED]`，并在 Round 2 追问 `run_input_keys` 和 `run_output_key`。

## 符号说明

- `build_prompt(A, B)` — A 对应 `run_input_keys[0]`，B 对应 `run_input_keys[1]`
- `→` — prompt 必须指示 LLM 返回的输出 schema
- `*` — 该算子存在多种调用形式，使用最常见形式

---

## GENERAL_KG

| OP_NAME | `build_prompt` 参数 | `run_input_keys` | `run_output_key` | 输出 Schema |
|---|---|---|---|---|
| `KGEntityExtraction` | `(text: str)` | `["raw_chunk"]` | `"entity"` | JSON 字符串数组：`["实体1", "实体2", ...]` |
| `KGTripleExtraction` | `(text: str, entity_list: str)` | `["raw_chunk", "entity"]` | `"triple"` | `{"triple": ["<subj> X <obj> Y <rel> Z", ...]}` |
| `KGRelationTripleInference` | `(existing_triples: str, source_texts: str)` | `["triple", "raw_chunk"]` | `"triple"` | `{"inferred_triple": ["<subj> X <obj> Y <rel> Z", ...]}` |
| `KGRelationTriplePathQAGeneration` | `(triples: str)` | `["triple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `KGRelationTripleSubgraphQAGeneration` | `(relation_triples: str)` | `["triple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `KGAttributeTripleQAGeneration` | `(triples: str)` | `["triple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `KGTupleTextGeneration` | `(tuples: str)` | `["triple"]` | `"text"` | 纯文本段落（无 JSON 包装） |
| `KGTripleStrengthFilter` | `(source_texts: str, extracted_triples: str)` | `["raw_chunk", "triple"]` | `"triple_strength_score"` | `{"scores": [0.0, 1.0, ...]}` |
| `KGEntityClassification` | `(entity: str)` | `["entity"]` | `"entity_type"` | `{"entity_type": "分类标签"}` |
| `KGTripleDisambiguation` | `(triple: str)` | `["triple"]` | `"triple"` | 去歧义后的 triple 字符串 |
| `KGTupleNormalization` | `(text: str)` | `["triple"]` | `"triple"` | 规范化后的 triple 字符串 |
| `KGEntityNormalization` | `(entity: str)` | `["entity"]` | `"entity"` | 规范化实体名称字符串 |
| `KGEntityDisambiguation` | `(entity: str)` | `["entity"]` | `"entity"` | 去歧义实体名称字符串 |
| `KGEntityAlignment` | `(entity: str)` | `["entity"]` | `"entity"` | 对齐后的实体标识符 |

---

## TEMPORAL_KG

| OP_NAME | `build_prompt` 参数 | `run_input_keys` | `run_output_key` | 输出 Schema |
|---|---|---|---|---|
| `TKGTupleExtraction` | `(text: str)` | `["raw_chunk"]` | `"tuple"` | 时序四元组字符串，含时间戳，例如 `"<subj> X <obj> Y <rel> Z <time> T"` |
| `TKGAttributeQAGeneration` | `(temporal_quadruples: str)` | `["tuple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `TKGTuplePathQAGeneration` | `(temporal_quadruples: str)` | `["tuple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `TKGTupleSubgraphQAGeneration` | `(temporal_quadruples: str)` | `["tuple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `TKGRelationTupleDialogueQAGeneration` | `(paths: str)` | `["tuple"]` | `"QA_pairs"` | 对话式 JSON：`{"dialogue": {"constructed_path": [...], "turns": [...]}}` |
| `TKGTupleDisambiguation` | `(triple: str)` | `["tuple"]` | `"tuple"` | 去歧义后的四元组字符串 |

---

## HYPER-RELATIONAL_KG (HRKG)

| OP_NAME | `build_prompt` 参数 | `run_input_keys` | `run_output_key` | 输出 Schema |
|---|---|---|---|---|
| `HRKGTripleExtraction` | `(text: str)` | `["raw_chunk"]` | `"tuple"` | 超关系四元组（含限定词），格式参考具体算子文档 |
| `HRKGRelationTriplePathQAGeneration` | `(triples: str)` | `["triple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `HRKGRelationTripleSubgraphQAGeneration` | `(relation_triples: str)` | `["triple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |

---

## COMMONSENSE_KG (CSKG)

| OP_NAME | `build_prompt` 参数 | `run_input_keys` | `run_output_key` | 输出 Schema |
|---|---|---|---|---|
| `CSKGTripleExtraction` | `(text: str)` | `["raw_chunk"]` | `"triple"` | `{"triple": ["<subj> X <obj> Y <rel> Z", ...]}` |
| `CSKGRelationTripleQAGeneration` | `(triples: str)` | `["triple"]` | `"QA_pairs"` | `{"QA_pairs": ["Question: ... Answer: ...", ...]}` |
| `CSKGTripleConceptGeneralization` | `(text: str)` | `["triple"]` | `"triple"` | 泛化后的 triple 字符串 |

---

## GRAPH_RAG

| OP_NAME | `build_prompt` 参数 | `run_input_keys` | `run_output_key` | 输出 Schema |
|---|---|---|---|---|
| `KGGraphRAGQueryExtraction` | `(question: str)` | `["question"]` | `["entities", "relations"]` | 多输出列：entities 列表 + relations 列表 |
| `KGGraphRAGGetAnswer` | `(subgraph_prompt: str)` | `["question", "subgraph_prompt"]` | `"answer"` | 纯文本答案（必须基于证据，禁止外部知识） |
| `KGRAGAnswerPlausibilityFilter` | `(question: str, answer: str)` | `["question", "answer"]` | `"plausibility_score"` | `{"score": float, "reason": str}` |

---

## GRAPH_REASONING

| OP_NAME | `build_prompt` 参数 | `run_input_keys` | `run_output_key` | 输出 Schema |
|---|---|---|---|---|
| `KGReasoningRelationGeneration` | `(path: str)` | `["triple"]` | `"relation"` | 推理关系字符串 |

---

## 领域 KG (Domain KG)

| OP_NAME | 类别 | `build_prompt` 参数 | `run_input_keys` | `run_output_key` | 输出 Schema |
|---|---|---|---|---|---|
| `FinKGTupleExtraction` | FinKG | `(text: str)` | `["raw_chunk"]` | `"tuple"` | 金融四元组字符串 |
| `MedKGTripleExtraction` | MedKG | `(text: str)` | `["raw_chunk"]` | `"triple"` | `{"triple": ["<subj> X <obj> Y <rel> Z", ...]}` |
| `GeoKGTupleExtraction` | GeoKG | `(text: str)` | `["raw_chunk"]` | `"tuple"` | 时空四元组字符串 |
| `LegalKGTupleExtraction` | LegalKG | `(text: str)` | `["raw_chunk"]` | `"triple"` | `{"triple": ["<subj> X <obj> Y <rel> Z", ...]}` |
| `SchoKGTripleExtraction` | SchoKG | `(text: str)` | `["raw_chunk"]` | `"triple"` | `{"triple": ["<subj> X <obj> Y <rel> Z", ...]}` |
| `LegalKGJudgementPrediction` | LegalKG | `(text: str)` | `["raw_chunk"]` | `"judgement"` | 判决预测文本 |
| `LegalKGCaseSummarySimilarity` | LegalKG | `(text: str)` | `["raw_chunk"]` | `"similarity_score"` | `{"score": float}` |
| `MedKGTripleDrugActionMechanismDiscovery` | MedKG | `(text: str)` | `["raw_chunk"]` | `"mechanism"` | 药物作用机制描述文本 |

---

## INFERRED 兜底（OP_NAME 不在矩阵中）

当 OP_NAME 未出现在上述表格时，执行以下默认策略：

1. 假设 `build_prompt` 的第一个参数对应 `run_input_keys[0]`（主要输入列）。
2. `build_system_prompt()` 仍然必须实现（所有 KG 算子均调用）。
3. 输出顶层 JSON key 使用 `run_output_key` 的值（若用户已提供）；否则追问。
4. Stage 1 中所有接口字段标注 `[INFERRED]`，在 `reason` 中说明推断依据。
5. Round 2 必须追问 `run_input_keys` 和 `run_output_key`（触发规则生效）。
