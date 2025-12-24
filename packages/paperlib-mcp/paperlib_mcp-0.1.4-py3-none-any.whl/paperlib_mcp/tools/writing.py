"""文献综述生成工具"""

import json
from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from fastmcp import FastMCP

from paperlib_mcp.tools.search import hybrid_search
from paperlib_mcp.db import query_one, query_all, get_db


# 经济金融领域文献综述的标准结构
OUTLINE_TEMPLATES = {
    "econ_finance_canonical": {
        "name": "经济金融学经典结构",
        "sections": [
            {
                "id": "research_question",
                "title": "研究问题与理论框架",
                "description": "核心研究问题、理论基础和主要假设",
                "keywords": ["theory", "hypothesis", "framework", "model", "prediction"],
            },
            {
                "id": "methodology",
                "title": "方法与识别策略",
                "description": "实证方法、因果识别、计量模型",
                "keywords": ["method", "identification", "strategy", "estimation", "regression", "instrumental", "difference-in-differences", "RDD"],
            },
            {
                "id": "data",
                "title": "数据与变量度量",
                "description": "数据来源、样本选择、关键变量定义",
                "keywords": ["data", "sample", "variable", "measure", "proxy", "definition"],
            },
            {
                "id": "findings",
                "title": "主要发现",
                "description": "核心结论、稳健性检验、异质性分析",
                "keywords": ["result", "finding", "evidence", "show", "demonstrate", "coefficient", "significant"],
            },
            {
                "id": "debates",
                "title": "争议与不一致发现",
                "description": "文献中的分歧、methodological debates",
                "keywords": ["debate", "controversy", "inconsistent", "contrast", "however", "limitation"],
            },
            {
                "id": "gaps",
                "title": "研究空白与未来方向",
                "description": "尚未解决的问题、潜在研究机会",
                "keywords": ["gap", "future", "direction", "unexplored", "opportunity", "need"],
            },
        ],
    },
    "general": {
        "name": "通用文献综述结构",
        "sections": [
            {
                "id": "background",
                "title": "背景与动机",
                "description": "研究领域概述和重要性",
                "keywords": ["background", "motivation", "importance", "context"],
            },
            {
                "id": "theory",
                "title": "理论基础",
                "description": "相关理论和概念框架",
                "keywords": ["theory", "framework", "concept", "model"],
            },
            {
                "id": "methods",
                "title": "研究方法",
                "description": "主要研究方法和技术路线",
                "keywords": ["method", "approach", "technique", "design"],
            },
            {
                "id": "findings",
                "title": "主要发现",
                "description": "关键研究结论和证据",
                "keywords": ["result", "finding", "evidence", "conclusion"],
            },
            {
                "id": "future",
                "title": "未来研究方向",
                "description": "研究空白和潜在机会",
                "keywords": ["future", "direction", "gap", "opportunity"],
            },
        ],
    },
}


class LitReviewSection(BaseModel):
    """综述章节"""
    section_id: str
    title: str
    content: str
    citations: list[dict[str, Any]]


class LitReviewDraft(BaseModel):
    """综述草稿"""
    topic: str
    outline_style: str
    pack_id: int | None
    total_sources: int
    unique_documents: int
    sections: list[LitReviewSection]
    all_citations: list[dict[str, Any]]


class EvidencePackItem(BaseModel):
    """证据包条目"""
    doc_id: str
    chunk_id: int
    page_start: int
    page_end: int
    text: str
    score: float


class EvidencePack(BaseModel):
    """证据包"""
    pack_id: int
    query: str
    params: dict[str, Any]
    items: list[EvidencePackItem]
    stats: dict[str, Any]


def get_evidence_pack(pack_id: int) -> EvidencePack | None:
    """获取证据包内容
    
    Args:
        pack_id: 证据包 ID
        
    Returns:
        证据包对象，如果不存在返回 None
    """
    # 获取证据包元数据
    pack = query_one(
        """
        SELECT pack_id, query, params_json, created_at::text
        FROM evidence_packs
        WHERE pack_id = %s
        """,
        (pack_id,)
    )
    
    if not pack:
        return None
    
    # 获取证据包条目
    items = query_all(
        """
        SELECT 
            epi.doc_id,
            epi.chunk_id,
            epi.rank,
            c.page_start,
            c.page_end,
            c.text
        FROM evidence_pack_items epi
        JOIN chunks c ON epi.chunk_id = c.chunk_id
        WHERE epi.pack_id = %s
        ORDER BY epi.rank
        """,
        (pack_id,)
    )
    
    # 统计
    unique_docs = len(set(item["doc_id"] for item in items))
    
    return EvidencePack(
        pack_id=pack["pack_id"],
        query=pack["query"],
        params=pack["params_json"] or {},
        items=[
            EvidencePackItem(
                doc_id=item["doc_id"],
                chunk_id=item["chunk_id"],
                page_start=item["page_start"],
                page_end=item["page_end"],
                text=item["text"],
                score=1.0 / (item["rank"] + 1) if item["rank"] is not None else 0.5,  # 基于排名的伪分数
            )
            for item in items
        ],
        stats={
            "total_chunks": len(items),
            "unique_docs": unique_docs,
        }
    )


def register_writing_tools(mcp: FastMCP) -> None:
    """注册写作工具"""

    @mcp.tool()
    async def build_evidence_pack(
        query: str,
        k: int = 40,
        per_doc_limit: int = 3,
        alpha: float = 0.6,
    ) -> dict[str, Any]:
        """构建证据包
        
        搜索与主题相关的文献片段，并保存为可复用的证据包。
        证据包可用于多次迭代综述写作，避免每次重新检索导致结果漂移。
        
        Args:
            query: 搜索主题/研究问题
            k: 检索数量，默认 40
            per_doc_limit: 每篇文档最多返回的 chunk 数量，默认 3
            alpha: 向量搜索权重，默认 0.6
            
        Returns:
            证据包信息，包含 pack_id 和检索到的条目
        """
        try:
            # 执行搜索
            search_result = await hybrid_search(
                query=query,
                k=k,
                alpha=alpha,
                per_doc_limit=per_doc_limit,
            )
            
            if not search_result.results:
                return {
                    "error": "No relevant literature found",
                    "query": query,
                    "pack_id": None,
                }
            
            # 保存证据包
            params = {
                "k": k,
                "per_doc_limit": per_doc_limit,
                "alpha": alpha,
            }
            
            with get_db() as conn:
                with conn.cursor() as cur:
                    # 创建证据包
                    cur.execute(
                        """
                        INSERT INTO evidence_packs (query, params_json)
                        VALUES (%s, %s)
                        RETURNING pack_id
                        """,
                        (query, json.dumps(params))
                    )
                    pack_result = cur.fetchone()
                    pack_id = pack_result["pack_id"]
                    
                    # 插入条目
                    for rank, result in enumerate(search_result.results):
                        cur.execute(
                            """
                            INSERT INTO evidence_pack_items (pack_id, doc_id, chunk_id, rank)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (pack_id, result.doc_id, result.chunk_id, rank)
                        )
            
            # 获取文档元数据
            doc_ids = list(set(r.doc_id for r in search_result.results))
            doc_metadata = {}
            for doc_id in doc_ids:
                doc = query_one(
                    "SELECT title, authors, year FROM documents WHERE doc_id = %s",
                    (doc_id,)
                )
                if doc:
                    doc_metadata[doc_id] = doc
            
            # 构建返回结果
            items = []
            for result in search_result.results:
                meta = doc_metadata.get(result.doc_id, {})
                items.append({
                    "doc_id": result.doc_id,
                    "chunk_id": result.chunk_id,
                    "page_start": result.page_start,
                    "page_end": result.page_end,
                    "text": result.snippet,
                    "score": result.score_total,
                    "title": meta.get("title"),
                    "authors": meta.get("authors"),
                    "year": meta.get("year"),
                })
            
            return {
                "pack_id": pack_id,
                "query": query,
                "params": params,
                "items": items,
                "stats": {
                    "total_chunks": len(items),
                    "unique_docs": len(doc_ids),
                },
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "pack_id": None,
            }

    @mcp.tool()
    def get_evidence_pack_info(pack_id: int) -> dict[str, Any]:
        """获取证据包详情
        
        查看已保存的证据包内容和统计信息。
        
        Args:
            pack_id: 证据包 ID
            
        Returns:
            证据包详情
        """
        try:
            pack = get_evidence_pack(pack_id)
            
            if not pack:
                return {
                    "error": f"Evidence pack not found: {pack_id}",
                    "pack_id": pack_id,
                }
            
            # 获取文档元数据
            doc_ids = list(set(item.doc_id for item in pack.items))
            doc_metadata = {}
            for doc_id in doc_ids:
                doc = query_one(
                    "SELECT title, authors, year FROM documents WHERE doc_id = %s",
                    (doc_id,)
                )
                if doc:
                    doc_metadata[doc_id] = doc
            
            items_with_meta = []
            for item in pack.items:
                meta = doc_metadata.get(item.doc_id, {})
                text = item.text
                snippet = text[:200] + "..." if len(text) > 200 else text
                items_with_meta.append({
                    "doc_id": item.doc_id,
                    "chunk_id": item.chunk_id,
                    "page_start": item.page_start,
                    "page_end": item.page_end,
                    "snippet": snippet,
                    "title": meta.get("title"),
                    "authors": meta.get("authors"),
                    "year": meta.get("year"),
                })
            
            return {
                "pack_id": pack.pack_id,
                "query": pack.query,
                "params": pack.params,
                "items": items_with_meta,
                "stats": pack.stats,
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "pack_id": pack_id,
            }

    @mcp.tool()
    def list_evidence_packs(limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """列出所有证据包
        
        查看已保存的证据包列表。
        
        Args:
            limit: 返回数量限制，默认 20
            offset: 分页偏移量，默认 0
            
        Returns:
            证据包列表
        """
        try:
            packs = query_all(
                """
                SELECT 
                    ep.pack_id,
                    ep.query,
                    ep.created_at::text,
                    COUNT(epi.id) as item_count,
                    COUNT(DISTINCT epi.doc_id) as doc_count
                FROM evidence_packs ep
                LEFT JOIN evidence_pack_items epi ON ep.pack_id = epi.pack_id
                GROUP BY ep.pack_id
                ORDER BY ep.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )
            
            total = query_one("SELECT COUNT(*) as count FROM evidence_packs")
            
            return {
                "total": total["count"] if total else 0,
                "limit": limit,
                "offset": offset,
                "packs": [
                    {
                        "pack_id": p["pack_id"],
                        "query": p["query"],
                        "created_at": p["created_at"],
                        "item_count": p["item_count"],
                        "doc_count": p["doc_count"],
                    }
                    for p in packs
                ],
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total": 0,
                "packs": [],
            }

    @mcp.tool()
    async def draft_lit_review_v1(
        topic: str | None = None,
        pack_id: int | None = None,
        k: int = 30,
        outline_style: str = "econ_finance_canonical",
    ) -> dict[str, Any]:
        """生成文献综述草稿
        
        基于指定主题或已有证据包，按照学术标准结构组织成综述草稿。
        
        Args:
            topic: 综述主题/研究问题（如果提供 pack_id 则可选）
            pack_id: 已有证据包 ID（如果提供则直接使用，不重新检索）
            k: 检索的相关 chunk 数量（仅当未提供 pack_id 时使用），默认 30
            outline_style: 大纲样式，可选 "econ_finance_canonical"（经济金融）或 "general"（通用）
            
        Returns:
            综述草稿，包含：
            - sections: 按结构组织的章节列表
            - all_citations: 所有引用的文献信息
            - total_sources: 引用的文献总数
        """
        try:
            # 确定使用的证据来源
            evidence_items = []
            used_pack_id = None
            actual_topic = topic
            
            if pack_id:
                # 使用已有证据包
                pack = get_evidence_pack(pack_id)
                if not pack:
                    return {
                        "error": f"Evidence pack not found: {pack_id}",
                        "pack_id": pack_id,
                    }
                
                used_pack_id = pack_id
                actual_topic = topic or pack.query
                
                # 转换为统一格式
                for item in pack.items:
                    evidence_items.append({
                        "doc_id": item.doc_id,
                        "chunk_id": item.chunk_id,
                        "page_start": item.page_start,
                        "page_end": item.page_end,
                        "text": item.text,
                        "score": item.score,
                    })
            else:
                if not topic:
                    return {
                        "error": "Must provide either topic or pack_id",
                    }
                
                # 执行新的搜索
                search_result = await hybrid_search(topic, k=k, alpha=0.6, per_doc_limit=3)
                
                if not search_result.results:
                    return {
                        "error": "No relevant literature found for the topic",
                        "topic": topic,
                        "sections": [],
                        "all_citations": [],
                    }
                
                for result in search_result.results:
                    # 获取完整文本
                    chunk = query_one(
                        "SELECT text FROM chunks WHERE chunk_id = %s",
                        (result.chunk_id,)
                    )
                    evidence_items.append({
                        "doc_id": result.doc_id,
                        "chunk_id": result.chunk_id,
                        "page_start": result.page_start,
                        "page_end": result.page_end,
                        "text": chunk["text"] if chunk else result.snippet,
                        "score": result.score_total,
                    })
            
            # 2. 获取大纲模板
            template = OUTLINE_TEMPLATES.get(outline_style, OUTLINE_TEMPLATES["general"])
            
            # 3. 获取文档元数据
            doc_ids = list(set(item["doc_id"] for item in evidence_items))
            doc_metadata: dict[str, dict] = {}
            for doc_id in doc_ids:
                doc = query_one(
                    "SELECT doc_id, title, authors, year FROM documents WHERE doc_id = %s",
                    (doc_id,)
                )
                if doc:
                    doc_metadata[doc_id] = {
                        "doc_id": doc["doc_id"],
                        "title": doc["title"] or "Untitled",
                        "authors": doc["authors"] or "Unknown",
                        "year": doc["year"],
                    }
            
            # 4. 将证据分配到各章节（基于关键词匹配）
            section_evidence: dict[str, list] = {s["id"]: [] for s in template["sections"]}
            
            for item in evidence_items:
                text_lower = item["text"].lower()
                best_section = None
                best_score = 0
                
                for section in template["sections"]:
                    # 计算关键词匹配分数
                    keywords = section.get("keywords", [])
                    match_count = sum(1 for kw in keywords if kw.lower() in text_lower)
                    if match_count > best_score:
                        best_score = match_count
                        best_section = section["id"]
                
                # 如果没有明确匹配，放入第一个章节
                if not best_section:
                    best_section = template["sections"][0]["id"]
                
                section_evidence[best_section].append(item)
            
            # 5. 生成各章节内容
            sections = []
            all_citations = []
            
            for section_template in template["sections"]:
                section_id = section_template["id"]
                section_items = section_evidence.get(section_id, [])
                
                # 按分数排序
                section_items.sort(key=lambda x: x["score"], reverse=True)
                
                # 构建章节内容
                content_parts = []
                section_citations = []
                
                content_parts.append(f"**{section_template['description']}**\n")
                
                for item in section_items[:10]:  # 每章节最多 10 条
                    doc_id = item["doc_id"]
                    meta = doc_metadata.get(doc_id, {"title": "Unknown", "authors": "Unknown", "year": None})
                    
                    # 添加引用信息
                    citation = {
                        "doc_id": doc_id,
                        "title": meta["title"],
                        "authors": meta["authors"],
                        "year": meta["year"],
                        "page_start": item["page_start"],
                        "page_end": item["page_end"],
                        "chunk_id": item["chunk_id"],
                    }
                    section_citations.append(citation)
                    
                    # 格式化引用标记
                    year_str = str(meta["year"]) if meta["year"] else "n.d."
                    cite_key = f"[{meta['authors']}, {year_str}: p.{item['page_start']}-{item['page_end']}]"
                    
                    # 生成摘要
                    text = item["text"]
                    snippet = text[:300] + "..." if len(text) > 300 else text
                    
                    content_parts.append(f"- {snippet} {cite_key}")
                
                if not section_items:
                    content_parts.append("（暂无相关内容）")
                
                sections.append(LitReviewSection(
                    section_id=section_id,
                    title=section_template["title"],
                    content="\n\n".join(content_parts),
                    citations=section_citations,
                ))
                
                all_citations.extend(section_citations)
            
            # 6. 去重引用列表
            unique_citations = []
            seen_docs = set()
            for cite in all_citations:
                if cite["doc_id"] not in seen_docs:
                    seen_docs.add(cite["doc_id"])
                    unique_citations.append({
                        "doc_id": cite["doc_id"],
                        "title": cite["title"],
                        "authors": cite["authors"],
                        "year": cite["year"],
                    })
            
            return LitReviewDraft(
                topic=actual_topic,
                outline_style=outline_style,
                pack_id=used_pack_id,
                total_sources=len(evidence_items),
                unique_documents=len(unique_citations),
                sections=sections,
                all_citations=unique_citations,
            ).model_dump()
            
        except Exception as e:
            return {
                "error": str(e),
                "topic": topic,
                "sections": [],
                "all_citations": [],
            }

    @mcp.tool()
    def draft_section(
        pack_id: int,
        section: str,
        outline_style: str = "econ_finance_canonical",
    ) -> dict[str, Any]:
        """生成综述特定章节
        
        基于证据包，只生成指定章节的内容。适合迭代写作某个特定部分。
        
        Args:
            pack_id: 证据包 ID
            section: 章节类型，如 "methodology"、"findings"、"gaps" 等
            outline_style: 大纲样式，默认 "econ_finance_canonical"
            
        Returns:
            章节内容和引用列表
        """
        try:
            # 获取证据包
            pack = get_evidence_pack(pack_id)
            if not pack:
                return {
                    "error": f"Evidence pack not found: {pack_id}",
                    "pack_id": pack_id,
                }
            
            # 获取模板
            template = OUTLINE_TEMPLATES.get(outline_style, OUTLINE_TEMPLATES["general"])
            
            # 找到对应章节
            section_template = None
            for s in template["sections"]:
                if s["id"] == section:
                    section_template = s
                    break
            
            if not section_template:
                available_sections = [s["id"] for s in template["sections"]]
                return {
                    "error": f"Section '{section}' not found. Available: {available_sections}",
                    "pack_id": pack_id,
                    "section": section,
                }
            
            # 获取文档元数据
            doc_ids = list(set(item.doc_id for item in pack.items))
            doc_metadata: dict[str, dict] = {}
            for doc_id in doc_ids:
                doc = query_one(
                    "SELECT doc_id, title, authors, year FROM documents WHERE doc_id = %s",
                    (doc_id,)
                )
                if doc:
                    doc_metadata[doc_id] = {
                        "doc_id": doc["doc_id"],
                        "title": doc["title"] or "Untitled",
                        "authors": doc["authors"] or "Unknown",
                        "year": doc["year"],
                    }
            
            # 筛选与章节相关的证据
            keywords = section_template.get("keywords", [])
            relevant_items = []
            
            for item in pack.items:
                text_lower = item.text.lower()
                match_count = sum(1 for kw in keywords if kw.lower() in text_lower)
                if match_count > 0:
                    relevant_items.append((item, match_count))
            
            # 按匹配数排序
            relevant_items.sort(key=lambda x: x[1], reverse=True)
            
            # 构建章节内容
            content_parts = []
            citations = []
            
            content_parts.append(f"# {section_template['title']}\n")
            content_parts.append(f"**{section_template['description']}**\n")
            
            for item, match_count in relevant_items[:15]:  # 最多 15 条
                meta = doc_metadata.get(item.doc_id, {"title": "Unknown", "authors": "Unknown", "year": None})
                
                citation = {
                    "doc_id": item.doc_id,
                    "title": meta["title"],
                    "authors": meta["authors"],
                    "year": meta["year"],
                    "page_start": item.page_start,
                    "page_end": item.page_end,
                    "chunk_id": item.chunk_id,
                    "relevance": match_count,
                }
                citations.append(citation)
                
                year_str = str(meta["year"]) if meta["year"] else "n.d."
                cite_key = f"[{meta['authors']}, {year_str}: p.{item.page_start}-{item.page_end}]"
                
                text = item.text
                snippet = text[:400] + "..." if len(text) > 400 else text
                
                content_parts.append(f"- {snippet} {cite_key}")
            
            if not relevant_items:
                content_parts.append("（该章节暂无匹配的相关内容）")
            
            # 去重引用
            unique_citations = []
            seen_docs = set()
            for cite in citations:
                if cite["doc_id"] not in seen_docs:
                    seen_docs.add(cite["doc_id"])
                    unique_citations.append(cite)
            
            return {
                "pack_id": pack_id,
                "section_id": section,
                "title": section_template["title"],
                "content": "\n\n".join(content_parts),
                "citations": citations,
                "unique_documents": len(unique_citations),
                "total_evidence": len(relevant_items),
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "pack_id": pack_id,
                "section": section,
            }

    @mcp.tool()
    def get_outline_templates() -> dict[str, Any]:
        """获取可用的综述大纲模板
        
        返回所有支持的文献综述结构模板。
        
        Returns:
            模板列表，每个包含名称和章节结构
        """
        return {
            "templates": [
                {
                    "id": key,
                    "name": template["name"],
                    "sections": [
                        {
                            "id": s["id"],
                            "title": s["title"],
                            "description": s["description"],
                        }
                        for s in template["sections"]
                    ],
                }
                for key, template in OUTLINE_TEMPLATES.items()
            ]
        }

    @mcp.tool()
    async def collect_evidence(
        topic: str,
        section_focus: str | None = None,
        k: int = 20,
    ) -> dict[str, Any]:
        """收集特定主题的文献证据
        
        搜索与主题相关的文献片段，可选择聚焦于特定章节类型。
        
        Args:
            topic: 搜索主题
            section_focus: 聚焦的章节类型（如 "methodology", "findings"）
            k: 返回结果数量
            
        Returns:
            按文献聚合的证据列表
        """
        try:
            # 如果有章节聚焦，调整查询
            query = topic
            if section_focus:
                focus_keywords = {
                    "methodology": "method approach model estimation identification",
                    "findings": "result finding evidence show demonstrate",
                    "theory": "theory framework hypothesis prediction",
                    "data": "data sample variable measure",
                }
                if section_focus in focus_keywords:
                    query = f"{topic} {focus_keywords[section_focus]}"
            
            # 搜索
            search_result = await hybrid_search(query, k=k, alpha=0.6, per_doc_limit=5)
            
            # 按文档聚合
            evidence_by_doc: dict[str, dict] = {}
            
            for result in search_result.results:
                doc_id = result.doc_id
                
                if doc_id not in evidence_by_doc:
                    # 获取文档信息
                    doc = query_one(
                        "SELECT title, authors, year FROM documents WHERE doc_id = %s",
                        (doc_id,)
                    )
                    evidence_by_doc[doc_id] = {
                        "doc_id": doc_id,
                        "title": doc["title"] if doc else "Unknown",
                        "authors": doc["authors"] if doc else "Unknown",
                        "year": doc["year"] if doc else None,
                        "evidence": [],
                    }
                
                evidence_by_doc[doc_id]["evidence"].append({
                    "chunk_id": result.chunk_id,
                    "page_start": result.page_start,
                    "page_end": result.page_end,
                    "text": result.snippet,
                    "relevance_score": result.score_total,
                })
            
            # 按证据数量排序
            sorted_evidence = sorted(
                evidence_by_doc.values(),
                key=lambda x: len(x["evidence"]),
                reverse=True
            )
            
            return {
                "topic": topic,
                "section_focus": section_focus,
                "total_chunks": len(search_result.results),
                "unique_documents": len(sorted_evidence),
                "evidence": sorted_evidence,
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "topic": topic,
                "evidence": [],
            }
