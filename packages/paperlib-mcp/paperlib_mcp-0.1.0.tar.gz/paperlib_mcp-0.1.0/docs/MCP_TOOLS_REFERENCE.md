# MCP 工具参考手册

本文档提供 Paperlib MCP 所有工具的完整 API 参考。

## 工具目录

| 类别 | 工具数 | 说明 |
|------|--------|------|
| [健康检查](#1-健康检查) | 2 | 系统状态检查 |
| [PDF 导入](#2-pdf-导入) | 2 | 文档导入与状态 |
| [搜索检索](#3-搜索检索) | 4 | 混合/向量/全文搜索 |
| [数据获取](#4-数据获取) | 7 | 文档和 chunk CRUD |
| [综述写作](#5-综述写作) | 5 | 证据包与综述生成 |
| [图谱抽取](#6-图谱抽取) | 4 | 知识图谱抽取 |
| [实体规范化](#7-实体规范化) | 3 | 实体合并与锁定 |
| [社区构建](#8-社区构建) | 2 | Leiden 聚类 |
| [摘要导出](#9-摘要导出) | 3 | 社区摘要与矩阵 |
| [图谱维护](#10-图谱维护) | 3 | 状态与清理 |
| [关系规范化](#11-关系规范化) | 2 | 关系合并 |
| [Claim 分组](#12-claim-分组) | 2 | Claim 聚类 |
| [v1.2 增强](#13-v12-增强工具) | 5 | 词表与特征分配 |
| [Review 工具](#14-review-工具) | 5 | 大纲与章节 |

---

## 1. 健康检查

### `health_check`

验证数据库和存储连接状态。

**参数**: 无

**返回**:
```json
{
  "ok": true,
  "db": {
    "connected": true,
    "extensions": ["vector"],
    "vector_enabled": true
  },
  "s3": {
    "accessible": true,
    "bucket": "papers",
    "endpoint": "http://localhost:9000"
  }
}
```

### `graph_health_check`

检查 GraphRAG 层健康状态。

**参数**:
| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `include_counts` | bool | `true` | 是否包含行数统计 |

**返回**:
```json
{
  "ok": true,
  "db_ok": true,
  "tables_ok": true,
  "indexes_ok": true,
  "counts": {
    "entities": 1234,
    "mentions": 5678,
    "relations": 890,
    "claims": 456,
    "communities": 12
  }
}
```

---

## 2. PDF 导入

### `import_pdf`

导入 PDF 文献到知识库。

**参数**:
| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file_path` | str | ✅ | - | PDF 文件路径 |
| `title` | str | ❌ | - | 论文标题 |
| `authors` | str | ❌ | - | 作者 |
| `year` | int | ❌ | - | 年份 |
| `force` | bool | ❌ | `false` | 强制重新导入 |

**返回**:
```json
{
  "success": true,
  "doc_id": "abc123...",
  "job_id": 42,
  "pdf_key": "papers/abc123.pdf",
  "n_pages": 25,
  "n_chunks": 25,
  "embedded_chunks": 25,
  "empty_pages": 0,
  "skipped": false,
  "message": "Successfully imported"
}
```

### `ingest_status`

查看导入状态。

**参数**:
| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | str | ❌ | 文档 ID |
| `job_id` | int | ❌ | 作业 ID |

---

## 3. 搜索检索

### `search_hybrid`

混合搜索（推荐）。

**参数**:
| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | str | - | 搜索查询 |
| `k` | int | `10` | 返回数量 |
| `alpha` | float | `0.6` | 向量权重 (0-1) |
| `per_doc_limit` | int | `3` | 每文档最大 chunk 数 |
| `fts_topn` | int | `50` | FTS 候选数 |
| `vec_topn` | int | `50` | 向量候选数 |

**返回**:
```json
{
  "query": "monetary policy",
  "k": 10,
  "alpha": 0.6,
  "results": [
    {
      "chunk_id": 123,
      "doc_id": "abc123",
      "page_start": 5,
      "page_end": 5,
      "snippet": "The monetary policy transmission...",
      "score_total": 0.85,
      "score_vec": 0.9,
      "score_fts": 0.75
    }
  ],
  "fts_candidates": 50,
  "vec_candidates": 50
}
```

### `search_vector_only`

纯向量搜索。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `query` | str | - |
| `k` | int | `10` |

### `search_fts_only`

纯全文搜索。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `query` | str | - |
| `k` | int | `10` |

### `explain_search`

详细搜索解释（调试用）。

**返回额外字段**:
- `fts_only_hits`: 仅 FTS 命中
- `vec_only_hits`: 仅向量命中
- `intersection_hits`: 两者都命中
- `stats`: 统计信息

---

## 4. 数据获取

### `get_chunk`

获取 chunk 完整内容。

**参数**: `chunk_id: int`

**返回**:
```json
{
  "chunk_id": 123,
  "doc_id": "abc123",
  "chunk_index": 5,
  "page_start": 5,
  "page_end": 5,
  "text": "Full chunk text...",
  "token_count": 500,
  "has_embedding": true
}
```

### `get_document`

获取文档元数据。

**参数**: `doc_id: str`

**返回**:
```json
{
  "doc_id": "abc123",
  "title": "Paper Title",
  "authors": "Author Name",
  "year": 2024,
  "venue": "Journal Name",
  "chunk_count": 25,
  "embedded_chunk_count": 25,
  "total_tokens": 12500
}
```

### `get_document_chunks`

获取文档所有 chunks。

**参数**: `doc_id: str`

### `list_documents`

列出所有文档。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `limit` | int | `50` |
| `offset` | int | `0` |
| `order_by` | str | `"created_at"` |
| `has_embeddings` | bool | `None` |

### `update_document`

更新文档元数据。

**参数**:
| 名称 | 类型 | 必填 |
|------|------|------|
| `doc_id` | str | ✅ |
| `title` | str | ❌ |
| `authors` | str | ❌ |
| `year` | int | ❌ |
| `venue` | str | ❌ |
| `doi` | str | ❌ |
| `url` | str | ❌ |

### `delete_document`

删除文档。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `doc_id` | str | - |
| `also_delete_object` | bool | `false` |

### `reembed_document`

重新生成 embeddings。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `doc_id` | str | - |
| `batch_size` | int | `64` |
| `force` | bool | `false` |

### `rechunk_document`

重新分块文档。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `doc_id` | str | - |
| `strategy` | str | `"page_v1"` |
| `force` | bool | `false` |

---

## 5. 综述写作

### `build_evidence_pack`

构建证据包。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `query` | str | - |
| `k` | int | `40` |
| `per_doc_limit` | int | `3` |
| `alpha` | float | `0.6` |

**返回**:
```json
{
  "pack_id": 1,
  "query": "monetary policy effects",
  "items": [...],
  "stats": {
    "total_chunks": 40,
    "unique_docs": 15
  }
}
```

### `get_evidence_pack_info`

获取证据包详情。

**参数**: `pack_id: int`

### `list_evidence_packs`

列出所有证据包。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `limit` | int | `20` |
| `offset` | int | `0` |

### `draft_lit_review_v1`

生成文献综述草稿。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `topic` | str | - |
| `pack_id` | int | `None` |
| `k` | int | `30` |
| `outline_style` | str | `"econ_finance_canonical"` |

**返回**:
```json
{
  "topic": "Central bank digital currency",
  "outline_style": "econ_finance_canonical",
  "pack_id": 5,
  "total_sources": 25,
  "sections": [
    {
      "section_id": "research_question",
      "title": "研究问题与理论框架",
      "content": "...",
      "citations": [...]
    }
  ],
  "all_citations": [...]
}
```

### `draft_section`

生成特定章节。

**参数**:
| 名称 | 类型 |
|------|------|
| `pack_id` | int |
| `section` | str |
| `outline_style` | str |

### `get_outline_templates`

获取可用模板。

**返回**:
```json
{
  "templates": [
    {
      "name": "econ_finance_canonical",
      "display_name": "经济金融学经典结构",
      "sections": [
        {"id": "research_question", "title": "研究问题与理论框架"},
        {"id": "measurement", "title": "度量与代理变量"},
        {"id": "identification", "title": "识别策略"},
        {"id": "findings", "title": "主要发现"},
        {"id": "debates", "title": "争议与不一致发现"},
        {"id": "gaps", "title": "研究空白与未来方向"}
      ]
    }
  ]
}
```

---

## 6. 图谱抽取

### `extract_graph_v1`

抽取结构化图谱要素。

**参数**:
| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `doc_id` | str | `None` | 文档 ID |
| `chunk_ids` | list[int] | `None` | 指定 chunk 列表 |
| `mode` | str | `"high_value_only"` | 筛选模式 |
| `max_chunks` | int | `60` | 最大 chunk 数 |
| `llm_model` | str | `None` | LLM 模型 |
| `min_confidence` | float | `0.8` | 最小置信度 |
| `dry_run` | bool | `false` | 仅预览 |
| `concurrency` | int | `60` | 并发数 |

**返回**:
```json
{
  "doc_id": "abc123",
  "stats": {
    "processed_chunks": 25,
    "new_entities": 45,
    "new_mentions": 120,
    "new_relations": 35,
    "new_claims": 18,
    "skipped_low_confidence": 5
  }
}
```

### `select_high_value_chunks`

筛选高价值 chunks。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `doc_id` | str | `None` |
| `pack_id` | int | `None` |
| `max_chunks` | int | `60` |
| `keyword_mode` | str | `"default"` |

### `extract_graph_missing`

批量抽取未处理文档。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `limit_docs` | int | `50` |
| `llm_model` | str | `None` |
| `min_confidence` | float | `0.8` |
| `concurrency` | int | `30` |
| `max_chunks` | int | `60` |

---

## 7. 实体规范化

### `canonicalize_entities_v1`

规范化并合并重复实体。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `types` | list[str] | `["Topic", "MeasureProxy", "IdentificationStrategy", "Method"]` |
| `suggest_only` | bool | `false` |
| `max_groups` | int | `5000` |

**返回**:
```json
{
  "executed": true,
  "merged_groups": 45,
  "merged_entities": 120,
  "suggestions": [...]
}
```

### `merge_entities`

手动合并两个实体。

**参数**:
| 名称 | 类型 |
|------|------|
| `from_entity_id` | int |
| `to_entity_id` | int |
| `reason` | str |

### `lock_entity`

锁定/解锁实体。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `entity_id` | int | - |
| `is_locked` | bool | `true` |

---

## 8. 社区构建

### `build_communities_v1`

构建主题社区。

**参数**:
| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `level` | str | `"macro"` | macro/micro |
| `min_df` | int | `3` | 最小文档频率 |
| `resolution` | float | `1.0` | Leiden 分辨率 |
| `max_nodes` | int | `20000` | 最大节点数 |
| `rebuild` | bool | `false` | 清除旧结果 |

**返回**:
```json
{
  "communities": [
    {
      "comm_id": 1,
      "size": 45,
      "top_entities": [
        {"entity_id": 123, "type": "Topic", "canonical_name": "Monetary Policy", "weight": 5.2}
      ]
    }
  ]
}
```

### `build_community_evidence_pack`

为社区构建证据包。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `comm_id` | int | - |
| `max_chunks` | int | `100` |
| `per_doc_limit` | int | `4` |

---

## 9. 摘要导出

### `summarize_community_v1`

生成社区结构化摘要。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `comm_id` | int | - |
| `pack_id` | int | `None` |
| `llm_model` | str | `None` |
| `max_chunks` | int | `100` |
| `style` | str | `"econ_finance"` |

### `summarize_all_communities`

批量生成社区摘要。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `level` | str | `None` |
| `concurrency` | int | `5` |
| `comm_ids` | list[int] | `None` |
| `force` | bool | `false` |

### `export_evidence_matrix_v1`

导出证据矩阵。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `comm_id` | int | `None` |
| `topic` | str | `None` |
| `format` | str | `"json"` |
| `limit_docs` | int | `None` |

---

## 10. 图谱维护

### `graph_status`

查看图谱覆盖状态。

**参数**: `doc_id: str | None`

### `clear_graph`

清理图谱数据。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `doc_id` | str | `None` |
| `clear_all` | bool | `false` |

### `rebuild_communities`

重建社区。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `level` | str | `"macro"` |
| `min_df` | int | `3` |
| `resolution` | float | `1.0` |

---

## 11. 关系规范化

### `canonicalize_relations_v1`

规范化合并关系。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `scope` | str | `"all"` |
| `predicate_whitelist` | list[str] | `None` |
| `qualifier_keys_keep` | list[str] | `["id_family", ...]` |
| `dry_run` | bool | `false` |

### `export_relations_compact_v1`

导出紧凑关系视图。

**参数**:
| 名称 | 类型 |
|------|------|
| `comm_id` | int |
| `pack_id` | int |

---

## 12. Claim 分组

### `build_claim_groups_v1`

构建 claim 分组。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `scope` | str | `"all"` |
| `max_claims_per_doc` | int | `100` |
| `dry_run` | bool | `false` |

### `export_claim_matrix_grouped_v1`

导出分组 claim 矩阵。

**参数**:
| 名称 | 类型 |
|------|------|
| `comm_id` | int |
| `pack_id` | int |

---

## 13. v1.2 增强工具

### `taxonomy_list_terms`

列出词表规则。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `kind` | str | `None` |
| `enabled_only` | bool | `true` |

### `taxonomy_upsert_term`

添加/更新词表规则。

**参数**:
| 名称 | 类型 | 必填 |
|------|------|------|
| `kind` | str | ✅ |
| `family` | str | ✅ |
| `pattern` | str | ✅ |
| `priority` | int | ❌ |
| `enabled` | bool | ❌ |
| `notes` | str | ❌ |

### `compute_topic_df_cache`

计算 Topic 文档频率缓存。

### `assign_claim_features_v1_2`

分配 claim 特征。

**参数**: `scope: str = "all"`

### `build_claim_groups_v1_2`

构建 v1.2 claim 分组。

**参数**: `scope: str = "all"`

### `split_large_claim_groups_v1_2`

拆分大型分组。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `split_threshold` | int | `150` |
| `target_size` | int | `120` |

### `export_claim_matrix_grouped_v1_2`

导出 v1.2 分组矩阵。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `comm_id` | int | `None` |
| `pack_id` | int | `None` |
| `top_k_per_group` | int | `10` |
| `include_subgroups` | bool | `true` |

---

## 14. Review 工具

### `generate_review_outline_data_v1`

生成综述大纲。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `topic` | str | `None` |
| `comm_ids` | list[int] | `None` |
| `outline_style` | str | `"econ_finance_canonical"` |
| `rebuild` | bool | `false` |

### `build_section_evidence_pack_v1`

构建章节证据包。

**参数**:
| 名称 | 类型 | 默认值 |
|------|------|--------|
| `outline_id` | str | - |
| `section_id` | str | - |
| `max_chunks` | int | `60` |
| `per_doc_limit` | int | `4` |
| `rebuild` | bool | `false` |

### `export_section_packet_v1`

导出章节写作输入包。

**参数**: `pack_id: int`

### `lint_section_v1`

验证章节引用合规。

**参数**:
| 名称 | 类型 |
|------|------|
| `pack_id` | int |
| `markdown` | str |
| `require_citations_per_paragraph` | bool |
| `min_citations_per_paragraph` | int |

### `lint_review_v1`

验证全文合规。

**参数**:
| 名称 | 类型 |
|------|------|
| `pack_ids` | list[int] |
| `markdown` | str |

### `compose_full_template_v1`

生成全文结构模板。

**参数**: `outline_id: str`

---

## 使用示例

### 完整导入和检索流程

```python
# 1. 健康检查
health_check()

# 2. 导入 PDF
import_pdf(
    file_path="/path/to/paper.pdf",
    title="Paper Title",
    authors="Author Name",
    year=2024
)

# 3. 搜索
search_hybrid(
    query="monetary policy transmission",
    k=10,
    alpha=0.6
)
```

### 知识图谱构建

```python
# 1. 抽取图谱
extract_graph_missing(limit_docs=50)

# 2. 规范化实体
canonicalize_entities_v1()

# 3. 构建社区
build_communities_v1(level="macro")

# 4. 生成摘要
summarize_all_communities(level="macro")
```

### 文献综述生成

```python
# 1. 构建证据包
result = build_evidence_pack(
    query="central bank digital currency",
    k=40
)
pack_id = result["pack_id"]

# 2. 生成综述
draft_lit_review_v1(
    pack_id=pack_id,
    outline_style="econ_finance_canonical"
)
```
