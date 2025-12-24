"""GraphRAG 维护工具：graph_status, extract_graph_missing, rebuild_communities, clear_graph"""

from typing import Any

import asyncio
from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one
from paperlib_mcp.settings import get_settings
from paperlib_mcp.models_graph import (
    MCPErrorModel,
    GraphStatusOut,
    ExtractGraphMissingOut,
    ClearGraphOut,
)


# ============================================================
# 工具注册
# ============================================================


def register_graph_maintenance_tools(mcp: FastMCP) -> None:
    """注册 GraphRAG 维护工具"""

    @mcp.tool()
    def graph_status(doc_id: str | None = None) -> dict[str, Any]:
        """查看 GraphRAG 覆盖状态
        
        统计每个文档（或全局）的 entities、mentions、claims 覆盖率。
        
        Args:
            doc_id: 文档 ID（可选，若无则返回全局统计）
            
        Returns:
            覆盖率统计信息
        """
        try:
            if doc_id:
                # 单文档统计
                chunks_count = query_one(
                    "SELECT COUNT(*) as count FROM chunks WHERE doc_id = %s",
                    (doc_id,)
                )
                mentions_count = query_one(
                    "SELECT COUNT(*) as count FROM mentions WHERE doc_id = %s",
                    (doc_id,)
                )
                claims_count = query_one(
                    "SELECT COUNT(*) as count FROM claims WHERE doc_id = %s",
                    (doc_id,)
                )
                
                # 获取该文档关联的实体数
                entities_count = query_one(
                    """
                    SELECT COUNT(DISTINCT entity_id) as count
                    FROM mentions
                    WHERE doc_id = %s
                    """,
                    (doc_id,)
                )
                
                # 获取该文档的关系数
                relations_count = query_one(
                    """
                    SELECT COUNT(*) as count
                    FROM relations r
                    JOIN entities p ON p.entity_id = r.subj_entity_id
                    WHERE p.type = 'Paper' AND p.canonical_key = %s
                    """,
                    (doc_id,)
                )
                
                coverage = {
                    "doc_id": doc_id,
                    "chunks": chunks_count["count"] if chunks_count else 0,
                    "mentions": mentions_count["count"] if mentions_count else 0,
                    "claims": claims_count["count"] if claims_count else 0,
                    "entities_referenced": entities_count["count"] if entities_count else 0,
                    "relations": relations_count["count"] if relations_count else 0,
                    "is_extracted": (mentions_count["count"] if mentions_count else 0) > 0,
                }
            else:
                # 全局统计
                total_docs = query_one("SELECT COUNT(*) as count FROM documents")
                total_chunks = query_one("SELECT COUNT(*) as count FROM chunks")
                total_entities = query_one("SELECT COUNT(*) as count FROM entities")
                total_mentions = query_one("SELECT COUNT(*) as count FROM mentions")
                total_relations = query_one("SELECT COUNT(*) as count FROM relations")
                total_claims = query_one("SELECT COUNT(*) as count FROM claims")
                total_communities = query_one("SELECT COUNT(*) as count FROM communities")
                
                # 已抽取的文档数（有 mentions 的文档）
                extracted_docs = query_one(
                    "SELECT COUNT(DISTINCT doc_id) as count FROM mentions"
                )
                
                # 有社区摘要的社区数
                summarized_communities = query_one(
                    "SELECT COUNT(*) as count FROM community_summaries"
                )
                
                # 实体类型分布
                entity_types = query_all(
                    """
                    SELECT type, COUNT(*) as count
                    FROM entities
                    GROUP BY type
                    ORDER BY count DESC
                    """
                )
                
                coverage = {
                    "total_documents": total_docs["count"] if total_docs else 0,
                    "extracted_documents": extracted_docs["count"] if extracted_docs else 0,
                    "extraction_coverage": (
                        round(extracted_docs["count"] / total_docs["count"] * 100, 1)
                        if total_docs and total_docs["count"] > 0 else 0
                    ),
                    "total_chunks": total_chunks["count"] if total_chunks else 0,
                    "total_entities": total_entities["count"] if total_entities else 0,
                    "total_mentions": total_mentions["count"] if total_mentions else 0,
                    "total_relations": total_relations["count"] if total_relations else 0,
                    "total_claims": total_claims["count"] if total_claims else 0,
                    "total_communities": total_communities["count"] if total_communities else 0,
                    "summarized_communities": summarized_communities["count"] if summarized_communities else 0,
                    "entity_type_distribution": {r["type"]: r["count"] for r in entity_types},
                }
            
            return GraphStatusOut(coverage=coverage).model_dump()
            
        except Exception as e:
            return GraphStatusOut(
                coverage={},
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

    @mcp.tool()
    async def extract_graph_missing(
        limit_docs: int = 50,
        llm_model: str | None = None,
        min_confidence: float = 0.8,
        concurrency: int = 30,
        doc_concurrency: int = 15,
        max_chunks: int = 60,
    ) -> dict[str, Any]:
        """批量补跑未抽取的文档
        
        找出没有 mentions 的文档，并对它们执行 extract_graph_v1。
        
        Args:
            limit_docs: 最大处理文档数，默认 50
            llm_model: LLM 模型，默认使用环境变量 LLM_MODEL 配置
            min_confidence: 最小置信度阈值
            
        Returns:
            处理的文档数和文档 ID 列表
        """
        try:
            settings = get_settings()
            actual_llm_model = llm_model or settings.llm_model
            # 找出未抽取的文档
            missing_docs = query_all(
                """
                SELECT d.doc_id
                FROM documents d
                LEFT JOIN mentions m ON m.doc_id = d.doc_id
                GROUP BY d.doc_id
                HAVING COUNT(m.mention_id) = 0
                ORDER BY d.created_at DESC
                LIMIT %s
                """,
                (limit_docs,)
            )
            
            if not missing_docs:
                return ExtractGraphMissingOut(
                    processed_docs=0,
                    doc_ids=[],
                ).model_dump()
            
            # 导入抽取工具
            from paperlib_mcp.tools.graph_extract import (
                extract_graph_v1_run,
                HIGH_VALUE_KEYWORDS_DEFAULT,
            )
            
            processed_doc_ids = []
            
            # 使用 Semaphore 限制文档级并发
            sem = asyncio.Semaphore(doc_concurrency)

            async def process_single_doc(doc_row):
                async with sem:
                    doc_id = doc_row["doc_id"]
                    
                    # 获取该文档的高价值 chunks
                    fts_query = " OR ".join(f"'{kw}'" for kw in HIGH_VALUE_KEYWORDS_DEFAULT)
                    chunks = query_all(
                        """
                        SELECT chunk_id, doc_id, page_start, page_end, text
                        FROM chunks
                        WHERE doc_id = %s
                        AND tsv @@ websearch_to_tsquery('english', %s)
                        ORDER BY ts_rank(tsv, websearch_to_tsquery('english', %s)) DESC
                        LIMIT %s
                        """,
                        (doc_id, fts_query, fts_query, max_chunks)
                    )
                    
                    if not chunks:
                        # 没有高价值 chunks，使用所有 chunks
                        chunks = query_all(
                            """
                            SELECT chunk_id, doc_id, page_start, page_end, text
                            FROM chunks
                            WHERE doc_id = %s
                            ORDER BY chunk_index
                            LIMIT %s
                            """,
                            (doc_id, max_chunks)
                        )
                    
                    if not chunks:
                        return None
                    
                    # 直接调用优化后的 extract_graph_v1_run (支持并行)
                    # from paperlib_mcp.tools.graph_extract import extract_graph_v1_run # Already imported above
                    
                    # 提取 chunk_ids
                    chunk_ids = [c["chunk_id"] for c in chunks]
                    
                    await extract_graph_v1_run(
                        doc_id=doc_id,
                        chunk_ids=chunk_ids,
                        mode="custom", # 使用传入的 chunk_ids
                        max_chunks=len(chunks),
                        llm_model=actual_llm_model,
                        min_confidence=min_confidence,
                        concurrency=concurrency,
                    )
                            
                    return doc_id

            # 并发执行所有文档
            tasks = [process_single_doc(doc) for doc in missing_docs]
            results = await asyncio.gather(*tasks)
            
            # 收集能够成功处理的 doc_id
            processed_doc_ids = [r for r in results if r is not None]
            
            return ExtractGraphMissingOut(
                processed_docs=len(processed_doc_ids),
                doc_ids=processed_doc_ids,
            ).model_dump()
            
        except Exception as e:
            return ExtractGraphMissingOut(
                processed_docs=0,
                doc_ids=[],
                error=MCPErrorModel(code="LLM_ERROR", message=str(e)),
            ).model_dump()

    @mcp.tool()
    def rebuild_communities(
        level: str = "macro",
        min_df: int = 3,
        resolution: float = 1.0,
    ) -> dict[str, Any]:
        """重建社区
        
        清除指定层级的旧社区并重新构建。
        
        Args:
            level: 社区层级，"macro" 或 "micro"
            min_df: 节点最小文档频率，默认 3
            resolution: Leiden 分辨率参数，默认 1.0
            
        Returns:
            新社区列表
        """
        try:
            # 直接调用 build_communities_v1 with rebuild=True
            from paperlib_mcp.tools.graph_community import register_graph_community_tools
            
            # 由于我们需要直接调用逻辑，这里重新实现简化版本
            # 或者导入并使用内部逻辑
            
            try:
                import igraph as ig
                import leidenalg
            except ImportError:
                return {
                    "communities": [],
                    "error": {
                        "code": "DEPENDENCY_ERROR",
                        "message": "igraph and leidenalg are required"
                    }
                }
            
            from paperlib_mcp.tools.graph_community import (
                COMMUNITY_ENTITY_TYPES,
                get_edge_weight,
            )
            from paperlib_mcp.models_graph import CommunityBrief
            from collections import defaultdict
            import json
            
            with get_db() as conn:
                # 清除旧结果
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM community_members 
                        WHERE comm_id IN (SELECT comm_id FROM communities WHERE level = %s)
                        """,
                        (level,)
                    )
                    cur.execute(
                        """
                        DELETE FROM community_summaries 
                        WHERE comm_id IN (SELECT comm_id FROM communities WHERE level = %s)
                        """,
                        (level,)
                    )
                    cur.execute(
                        "DELETE FROM communities WHERE level = %s",
                        (level,)
                    )
                
                # 获取 Paper->Entity 关系
                relations = query_all(
                    """
                    SELECT 
                        p.entity_id AS paper_eid,
                        p.canonical_key AS doc_id,
                        x.entity_id AS node_eid,
                        x.type AS node_type,
                        x.canonical_name
                    FROM relations r
                    JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                    JOIN entities x ON x.entity_id = r.obj_entity_id
                    WHERE r.predicate IN (
                        'PAPER_HAS_TOPIC', 'PAPER_USES_MEASURE', 'PAPER_IDENTIFIES_WITH',
                        'PAPER_IN_SETTING', 'PAPER_USES_DATA'
                    )
                    AND x.type = ANY(%s)
                    """,
                    (COMMUNITY_ENTITY_TYPES,)
                )
                
                if not relations:
                    return {"communities": [], "error": {"code": "NOT_FOUND", "message": "No relations found"}}
                
                # 构建图并聚类（同 build_communities_v1）
                paper_to_nodes: dict[str, set[int]] = defaultdict(set)
                node_info: dict[int, dict] = {}
                
                for r in relations:
                    paper_to_nodes[r["doc_id"]].add(r["node_eid"])
                    if r["node_eid"] not in node_info:
                        node_info[r["node_eid"]] = {
                            "entity_id": r["node_eid"],
                            "type": r["node_type"],
                            "canonical_name": r["canonical_name"],
                        }
                
                node_df: dict[int, int] = defaultdict(int)
                for doc_id, nodes in paper_to_nodes.items():
                    for node_id in nodes:
                        node_df[node_id] += 1
                
                valid_nodes = {nid for nid, df in node_df.items() if df >= min_df}
                
                if not valid_nodes:
                    return {"communities": [], "error": {"code": "NOT_FOUND", "message": f"No nodes with df >= {min_df}"}}
                
                # 构建边
                edge_counts: dict[tuple[int, int], float] = defaultdict(float)
                for doc_id, nodes in paper_to_nodes.items():
                    valid_doc_nodes = [n for n in nodes if n in valid_nodes]
                    for i, n1 in enumerate(valid_doc_nodes):
                        for n2 in valid_doc_nodes[i+1:]:
                            key = (min(n1, n2), max(n1, n2))
                            weight = get_edge_weight(node_info[n1]["type"], node_info[n2]["type"])
                            edge_counts[key] += weight
                
                if not edge_counts:
                    return {"communities": [], "error": {"code": "NOT_FOUND", "message": "No edges found"}}
                
                # 构建 igraph
                node_list = sorted(valid_nodes)
                node_to_idx = {nid: idx for idx, nid in enumerate(node_list)}
                
                edges = []
                weights = []
                for (n1, n2), w in edge_counts.items():
                    edges.append((node_to_idx[n1], node_to_idx[n2]))
                    weights.append(w)
                
                g = ig.Graph(n=len(node_list), edges=edges, directed=False)
                g.es["weight"] = weights
                
                # Leiden 聚类
                partition = leidenalg.find_partition(
                    g, leidenalg.RBConfigurationVertexPartition,
                    weights="weight", resolution_parameter=resolution
                )
                
                # 写入数据库
                communities_result = []
                community_members_map: dict[int, list[tuple[int, float]]] = defaultdict(list)
                
                for node_idx, comm_idx in enumerate(partition.membership):
                    node_id = node_list[node_idx]
                    weight = float(node_df[node_id])
                    community_members_map[comm_idx].append((node_id, weight))
                
                with conn.cursor() as cur:
                    for comm_idx, members in community_members_map.items():
                        if len(members) < 2:
                            continue
                        
                        cur.execute(
                            """
                            INSERT INTO communities(level, method, params)
                            VALUES (%s, 'leiden', %s::jsonb)
                            RETURNING comm_id
                            """,
                            (level, json.dumps({"resolution": resolution, "min_df": min_df}))
                        )
                        result = cur.fetchone()
                        comm_id = result["comm_id"]
                        
                        for node_id, weight in members:
                            cur.execute(
                                """
                                INSERT INTO community_members(comm_id, entity_id, role, weight)
                                VALUES (%s, %s, 'member', %s)
                                """,
                                (comm_id, node_id, weight)
                            )
                        
                        sorted_members = sorted(members, key=lambda x: x[1], reverse=True)
                        top_entities = []
                        for node_id, weight in sorted_members[:20]:
                            info = node_info.get(node_id, {})
                            top_entities.append({
                                "entity_id": node_id,
                                "type": info.get("type", ""),
                                "canonical_name": info.get("canonical_name", ""),
                                "weight": weight,
                            })
                        
                        communities_result.append({
                            "comm_id": comm_id,
                            "size": len(members),
                            "top_entities": top_entities,
                        })
                
                communities_result.sort(key=lambda x: x["size"], reverse=True)
                
                return {"communities": communities_result}
                
        except Exception as e:
            return {"communities": [], "error": {"code": "DB_CONN_ERROR", "message": str(e)}}

    @mcp.tool()
    def clear_graph(doc_id: str | None = None, clear_all: bool = False) -> dict[str, Any]:
        """清理 GraphRAG 数据
        
        清理指定文档或全部的 GraphRAG 数据。
        
        Args:
            doc_id: 文档 ID（清理单个文档）
            clear_all: 是否清理全部（危险操作）
            
        Returns:
            清理结果，包含删除的记录数
        """
        try:
            if not doc_id and not clear_all:
                return ClearGraphOut(
                    ok=False,
                    error=MCPErrorModel(code="VALIDATION_ERROR", message="Must provide doc_id or set clear_all=True"),
                ).model_dump()
            
            deleted_counts = {}
            
            with get_db() as conn:
                with conn.cursor() as cur:
                    if clear_all:
                        # 按顺序清理（先清理依赖表）
                        cur.execute("DELETE FROM community_summaries")
                        deleted_counts["community_summaries"] = cur.rowcount
                        
                        cur.execute("DELETE FROM community_members")
                        deleted_counts["community_members"] = cur.rowcount
                        
                        cur.execute("DELETE FROM communities")
                        deleted_counts["communities"] = cur.rowcount
                        
                        cur.execute("DELETE FROM claims")
                        deleted_counts["claims"] = cur.rowcount
                        
                        cur.execute("DELETE FROM relations")
                        deleted_counts["relations"] = cur.rowcount
                        
                        cur.execute("DELETE FROM mentions")
                        deleted_counts["mentions"] = cur.rowcount
                        
                        cur.execute("DELETE FROM entity_aliases")
                        deleted_counts["entity_aliases"] = cur.rowcount
                        
                        cur.execute("DELETE FROM entities")
                        deleted_counts["entities"] = cur.rowcount
                        
                        cur.execute("DELETE FROM entity_merge_log")
                        deleted_counts["entity_merge_log"] = cur.rowcount
                    else:
                        # 清理单个文档
                        # 删除 claims
                        cur.execute("DELETE FROM claims WHERE doc_id = %s", (doc_id,))
                        deleted_counts["claims"] = cur.rowcount
                        
                        # 删除 mentions
                        cur.execute("DELETE FROM mentions WHERE doc_id = %s", (doc_id,))
                        deleted_counts["mentions"] = cur.rowcount
                        
                        # 删除 relations（通过 evidence）
                        cur.execute(
                            "DELETE FROM relations WHERE evidence->>'doc_id' = %s",
                            (doc_id,)
                        )
                        deleted_counts["relations"] = cur.rowcount
                        
                        # 可选：删除 Paper entity
                        # cur.execute(
                        #     "DELETE FROM entities WHERE type = 'Paper' AND canonical_key = %s",
                        #     (doc_id,)
                        # )
                        # deleted_counts["paper_entity"] = cur.rowcount
            
            return ClearGraphOut(
                ok=True,
                deleted_counts=deleted_counts,
            ).model_dump()
            
        except Exception as e:
            return ClearGraphOut(
                ok=False,
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

