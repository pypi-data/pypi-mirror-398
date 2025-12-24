"""M3 Review Tools: 综述生成与验证工具

实现 M3 阶段的核心功能：
1. generate_review_outline_data_v1 - 生成综述大纲（确定性）
2. build_section_evidence_pack_v1 - 构建章节证据包
3. export_section_packet_v1 - 导出写作输入包
4. lint_section_v1 - 验证章节引用合规
5. compose_full_template_v1 - 生成全文模板
6. lint_review_v1 - 验证全文合规
"""

import json
import re
import uuid
from collections import defaultdict
from typing import Any

from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one


# ============================================================
# 章节模板定义（经济金融领域标准）
# ============================================================

SECTION_TEMPLATES = {
    "econ_finance_canonical": {
        "name": "经济金融学经典结构",
        "sections": [
            {
                "id": "research_question",
                "title": "研究问题与理论框架",
                "description": "核心研究问题、理论基础和主要假设",
                "ord": 1,
                "keywords": ["research question", "theory", "hypothesis", "framework", "motivation"],
                "entity_types": ["Topic"],
            },
            {
                "id": "measurement",
                "title": "测量与数据",
                "description": "变量定义、代理变量选择、数据来源",
                "ord": 2,
                "keywords": ["measure", "proxy", "variable", "data", "sample", "dataset"],
                "entity_types": ["MeasureProxy", "DataSource"],
            },
            {
                "id": "identification",
                "title": "识别策略",
                "description": "因果识别方法、内生性处理、工具变量",
                "ord": 3,
                "keywords": ["identification", "endogeneity", "instrument", "exogenous", "causal", "IV", "DID", "RDD"],
                "entity_types": ["IdentificationStrategy", "Method"],
            },
            {
                "id": "findings",
                "title": "主要发现",
                "description": "核心结论、稳健性检验、异质性分析",
                "ord": 4,
                "keywords": ["result", "finding", "evidence", "show", "demonstrate", "coefficient", "significant", "effect"],
                "entity_types": [],  # Use claims
            },
            {
                "id": "debates",
                "title": "争议与不一致发现",
                "description": "文献中的分歧、methodological debates",
                "ord": 5,
                "keywords": ["debate", "controversy", "inconsistent", "mixed", "contrast", "challenge"],
                "entity_types": [],  # Use claims with conflicting signs
            },
            {
                "id": "gaps",
                "title": "研究空白与未来方向",
                "description": "尚未解决的问题、潜在研究机会",
                "ord": 6,
                "keywords": ["gap", "future", "direction", "unexplored", "opportunity", "need", "limitation"],
                "entity_types": ["LimitationGap"],
            },
        ],
    },
    "general": {
        "name": "通用文献综述结构",
        "sections": [
            {"id": "background", "title": "背景与动机", "description": "研究领域概述", "ord": 1, "keywords": ["background", "motivation"], "entity_types": []},
            {"id": "methodology", "title": "研究方法", "description": "方法论综述", "ord": 2, "keywords": ["method", "approach"], "entity_types": ["Method"]},
            {"id": "findings", "title": "主要发现", "description": "核心结论", "ord": 3, "keywords": ["finding", "result"], "entity_types": []},
            {"id": "discussion", "title": "讨论", "description": "争议与局限", "ord": 4, "keywords": ["discussion", "limitation"], "entity_types": []},
            {"id": "future", "title": "未来方向", "description": "研究空白", "ord": 5, "keywords": ["future", "gap"], "entity_types": ["LimitationGap"]},
        ],
    },
}


def get_section_template(outline_style: str) -> dict:
    """获取章节模板"""
    return SECTION_TEMPLATES.get(outline_style, SECTION_TEMPLATES["general"])


# ============================================================
# 工具注册
# ============================================================


def register_review_tools(mcp: FastMCP) -> None:
    """注册 M3 综述工具"""

    # ----------------------------------------------------------
    # Tool 1: generate_review_outline_data_v1
    # ----------------------------------------------------------

    @mcp.tool()
    def generate_review_outline_data_v1(
        topic: str | None = None,
        comm_ids: list[int] | None = None,
        outline_style: str = "econ_finance_canonical",
        rebuild: bool = False,
    ) -> dict[str, Any]:
        """生成综述大纲（确定性，无 LLM）

        从 topic 或 comm_ids 生成可复现的综述大纲结构，写入数据库。

        Args:
            topic: 综述主题（与 comm_ids 二选一）
            comm_ids: 社区 ID 列表（与 topic 二选一）
            outline_style: 大纲样式，默认 "econ_finance_canonical"
            rebuild: 是否重建已存在的大纲，默认 False

        Returns:
            outline_id, topic, sections 列表
        """
        try:
            if not topic and not comm_ids:
                return {"error": "Must provide either topic or comm_ids"}

            # 确定 topic
            actual_topic = topic or f"community_{','.join(map(str, comm_ids))}"

            # 检查是否已存在
            if not rebuild:
                existing = query_one(
                    """
                    SELECT outline_id, topic, outline_style, sources_json, created_at::text
                    FROM review_outlines
                    WHERE topic = %s AND outline_style = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (actual_topic, outline_style),
                )
                if existing:
                    # 获取 sections
                    sections = query_all(
                        """
                        SELECT section_id, title, description, ord, sources_json, keywords
                        FROM review_outline_sections
                        WHERE outline_id = %s
                        ORDER BY ord
                        """,
                        (existing["outline_id"],),
                    )
                    return {
                        "outline_id": existing["outline_id"],
                        "topic": existing["topic"],
                        "outline_style": existing["outline_style"],
                        "sources": existing["sources_json"] or {},
                        "created_at": existing["created_at"],
                        "sections": [
                            {
                                "section_id": s["section_id"],
                                "title": s["title"],
                                "description": s["description"],
                                "ord": s["ord"],
                                "sources": s["sources_json"] or {},
                                "keywords": s["keywords"] or [],
                            }
                            for s in sections
                        ],
                        "reused": True,
                    }

            # 如果只有 topic，通过搜索找到相关 doc_ids，再映射到 comm_ids
            source_doc_ids = []
            source_comm_ids = comm_ids or []

            if topic and not comm_ids:
                # 使用同步 FTS 搜索相关文档（避免 async 警告）
                from paperlib_mcp.tools.search import search_fts

                fts_results = search_fts(topic, limit=20)
                if fts_results:
                    source_doc_ids = list(set(r["doc_id"] for r in fts_results))

                # 从 doc_ids 映射到 comm_ids
                if source_doc_ids:
                    comm_rows = query_all(
                        """
                        SELECT DISTINCT cm.comm_id
                        FROM community_members cm
                        JOIN entities e ON cm.entity_id = e.entity_id
                        JOIN mentions m ON e.entity_id = m.entity_id
                        WHERE m.doc_id = ANY(%s)
                        """,
                        (source_doc_ids,),
                    )
                    source_comm_ids = [r["comm_id"] for r in comm_rows]

            # 生成新的 outline_id
            outline_id = str(uuid.uuid4())

            # 获取模板
            template = get_section_template(outline_style)

            # 写入 outline
            sources_json = {
                "doc_ids": source_doc_ids,
                "comm_ids": source_comm_ids,
            }

            with get_db() as conn:
                with conn.cursor() as cur:
                    # 如果 rebuild，先删除旧的
                    if rebuild:
                        cur.execute(
                            "DELETE FROM review_outlines WHERE topic = %s AND outline_style = %s",
                            (actual_topic, outline_style),
                        )

                    # 插入 outline
                    cur.execute(
                        """
                        INSERT INTO review_outlines (outline_id, topic, outline_style, sources_json)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (outline_id, actual_topic, outline_style, json.dumps(sources_json)),
                    )

                    # 插入 sections
                    for section in template["sections"]:
                        section_sources = {
                            "entity_types": section.get("entity_types", []),
                        }
                        cur.execute(
                            """
                            INSERT INTO review_outline_sections
                            (outline_id, section_id, title, description, ord, sources_json, keywords)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                outline_id,
                                section["id"],
                                section["title"],
                                section["description"],
                                section["ord"],
                                json.dumps(section_sources),
                                section.get("keywords", []),
                            ),
                        )

            return {
                "outline_id": outline_id,
                "topic": actual_topic,
                "outline_style": outline_style,
                "sources": sources_json,
                "sections": [
                    {
                        "section_id": s["id"],
                        "title": s["title"],
                        "description": s["description"],
                        "ord": s["ord"],
                        "keywords": s.get("keywords", []),
                    }
                    for s in template["sections"]
                ],
                "reused": False,
            }

        except Exception as e:
            return {"error": str(e)}

    # ----------------------------------------------------------
    # Tool 2: build_section_evidence_pack_v1
    # ----------------------------------------------------------

    @mcp.tool()
    def build_section_evidence_pack_v1(
        outline_id: str,
        section_id: str,
        max_chunks: int = 60,
        per_doc_limit: int = 4,
        rebuild: bool = False,
    ) -> dict[str, Any]:
        """构建章节证据包

        为指定章节生成固定的证据包（可复现）。

        Args:
            outline_id: 大纲 ID
            section_id: 章节 ID
            max_chunks: 最大 chunk 数量，默认 60
            per_doc_limit: 每篇文档最多 chunk 数，默认 4
            rebuild: 是否重建，默认 False

        Returns:
            pack_id, chunk_count, doc_count
        """
        try:
            # 检查缓存
            if not rebuild:
                cached = query_one(
                    """
                    SELECT pack_id, params, created_at::text
                    FROM review_section_packs
                    WHERE outline_id = %s AND section_id = %s
                    """,
                    (outline_id, section_id),
                )
                if cached:
                    # 获取 pack 统计
                    stats = query_one(
                        """
                        SELECT COUNT(*) as chunk_count, COUNT(DISTINCT doc_id) as doc_count
                        FROM evidence_pack_items
                        WHERE pack_id = %s
                        """,
                        (cached["pack_id"],),
                    )
                    return {
                        "pack_id": cached["pack_id"],
                        "section_id": section_id,
                        "chunk_count": stats["chunk_count"] if stats else 0,
                        "doc_count": stats["doc_count"] if stats else 0,
                        "params": cached["params"],
                        "created_at": cached["created_at"],
                        "reused": True,
                    }

            # 获取 outline 和 section 信息
            outline = query_one(
                "SELECT topic, sources_json FROM review_outlines WHERE outline_id = %s",
                (outline_id,),
            )
            if not outline:
                return {"error": f"Outline not found: {outline_id}"}

            section = query_one(
                """
                SELECT section_id, title, sources_json, keywords
                FROM review_outline_sections
                WHERE outline_id = %s AND section_id = %s
                """,
                (outline_id, section_id),
            )
            if not section:
                return {"error": f"Section not found: {section_id}"}

            # 根据 section 类型选择 chunks
            outline_sources = outline["sources_json"] or {}
            section_sources = section["sources_json"] or {}
            entity_types = section_sources.get("entity_types", [])
            keywords = section["keywords"] or []

            # 候选 chunk_ids
            candidate_chunks = []

            # 策略 1: 从实体类型对应的 mentions 获取 chunks
            if entity_types:
                entity_chunks = query_all(
                    """
                    SELECT DISTINCT m.chunk_id, m.doc_id, c.page_start, c.page_end
                    FROM mentions m
                    JOIN entities e ON m.entity_id = e.entity_id
                    JOIN chunks c ON m.chunk_id = c.chunk_id
                    WHERE e.type = ANY(%s)
                    ORDER BY m.chunk_id
                    LIMIT %s
                    """,
                    (entity_types, max_chunks * 2),
                )
                candidate_chunks.extend(entity_chunks)

            # 策略 2: 对于 findings/debates，使用 claims
            if section_id in ("findings", "debates"):
                if section_id == "findings":
                    # 高置信度 claims - 使用子查询避免 DISTINCT + ORDER BY 冲突
                    claim_chunks = query_all(
                        """
                        SELECT chunk_id, doc_id, page_start, page_end FROM (
                            SELECT DISTINCT ON (c.chunk_id) 
                                c.chunk_id, c.doc_id, ch.page_start, ch.page_end, c.confidence
                            FROM claims c
                            JOIN chunks ch ON c.chunk_id = ch.chunk_id
                            WHERE c.confidence >= 0.7
                            ORDER BY c.chunk_id, c.confidence DESC
                        ) sub
                        ORDER BY confidence DESC
                        LIMIT %s
                        """,
                        (max_chunks * 2,),
                    )
                else:  # debates - 找冲突 sign
                    claim_chunks = query_all(
                        """
                        SELECT DISTINCT c.chunk_id, c.doc_id, ch.page_start, ch.page_end
                        FROM claims c
                        JOIN chunks ch ON c.chunk_id = ch.chunk_id
                        WHERE c.sign IN ('positive', 'negative', 'mixed')
                        ORDER BY c.chunk_id
                        LIMIT %s
                        """,
                        (max_chunks * 2,),
                    )
                candidate_chunks.extend(claim_chunks)

            # 策略 3: 使用关键词搜索
            if keywords and len(candidate_chunks) < max_chunks:
                keyword_pattern = "|".join(keywords)
                keyword_chunks = query_all(
                    """
                    SELECT chunk_id, doc_id, page_start, page_end
                    FROM chunks
                    WHERE text ~* %s
                    LIMIT %s
                    """,
                    (keyword_pattern, max_chunks * 2),
                )
                candidate_chunks.extend(keyword_chunks)

            # 去重
            seen = set()
            unique_chunks = []
            for chunk in candidate_chunks:
                if chunk["chunk_id"] not in seen:
                    seen.add(chunk["chunk_id"])
                    unique_chunks.append(chunk)

            # 应用 per_doc_limit
            doc_counts: dict[str, int] = defaultdict(int)
            filtered_chunks = []
            for chunk in unique_chunks:
                doc_id = chunk["doc_id"]
                if doc_counts[doc_id] < per_doc_limit:
                    filtered_chunks.append(chunk)
                    doc_counts[doc_id] += 1
                if len(filtered_chunks) >= max_chunks:
                    break

            # 创建 evidence pack
            params = {
                "max_chunks": max_chunks,
                "per_doc_limit": per_doc_limit,
                "section_id": section_id,
            }

            with get_db() as conn:
                with conn.cursor() as cur:
                    # 创建 pack
                    cur.execute(
                        """
                        INSERT INTO evidence_packs (query, params_json)
                        VALUES (%s, %s)
                        RETURNING pack_id
                        """,
                        (f"section:{section_id}:{outline_id}", json.dumps(params)),
                    )
                    pack_id = cur.fetchone()["pack_id"]

                    # 插入 items
                    for rank, chunk in enumerate(filtered_chunks):
                        cur.execute(
                            """
                            INSERT INTO evidence_pack_items (pack_id, doc_id, chunk_id, rank)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (pack_id, chunk["doc_id"], chunk["chunk_id"], rank),
                        )

                    # 删除旧缓存
                    cur.execute(
                        "DELETE FROM review_section_packs WHERE outline_id = %s AND section_id = %s",
                        (outline_id, section_id),
                    )

                    # 缓存新映射
                    cur.execute(
                        """
                        INSERT INTO review_section_packs (outline_id, section_id, pack_id, params)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (outline_id, section_id, pack_id, json.dumps(params)),
                    )

            return {
                "pack_id": pack_id,
                "section_id": section_id,
                "chunk_count": len(filtered_chunks),
                "doc_count": len(doc_counts),
                "params": params,
                "reused": False,
            }

        except Exception as e:
            return {"error": str(e)}

    # ----------------------------------------------------------
    # Tool 3: export_section_packet_v1
    # ----------------------------------------------------------

    @mcp.tool()
    def export_section_packet_v1(pack_id: int) -> dict[str, Any]:
        """导出章节写作输入包

        生成包含所有必要信息的 JSON，供 Agent 写作使用。

        Args:
            pack_id: 证据包 ID

        Returns:
            evidence[], paper_matrix[], claim_matrix[], doc_citations[]
        """
        try:
            # 获取 pack 信息
            pack = query_one(
                "SELECT pack_id, query, params_json FROM evidence_packs WHERE pack_id = %s",
                (pack_id,),
            )
            if not pack:
                return {"error": f"Pack not found: {pack_id}"}

            # 获取所有 chunk 内容
            chunks = query_all(
                """
                SELECT
                    epi.doc_id,
                    epi.chunk_id,
                    epi.rank,
                    c.text,
                    c.page_start,
                    c.page_end,
                    d.title,
                    d.authors,
                    d.year
                FROM evidence_pack_items epi
                JOIN chunks c ON epi.chunk_id = c.chunk_id
                JOIN documents d ON epi.doc_id = d.doc_id
                WHERE epi.pack_id = %s
                ORDER BY epi.rank
                """,
                (pack_id,),
            )

            # 构建 evidence 列表
            evidence = []
            doc_ids = set()
            chunk_ids = []

            for chunk in chunks:
                doc_ids.add(chunk["doc_id"])
                chunk_ids.append(chunk["chunk_id"])
                evidence.append({
                    "doc_id": chunk["doc_id"],
                    "chunk_id": chunk["chunk_id"],
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                    "text": chunk["text"],
                    "title": chunk["title"],
                    "authors": chunk["authors"],
                    "year": chunk["year"],
                    "citation_anchor": f"[[chunk:{chunk['chunk_id']}]]",
                })

            doc_ids_list = list(doc_ids)

            # 构建 paper_matrix
            paper_matrix = []
            for doc_id in doc_ids_list:
                doc = query_one(
                    "SELECT doc_id, title, authors, year FROM documents WHERE doc_id = %s",
                    (doc_id,),
                )
                if doc:
                    # 获取该文档关联的实体
                    entities = query_all(
                        """
                        SELECT DISTINCT e.type, e.canonical_name
                        FROM entities e
                        JOIN mentions m ON e.entity_id = m.entity_id
                        WHERE m.doc_id = %s
                        """,
                        (doc_id,),
                    )

                    entity_by_type: dict[str, list[str]] = defaultdict(list)
                    for ent in entities:
                        entity_by_type[ent["type"]].append(ent["canonical_name"])

                    paper_matrix.append({
                        "doc_id": doc_id,
                        "title": doc["title"],
                        "authors": doc["authors"],
                        "year": doc["year"],
                        "topics": entity_by_type.get("Topic", []),
                        "measures": entity_by_type.get("MeasureProxy", []),
                        "identification_strategies": entity_by_type.get("IdentificationStrategy", []),
                        "methods": entity_by_type.get("Method", []),
                        "settings": entity_by_type.get("Setting", []),
                        "limitations": entity_by_type.get("LimitationGap", []),
                    })

            # 构建 claim_matrix
            claim_matrix = []
            if chunk_ids:
                claims = query_all(
                    """
                    SELECT claim_id, doc_id, chunk_id, claim_text, sign, conditions, confidence
                    FROM claims
                    WHERE chunk_id = ANY(%s)
                    ORDER BY confidence DESC
                    """,
                    (chunk_ids,),
                )
                for claim in claims:
                    claim_matrix.append({
                        "claim_id": claim["claim_id"],
                        "doc_id": claim["doc_id"],
                        "chunk_id": claim["chunk_id"],
                        "claim_text": claim["claim_text"],
                        "sign": claim["sign"],
                        "conditions": claim["conditions"] or {},
                        "confidence": claim["confidence"],
                        "citation_anchor": f"[[chunk:{claim['chunk_id']}]]",
                    })

            # 获取引用信息
            doc_citations = []
            for doc_id in doc_ids_list:
                citation = query_one(
                    """
                    SELECT d.doc_id, d.title, d.authors, d.year,
                           c.bibtex, c.apa
                    FROM documents d
                    LEFT JOIN citations c ON d.doc_id = c.doc_id
                    WHERE d.doc_id = %s
                    """,
                    (doc_id,),
                )
                if citation:
                    doc_citations.append({
                        "doc_id": citation["doc_id"],
                        "title": citation["title"],
                        "authors": citation["authors"],
                        "year": citation["year"],
                        "bibtex": citation["bibtex"],
                        "apa": citation["apa"],
                    })

            return {
                "pack_id": pack_id,
                "query": pack["query"],
                "evidence": evidence,
                "paper_matrix": paper_matrix,
                "claim_matrix": claim_matrix,
                "doc_citations": doc_citations,
                "stats": {
                    "total_chunks": len(evidence),
                    "unique_docs": len(doc_ids_list),
                    "total_claims": len(claim_matrix),
                },
            }

        except Exception as e:
            return {"error": str(e)}

    # ----------------------------------------------------------
    # Tool 4: lint_section_v1
    # ----------------------------------------------------------

    @mcp.tool()
    def lint_section_v1(
        pack_id: int,
        markdown: str,
        require_citations_per_paragraph: bool = False,
        min_citations_per_paragraph: int = 1,
    ) -> dict[str, Any]:
        """验证章节引用合规

        检查 Agent 写作的 markdown 是否符合引用规则。

        Args:
            pack_id: 证据包 ID
            markdown: Agent 写作的 markdown 内容
            require_citations_per_paragraph: 是否要求每段有引用，默认 False
            min_citations_per_paragraph: 每段最少引用数，默认 1

        Returns:
            passed, issues[], stats
        """
        try:
            # 获取 pack 中所有 chunk_ids
            pack_chunks = query_all(
                "SELECT chunk_id FROM evidence_pack_items WHERE pack_id = %s",
                (pack_id,),
            )
            if not pack_chunks:
                return {"error": f"Pack not found or empty: {pack_id}"}

            valid_chunk_ids = {row["chunk_id"] for row in pack_chunks}

            # 解析 markdown 中的引用
            # 格式: [[chunk:<chunk_id>]]
            citation_pattern = r"\[\[chunk:(\d+)\]\]"
            citations = re.findall(citation_pattern, markdown)
            cited_chunk_ids = [int(c) for c in citations]

            issues = []
            valid_citations = 0
            invalid_citations = 0

            # 检查每个引用
            for chunk_id in cited_chunk_ids:
                # 检查是否存在
                exists = query_one(
                    "SELECT chunk_id FROM chunks WHERE chunk_id = %s",
                    (chunk_id,),
                )
                if not exists:
                    issues.append({
                        "severity": "error",
                        "rule": "CHUNK_NOT_FOUND",
                        "chunk_id": chunk_id,
                        "message": f"Chunk {chunk_id} does not exist in database",
                        "suggestion": "Remove this citation or use a valid chunk_id from the evidence pack",
                    })
                    invalid_citations += 1
                    continue

                # 检查是否在 pack 内
                if chunk_id not in valid_chunk_ids:
                    issues.append({
                        "severity": "error",
                        "rule": "CHUNK_OUT_OF_PACK",
                        "chunk_id": chunk_id,
                        "message": f"Chunk {chunk_id} is not in evidence pack {pack_id}",
                        "suggestion": "Only cite chunks from the provided evidence pack",
                    })
                    invalid_citations += 1
                    continue

                valid_citations += 1

            # 检查段落引用密度（可选）
            if require_citations_per_paragraph:
                # 按段落分割
                paragraphs = [p.strip() for p in markdown.split("\n\n") if p.strip()]
                for i, para in enumerate(paragraphs):
                    # 跳过标题行
                    if para.startswith("#"):
                        continue
                    # 统计该段落的引用
                    para_citations = re.findall(citation_pattern, para)
                    if len(para_citations) < min_citations_per_paragraph:
                        issues.append({
                            "severity": "warning",
                            "rule": "LOW_PARAGRAPH_DENSITY",
                            "paragraph_index": i,
                            "message": f"Paragraph {i+1} has {len(para_citations)} citations (minimum: {min_citations_per_paragraph})",
                            "suggestion": f"Add at least {min_citations_per_paragraph - len(para_citations)} more citation(s) to this paragraph",
                        })

            # 检查单一来源主导
            if cited_chunk_ids:
                # 获取每个 chunk 的 doc_id
                chunk_docs = {}
                for chunk_id in set(cited_chunk_ids):
                    doc = query_one(
                        "SELECT doc_id FROM chunks WHERE chunk_id = %s",
                        (chunk_id,),
                    )
                    if doc:
                        chunk_docs[chunk_id] = doc["doc_id"]

                # 统计每个文档被引用次数
                doc_cite_counts: dict[str, int] = defaultdict(int)
                for chunk_id in cited_chunk_ids:
                    doc_id = chunk_docs.get(chunk_id)
                    if doc_id:
                        doc_cite_counts[doc_id] += 1

                total = len(cited_chunk_ids)
                for doc_id, count in doc_cite_counts.items():
                    if count / total > 0.5:
                        issues.append({
                            "severity": "warning",
                            "rule": "SINGLE_SOURCE_DOMINANT",
                            "doc_id": doc_id,
                            "message": f"Document {doc_id[:16]}... accounts for {count}/{total} ({count*100//total}%) of citations",
                            "suggestion": "Consider diversifying citations across multiple sources",
                        })

            # 判断是否通过
            has_errors = any(issue["severity"] == "error" for issue in issues)

            return {
                "passed": not has_errors,
                "issues": issues,
                "stats": {
                    "total_citations": len(cited_chunk_ids),
                    "valid_citations": valid_citations,
                    "invalid_citations": invalid_citations,
                    "unique_chunks_cited": len(set(cited_chunk_ids)),
                    "pack_chunk_count": len(valid_chunk_ids),
                    "citation_coverage": valid_citations / len(valid_chunk_ids) if valid_chunk_ids else 0,
                },
            }

        except Exception as e:
            return {"error": str(e), "passed": False}

    # ----------------------------------------------------------
    # Tool 5: compose_full_template_v1
    # ----------------------------------------------------------

    @mcp.tool()
    def compose_full_template_v1(outline_id: str) -> dict[str, Any]:
        """生成全文结构模板

        返回按顺序排列的章节和 markdown 模板（带占位符）。

        Args:
            outline_id: 大纲 ID

        Returns:
            ordered_sections[], template_markdown
        """
        try:
            # 获取 outline
            outline = query_one(
                "SELECT outline_id, topic, outline_style FROM review_outlines WHERE outline_id = %s",
                (outline_id,),
            )
            if not outline:
                return {"error": f"Outline not found: {outline_id}"}

            # 获取 sections
            sections = query_all(
                """
                SELECT section_id, title, description, ord
                FROM review_outline_sections
                WHERE outline_id = %s
                ORDER BY ord
                """,
                (outline_id,),
            )

            ordered_sections = [
                {
                    "section_id": s["section_id"],
                    "title": s["title"],
                    "description": s["description"],
                    "ord": s["ord"],
                }
                for s in sections
            ]

            # 生成 markdown 模板
            template_lines = [
                f"# {outline['topic']}",
                "",
            ]

            for section in sections:
                template_lines.extend([
                    f"## {section['title']}",
                    "",
                    f"<!-- SECTION: {section['section_id']} -->",
                    f"<!-- {section['description']} -->",
                    "",
                    "[请在此处插入章节内容]",
                    "",
                ])

            template_lines.extend([
                "## 参考文献",
                "",
                "<!-- REFERENCES -->",
                "",
            ])

            return {
                "outline_id": outline_id,
                "topic": outline["topic"],
                "outline_style": outline["outline_style"],
                "ordered_sections": ordered_sections,
                "template_markdown": "\n".join(template_lines),
            }

        except Exception as e:
            return {"error": str(e)}

    # ----------------------------------------------------------
    # Tool 6: lint_review_v1
    # ----------------------------------------------------------

    @mcp.tool()
    def lint_review_v1(
        pack_ids: list[int],
        markdown: str,
    ) -> dict[str, Any]:
        """验证全文合规

        检查完整综述是否符合所有引用规则。

        Args:
            pack_ids: 允许的证据包 ID 列表（白名单）
            markdown: 完整的综述 markdown

        Returns:
            passed, issues[], stats
        """
        try:
            # 收集所有允许的 chunk_ids
            all_valid_chunk_ids: set[int] = set()
            pack_chunk_counts: dict[int, int] = {}

            for pack_id in pack_ids:
                pack_chunks = query_all(
                    "SELECT chunk_id FROM evidence_pack_items WHERE pack_id = %s",
                    (pack_id,),
                )
                chunk_ids = {row["chunk_id"] for row in pack_chunks}
                all_valid_chunk_ids.update(chunk_ids)
                pack_chunk_counts[pack_id] = len(chunk_ids)

            if not all_valid_chunk_ids:
                return {"error": "No valid chunks in provided pack_ids"}

            # 解析引用
            citation_pattern = r"\[\[chunk:(\d+)\]\]"
            citations = re.findall(citation_pattern, markdown)
            cited_chunk_ids = [int(c) for c in citations]

            issues = []
            valid_citations = 0
            invalid_citations = 0

            # 检查每个引用
            for chunk_id in cited_chunk_ids:
                # 检查是否存在
                exists = query_one(
                    "SELECT chunk_id FROM chunks WHERE chunk_id = %s",
                    (chunk_id,),
                )
                if not exists:
                    issues.append({
                        "severity": "error",
                        "rule": "CHUNK_NOT_FOUND",
                        "chunk_id": chunk_id,
                        "message": f"Chunk {chunk_id} does not exist",
                    })
                    invalid_citations += 1
                    continue

                # 检查是否在白名单内
                if chunk_id not in all_valid_chunk_ids:
                    issues.append({
                        "severity": "error",
                        "rule": "CHUNK_OUT_OF_PACK",
                        "chunk_id": chunk_id,
                        "message": f"Chunk {chunk_id} is not in whitelisted packs",
                    })
                    invalid_citations += 1
                    continue

                valid_citations += 1

            # 通过判定
            has_errors = any(issue["severity"] == "error" for issue in issues)

            return {
                "passed": not has_errors,
                "issues": issues,
                "stats": {
                    "total_citations": len(cited_chunk_ids),
                    "unique_chunks_cited": len(set(cited_chunk_ids)),
                    "valid_citations": valid_citations,
                    "invalid_citations": invalid_citations,
                    "pack_count": len(pack_ids),
                    "total_allowed_chunks": len(all_valid_chunk_ids),
                    "citation_coverage_pct": (
                        len(set(cited_chunk_ids) & all_valid_chunk_ids) / len(all_valid_chunk_ids) * 100
                        if all_valid_chunk_ids else 0
                    ),
                },
            }

        except Exception as e:
            return {"error": str(e), "passed": False}
