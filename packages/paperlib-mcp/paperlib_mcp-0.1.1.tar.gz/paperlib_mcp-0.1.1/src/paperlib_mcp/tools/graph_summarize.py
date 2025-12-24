"""GraphRAG 摘要与导出工具：summarize_community_v1, export_evidence_matrix_v1"""

import json
from collections import defaultdict
from typing import Any

import httpx
from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one
from paperlib_mcp.settings import get_settings
from paperlib_mcp.models_graph import (
    MCPErrorModel,
    SummarizeCommunityOut,
    ExportEvidenceMatrixOut,
)


# ============================================================
# LLM 摘要 Prompt
# ============================================================

COMMUNITY_SUMMARY_SYSTEM_PROMPT = """You are an expert academic research analyst specializing in economics and finance literature.
Your task is to synthesize evidence from multiple research papers into a structured community summary.

You MUST output valid JSON following the exact schema provided. Do not include any text outside the JSON.
Every conclusion MUST cite specific evidence with doc_id and page numbers."""

COMMUNITY_SUMMARY_USER_PROMPT_TEMPLATE = """Synthesize the following evidence from academic papers into a structured community summary.

## Community Top Entities (keywords):
{top_entities}

## Evidence from Papers:
{evidence_text}

## Required JSON Schema:
{{
  "scope": {{
    "description": "Brief description of what this research community studies",
    "key_topics": ["topic1", "topic2", ...],
    "evidence": [{{"doc_id": "...", "page_start": N, "page_end": N}}]
  }},
  "measures": {{
    "description": "How key variables are measured in this literature",
    "common_proxies": ["proxy1", "proxy2", ...],
    "evidence": [{{"doc_id": "...", "page_start": N, "page_end": N, "quote": "..."}}]
  }},
  "identification_strategies": {{
    "description": "How causal effects are identified",
    "common_strategies": ["strategy1", "strategy2", ...],
    "evidence": [{{"doc_id": "...", "page_start": N, "page_end": N, "quote": "..."}}]
  }},
  "consensus": {{
    "description": "Main points of agreement in the literature",
    "key_findings": ["finding1", "finding2", ...],
    "evidence": [{{"doc_id": "...", "page_start": N, "page_end": N, "quote": "..."}}]
  }},
  "debates": {{
    "description": "Points of disagreement or ongoing debates",
    "key_debates": ["debate1", "debate2", ...],
    "evidence": [{{"doc_id": "...", "page_start": N, "page_end": N, "quote": "..."}}]
  }},
  "gaps": {{
    "description": "Identified research gaps and future directions",
    "key_gaps": ["gap1", "gap2", ...],
    "evidence": [{{"doc_id": "...", "page_start": N, "page_end": N, "quote": "..."}}]
  }},
  "entry_points": {{
    "description": "Suggested papers to start reading this literature",
    "recommended_papers": [{{"doc_id": "...", "title": "...", "reason": "..."}}]
  }},
  "coverage": "high|medium|low",
  "needs_human_review": true|false
}}

## Guidelines:
1. Synthesize across papers, not just list individual findings
2. Every claim MUST have evidence with specific doc_id and page numbers
3. If evidence is insufficient for a section, set coverage to "low" and needs_human_review to true
4. Focus on empirical methodology and findings, not just theory
5. Identify both consensus and disagreements in the literature

Output ONLY the JSON object, no additional text."""


def format_evidence_for_prompt(evidence_items: list[dict]) -> str:
    """格式化证据用于 prompt"""
    text_parts = []
    for item in evidence_items:
        doc_id = item.get("doc_id", "")
        title = item.get("title", "Unknown")
        authors = item.get("authors", "Unknown")
        year = item.get("year", "")
        page_start = item.get("page_start", "")
        page_end = item.get("page_end", "")
        text = item.get("text", "")[:800]  # 截断
        
        text_parts.append(f"""
---
Doc ID: {doc_id}
Title: {title}
Authors: {authors}, {year}
Pages: {page_start}-{page_end}
Text: {text}
---""")
    
    return "\n".join(text_parts)



import asyncio

async def acall_llm_summarize(top_entities: str, evidence_text: str, llm_model: str) -> dict | None:
    """调用 LLM 生成社区摘要 (Async)"""
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        return None
    
    url = f"{settings.openrouter_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": COMMUNITY_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": COMMUNITY_SUMMARY_USER_PROMPT_TEMPLATE.format(
                top_entities=top_entities,
                evidence_text=evidence_text,
            )},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        # OpenRouter 格式：禁用推理模型的 reasoning tokens（如 GPT-5 Nano）
        # 使用 effort: low 最小化推理，exclude: true 不返回推理内容
        "reasoning": {
            "effort": "low",
            "exclude": True,
        },
    }
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    
    except Exception as e:
        print(f"LLM summarize error: {e}")
        return None



def summary_to_markdown(summary: dict, comm_id: int) -> str:
    """Convert summary JSON to Markdown format"""
    md_lines = [f"# Research Community {comm_id} Summary", ""]
    
    scope = summary.get("scope", {})
    md_lines.extend([
        "## Scope",
        scope.get("description", "No description provided."),
        "",
        "**Key Topics:** " + ", ".join(scope.get("key_topics", [])),
        ""
    ])
    
    sections = [
        ("Measures", "measures", "common_proxies"),
        ("Identification Strategies", "identification_strategies", "common_strategies"),
        ("Consensus", "consensus", "key_findings"),
        ("Debates", "debates", "key_debates"),
        ("Gaps", "gaps", "key_gaps"),
    ]
    
    for title, key, list_key in sections:
        data = summary.get(key, {})
        md_lines.extend([
            f"## {title}",
            data.get("description", ""),
            ""
        ])
        items = data.get(list_key, [])
        if items:
            md_lines.extend([f"- {item}" for item in items])
        md_lines.append("")
        
    entry = summary.get("entry_points", {})
    md_lines.extend([
        "## Entry Points",
        entry.get("description", ""),
        ""
    ])
    for paper in entry.get("recommended_papers", []):
        md_lines.append(f"- **{paper.get('title', 'Unknown')}**: {paper.get('reason', '')} (Doc: {paper.get('doc_id')})")
        
    return "\n".join(md_lines)

def register_graph_summarize_tools(mcp: FastMCP) -> None:
    """注册 GraphRAG 摘要与导出工具"""


# ============================================================
# 核心逻辑实现 (Module Level)
# ============================================================

async def summarize_community_v1_run(
    comm_id: int,
    pack_id: int | None = None,
    llm_model: str | None = None,
    max_chunks: int = 100,
    style: str = "econ_finance",
) -> dict[str, Any]:
    """生成社区结构化摘要 (Core Implementation)"""
    try:
        settings = get_settings()
        # 优先使用 llm_summarize_model，留空则回退到 llm_model
        actual_llm_model = llm_model or settings.llm_summarize_model or settings.llm_model
        # 验证社区存在
        community = query_one(
            "SELECT comm_id, level FROM communities WHERE comm_id = %s",
            (comm_id,)
        )
        
        if not community:
            return SummarizeCommunityOut(
                comm_id=comm_id,
                pack_id=0,
                summary_json={},
                markdown="",
                error=MCPErrorModel(code="NOT_FOUND", message=f"Community {comm_id} not found"),
            ).model_dump()
        
        # 获取或创建证据包
        actual_pack_id = pack_id
        if not actual_pack_id:
            # 导入并调用 build_community_evidence_pack
            # 注意：此处避免循环导入，如果 graph_community 依赖 graph_summarize 可能会有问题
            # 但此处只引用工具注册，应该没事。或者直接复用 query 逻辑。
            # 为了简单，保持原有逻辑
            
            members = query_all(
                """
                SELECT entity_id, weight
                FROM community_members
                WHERE comm_id = %s
                ORDER BY weight DESC
                """,
                (comm_id,)
            )
            
            if not members:
                return SummarizeCommunityOut(
                    comm_id=comm_id,
                    pack_id=0,
                    summary_json={},
                    markdown="",
                    error=MCPErrorModel(code="NOT_FOUND", message="No members in community"),
                ).model_dump()
            
            entity_ids = [m["entity_id"] for m in members]
            
            # 获取 mentions -> chunks
            mentions = query_all(
                """
                SELECT m.doc_id, m.chunk_id, MAX(m.confidence) AS conf
                FROM mentions m
                WHERE m.entity_id = ANY(%s)
                GROUP BY m.doc_id, m.chunk_id
                ORDER BY conf DESC
                LIMIT 5000
                """,
                (entity_ids,)
            )
            
            # 应用 per_doc_limit
            doc_counts: dict[str, int] = defaultdict(int)
            selected_chunks: list[tuple[str, int]] = []
            per_doc_limit = 4
            
            for m in mentions:
                if doc_counts[m["doc_id"]] < per_doc_limit:
                    selected_chunks.append((m["doc_id"], m["chunk_id"]))
                    doc_counts[m["doc_id"]] += 1
                    if len(selected_chunks) >= max_chunks:
                        break
            
            if not selected_chunks:
                return SummarizeCommunityOut(
                    comm_id=comm_id,
                    pack_id=0,
                    summary_json={},
                    markdown="",
                    error=MCPErrorModel(code="NOT_FOUND", message="No chunks found for community"),
                ).model_dump()
            
            # 创建证据包
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO evidence_packs(query, params_json)
                        VALUES (%s, %s::jsonb)
                        RETURNING pack_id
                        """,
                        (
                            f"Community {comm_id} summary",
                            json.dumps({"comm_id": comm_id, "for": "summary"})
                        )
                    )
                    result = cur.fetchone()
                    actual_pack_id = result["pack_id"]
                    
                    for rank, (doc_id, chunk_id) in enumerate(selected_chunks):
                        cur.execute(
                            """
                            INSERT INTO evidence_pack_items(pack_id, doc_id, chunk_id, rank)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (actual_pack_id, doc_id, chunk_id, rank)
                        )
        
        # 获取证据包内容
        evidence_items = query_all(
            """
            SELECT 
                i.doc_id,
                i.chunk_id,
                c.page_start,
                c.page_end,
                c.text,
                d.title,
                d.authors,
                d.year
            FROM evidence_pack_items i
            JOIN chunks c ON c.chunk_id = i.chunk_id
            JOIN documents d ON d.doc_id = i.doc_id
            WHERE i.pack_id = %s
            ORDER BY i.rank
            """,
            (actual_pack_id,)
        )
        
        if not evidence_items:
            return SummarizeCommunityOut(
                comm_id=comm_id,
                pack_id=actual_pack_id,
                summary_json={},
                markdown="",
                error=MCPErrorModel(code="NOT_FOUND", message="Evidence pack is empty"),
            ).model_dump()
        
        # 获取 top entities
        top_entities = query_all(
            """
            SELECT e.canonical_name, e.type, cm.weight
            FROM community_members cm
            JOIN entities e ON e.entity_id = cm.entity_id
            WHERE cm.comm_id = %s
            ORDER BY cm.weight DESC
            LIMIT 20
            """,
            (comm_id,)
        )
        top_entities_str = ", ".join([
            f"{e['canonical_name']} ({e['type']})"
            for e in top_entities
        ])
        
        # 格式化证据
        evidence_text = format_evidence_for_prompt(evidence_items)
        
        # 调用 LLM (Async)
        summary_json = await acall_llm_summarize(top_entities_str, evidence_text, actual_llm_model)
        
        if not summary_json:
            return SummarizeCommunityOut(
                comm_id=comm_id,
                pack_id=actual_pack_id,
                summary_json={},
                markdown="",
                error=MCPErrorModel(code="LLM_ERROR", message="Failed to generate summary"),
            ).model_dump()
        
        # 生成 Markdown
        markdown = summary_to_markdown(summary_json, comm_id)
        
        # 保存到数据库
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO community_summaries(comm_id, summary_json)
                    VALUES (%s, %s::jsonb)
                    ON CONFLICT (comm_id) DO UPDATE
                    SET summary_json = EXCLUDED.summary_json, updated_at = now()
                    """,
                    (comm_id, json.dumps(summary_json))
                )
        
        return SummarizeCommunityOut(
            comm_id=comm_id,
            pack_id=actual_pack_id,
            summary_json=summary_json,
            markdown=markdown,
        ).model_dump()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return SummarizeCommunityOut(
            comm_id=comm_id,
            pack_id=pack_id or 0,
            summary_json={},
            markdown="",
            error=MCPErrorModel(code="LLM_ERROR", message=str(e)),
        ).model_dump()


async def summarize_all_communities_run(
    level: str | int | None = None,
    concurrency: int = 5,
    comm_ids: list[int] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """批量/并行生成社区摘要 (Core Implementation)"""
    # Normalize level to string "macro" or "micro" to match DB column type (TEXT)
    level_str: str | None = None
    if level is not None:
        l_lower = str(level).lower()
        if l_lower in ["macro", "1"]:
            level_str = "macro"
        elif l_lower in ["micro", "2"]:
            level_str = "micro"
        else:
            level_str = l_lower
    
    # 1. 确定要处理的 communities
    if comm_ids:
        target_ids = comm_ids
    else:
        query = "SELECT comm_id FROM communities WHERE 1=1"
        params = []
        if level_str is not None:
            query += " AND level = %s"
            params.append(level_str)
        
        if not force:
            query += " AND NOT EXISTS (SELECT 1 FROM community_summaries s WHERE s.comm_id = communities.comm_id)"
            
        rows = query_all(query, tuple(params))
        target_ids = [r["comm_id"] for r in rows]
        
    if not target_ids:
        return {"message": "No communities to summarize", "count": 0}
        
    # 2. 并行执行
    sem = asyncio.Semaphore(concurrency)
    
    async def process_one(cid):
        async with sem:
            res = await summarize_community_v1_run(comm_id=cid)
            return {
                "comm_id": cid, 
                "success": not res.get("error"), 
                "error": res.get("error")
            }
            
    tasks = [process_one(cid) for cid in target_ids]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    return {
        "total": len(target_ids),
        "success": success_count,
        "failed": failed_count,
        "details": results[:20]  # 返回前 20 个结果
    }


def register_graph_summarize_tools(mcp: FastMCP) -> None:
    """注册 GraphRAG 摘要与导出工具"""

    @mcp.tool()
    async def summarize_community_v1(
        comm_id: int,
        pack_id: int | None = None,
        llm_model: str | None = None,
        max_chunks: int = 100,
        style: str = "econ_finance",
    ) -> dict[str, Any]:
        """生成社区结构化摘要"""
        return await summarize_community_v1_run(
            comm_id=comm_id,
            pack_id=pack_id,
            llm_model=llm_model,
            max_chunks=max_chunks,
            style=style
        )

    @mcp.tool()
    async def summarize_all_communities(
        level: str | None = None,
        concurrency: int = 5,
        comm_ids: list[int] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """批量/并行生成社区摘要
        
        Args:
            level: 社区层级，"macro" 或 "micro"（或整数 1/2）
            concurrency: 并发数，默认 5
            comm_ids: 指定社区 ID 列表
            force: 是否强制重新生成
        """
        return await summarize_all_communities_run(
            level=level,
            concurrency=concurrency,
            comm_ids=comm_ids,
            force=force
        )

    @mcp.tool()
    def export_evidence_matrix_v1(
        comm_id: int | None = None,
        topic: str | None = None,
        format: str = "json",
        limit_docs: int | None = None,
    ) -> dict[str, Any]:
        """导出证据矩阵
        
        导出 PaperMatrix（论文级）和 ClaimMatrix（结论级）两张表。
        
        Args:
            comm_id: 社区 ID（与 topic 二选一）
            topic: 主题名称或 canonical_key（与 comm_id 二选一）
            format: 输出格式，"json" 或 "csv"
            limit_docs: 限制文档数量
            
        Returns:
            paper_matrix 和 claim_matrix
        """
        try:
            if not comm_id and not topic:
                return ExportEvidenceMatrixOut(
                    error=MCPErrorModel(code="VALIDATION_ERROR", message="Must provide either comm_id or topic"),
                ).model_dump()
            
            # 确定文档集合
            if comm_id:
                # 从社区获取文档
                doc_ids_result = query_all(
                    """
                    SELECT DISTINCT m.doc_id
                    FROM community_members cm
                    JOIN mentions m ON m.entity_id = cm.entity_id
                    WHERE cm.comm_id = %s
                    """,
                    (comm_id,)
                )
            else:
                # 从主题获取文档
                # 先查找 topic entity
                topic_entity = query_one(
                    """
                    SELECT entity_id FROM entities
                    WHERE type = 'Topic' AND (canonical_name ILIKE %s OR canonical_key ILIKE %s)
                    LIMIT 1
                    """,
                    (f"%{topic}%", f"%{topic}%")
                )
                
                if not topic_entity:
                    return ExportEvidenceMatrixOut(
                        error=MCPErrorModel(code="NOT_FOUND", message=f"Topic '{topic}' not found"),
                    ).model_dump()
                
                doc_ids_result = query_all(
                    """
                    SELECT DISTINCT m.doc_id
                    FROM mentions m
                    WHERE m.entity_id = %s
                    """,
                    (topic_entity["entity_id"],)
                )
            
            doc_ids = [r["doc_id"] for r in doc_ids_result]
            
            if not doc_ids:
                return ExportEvidenceMatrixOut(
                    error=MCPErrorModel(code="NOT_FOUND", message="No documents found"),
                ).model_dump()
            
            if limit_docs:
                doc_ids = doc_ids[:limit_docs]
            
            # ===== PaperMatrix =====
            # 获取文档元数据
            docs = query_all(
                """
                SELECT doc_id, title, authors, year, venue, doi
                FROM documents
                WHERE doc_id = ANY(%s)
                """,
                (doc_ids,)
            )
            doc_meta = {d["doc_id"]: d for d in docs}
            
            # 获取每个文档的 topics
            doc_topics = query_all(
                """
                SELECT DISTINCT p.canonical_key AS doc_id, x.canonical_name AS topic
                FROM relations r
                JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                JOIN entities x ON x.entity_id = r.obj_entity_id AND x.type = 'Topic'
                WHERE r.predicate = 'PAPER_HAS_TOPIC' AND p.canonical_key = ANY(%s)
                """,
                (doc_ids,)
            )
            topics_by_doc: dict[str, list[str]] = defaultdict(list)
            for r in doc_topics:
                topics_by_doc[r["doc_id"]].append(r["topic"])
            
            # 获取每个文档的 measures
            doc_measures = query_all(
                """
                SELECT DISTINCT p.canonical_key AS doc_id, x.canonical_name AS measure
                FROM relations r
                JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                JOIN entities x ON x.entity_id = r.obj_entity_id AND x.type = 'MeasureProxy'
                WHERE r.predicate = 'PAPER_USES_MEASURE' AND p.canonical_key = ANY(%s)
                """,
                (doc_ids,)
            )
            measures_by_doc: dict[str, list[str]] = defaultdict(list)
            for r in doc_measures:
                measures_by_doc[r["doc_id"]].append(r["measure"])
            
            # 获取每个文档的 identification strategies
            doc_ids_strat = query_all(
                """
                SELECT DISTINCT p.canonical_key AS doc_id, x.canonical_name AS id_strategy
                FROM relations r
                JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                JOIN entities x ON x.entity_id = r.obj_entity_id AND x.type = 'IdentificationStrategy'
                WHERE r.predicate = 'PAPER_IDENTIFIES_WITH' AND p.canonical_key = ANY(%s)
                """,
                (doc_ids,)
            )
            ids_by_doc: dict[str, list[str]] = defaultdict(list)
            for r in doc_ids_strat:
                ids_by_doc[r["doc_id"]].append(r["id_strategy"])
            
            # 获取每个文档的 methods
            doc_methods = query_all(
                """
                SELECT DISTINCT p.canonical_key AS doc_id, x.canonical_name AS method
                FROM relations r
                JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                JOIN entities x ON x.entity_id = r.obj_entity_id AND x.type = 'Method'
                WHERE r.predicate = 'PAPER_USES_METHOD' AND p.canonical_key = ANY(%s)
                """,
                (doc_ids,)
            )
            methods_by_doc: dict[str, list[str]] = defaultdict(list)
            for r in doc_methods:
                methods_by_doc[r["doc_id"]].append(r["method"])
            
            # 获取每个文档的 settings
            doc_settings = query_all(
                """
                SELECT DISTINCT p.canonical_key AS doc_id, x.canonical_name AS setting
                FROM relations r
                JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                JOIN entities x ON x.entity_id = r.obj_entity_id AND x.type = 'Setting'
                WHERE r.predicate = 'PAPER_IN_SETTING' AND p.canonical_key = ANY(%s)
                """,
                (doc_ids,)
            )
            settings_by_doc: dict[str, list[str]] = defaultdict(list)
            for r in doc_settings:
                settings_by_doc[r["doc_id"]].append(r["setting"])
            
            # 获取每个文档的 top claims
            doc_claims = query_all(
                """
                SELECT doc_id, claim_text, sign, confidence, chunk_id
                FROM claims
                WHERE doc_id = ANY(%s)
                ORDER BY doc_id, confidence DESC
                """,
                (doc_ids,)
            )
            claims_by_doc: dict[str, list[dict]] = defaultdict(list)
            for c in doc_claims:
                if len(claims_by_doc[c["doc_id"]]) < 3:  # Top 3 claims per doc
                    claims_by_doc[c["doc_id"]].append({
                        "claim_text": c["claim_text"],
                        "sign": c["sign"],
                        "chunk_id": c["chunk_id"],
                    })
            
            # 构建 PaperMatrix
            paper_matrix = []
            for doc_id in doc_ids:
                meta = doc_meta.get(doc_id, {})
                paper_matrix.append({
                    "doc_id": doc_id,
                    "title": meta.get("title", ""),
                    "authors": meta.get("authors", ""),
                    "year": meta.get("year"),
                    "venue": meta.get("venue", ""),
                    "topics": topics_by_doc.get(doc_id, []),
                    "measures": measures_by_doc.get(doc_id, []),
                    "identification_strategies": ids_by_doc.get(doc_id, []),
                    "methods": methods_by_doc.get(doc_id, []),
                    "settings": settings_by_doc.get(doc_id, []),
                    "top_claims": claims_by_doc.get(doc_id, []),
                })
            
            # ===== ClaimMatrix =====
            all_claims = query_all(
                """
                SELECT 
                    c.claim_id,
                    c.doc_id,
                    c.chunk_id,
                    c.claim_text,
                    c.sign,
                    c.effect_size_text,
                    c.conditions,
                    c.confidence,
                    ch.page_start,
                    ch.page_end
                FROM claims c
                JOIN chunks ch ON ch.chunk_id = c.chunk_id
                WHERE c.doc_id = ANY(%s)
                ORDER BY c.confidence DESC
                """,
                (doc_ids,)
            )
            
            claim_matrix = []
            for claim in all_claims:
                doc_id = claim["doc_id"]
                claim_matrix.append({
                    "claim_id": claim["claim_id"],
                    "doc_id": doc_id,
                    "chunk_id": claim["chunk_id"],
                    "claim_text": claim["claim_text"],
                    "sign": claim["sign"],
                    "effect_size_text": claim["effect_size_text"],
                    "conditions": claim["conditions"],
                    "confidence": claim["confidence"],
                    "page_start": claim["page_start"],
                    "page_end": claim["page_end"],
                    # 补充 doc 级信息
                    "topics": topics_by_doc.get(doc_id, []),
                    "identification_strategies": ids_by_doc.get(doc_id, []),
                })
            
            return ExportEvidenceMatrixOut(
                paper_matrix=paper_matrix,
                claim_matrix=claim_matrix,
            ).model_dump()
            
        except Exception as e:
            return ExportEvidenceMatrixOut(
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

