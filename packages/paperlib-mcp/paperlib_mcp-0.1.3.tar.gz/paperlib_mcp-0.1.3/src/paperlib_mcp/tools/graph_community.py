"""GraphRAG 社区构建工具：build_communities_v1, build_community_evidence_pack"""

import json
from collections import defaultdict
from typing import Any

from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one
from paperlib_mcp.models_graph import (
    EntityType,
    MCPErrorModel,
    CommunityBrief,
    BuildCommunitiesOut,
    BuildCommunityEvidencePackOut,
)


# ============================================================
# 社区构建常量
# ============================================================

# v1 参与社区构建的实体类型
COMMUNITY_ENTITY_TYPES = [
    EntityType.Topic.value,
    EntityType.MeasureProxy.value,
    EntityType.IdentificationStrategy.value,
    EntityType.Setting.value,
    EntityType.DataSource.value,
]

# 边权重配置
EDGE_WEIGHTS = {
    (EntityType.Topic.value, EntityType.MeasureProxy.value): 2.0,
    (EntityType.Topic.value, EntityType.IdentificationStrategy.value): 2.0,
    (EntityType.MeasureProxy.value, EntityType.IdentificationStrategy.value): 1.5,
    (EntityType.Topic.value, EntityType.Setting.value): 1.0,
    (EntityType.IdentificationStrategy.value, EntityType.Setting.value): 1.0,
}


def get_edge_weight(type1: str, type2: str) -> float:
    """获取两种实体类型之间的边权重"""
    key = (type1, type2)
    if key in EDGE_WEIGHTS:
        return EDGE_WEIGHTS[key]
    key = (type2, type1)
    if key in EDGE_WEIGHTS:
        return EDGE_WEIGHTS[key]
    return 1.0


# ============================================================
# 工具注册
# ============================================================


def register_graph_community_tools(mcp: FastMCP) -> None:
    """注册 GraphRAG 社区构建工具"""

    @mcp.tool()
    def build_communities_v1(
        level: str = "macro",
        min_df: int = 3,
        resolution: float = 1.0,
        max_nodes: int = 20000,
        rebuild: bool = False,
    ) -> dict[str, Any]:
        """构建主题社区
        
        从 Paper->Entity 关系构建共现图，使用 Leiden 算法聚类。
        
        Args:
            level: 社区层级，"macro" 或 "micro"
            min_df: 节点至少出现在 N 篇 paper，默认 3
            resolution: Leiden 分辨率参数，默认 1.0
            max_nodes: 最大节点数，默认 20000
            rebuild: 是否重建（清除同 level 旧结果），默认 False
            
        Returns:
            社区列表，每个包含 comm_id、大小和 top entities
        """
        try:
            # 尝试导入社区发现库
            try:
                import igraph as ig
                import leidenalg
            except ImportError:
                return BuildCommunitiesOut(
                    error=MCPErrorModel(
                        code="DEPENDENCY_ERROR",
                        message="igraph and leidenalg are required. Install with: pip install igraph leidenalg"
                    ),
                ).model_dump()
            
            with get_db() as conn:
                # 如果 rebuild，先清除旧结果
                if rebuild:
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
                
                # 1. 获取 Paper->Entity 关系
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
                    return BuildCommunitiesOut(
                        communities=[],
                        error=MCPErrorModel(code="NOT_FOUND", message="No Paper->Entity relations found"),
                    ).model_dump()
                
                # 2. 计算节点 document frequency
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
                
                # 计算 df
                node_df: dict[int, int] = defaultdict(int)
                for doc_id, nodes in paper_to_nodes.items():
                    for node_id in nodes:
                        node_df[node_id] += 1
                
                # 3. 过滤低频节点
                valid_nodes = {nid for nid, df in node_df.items() if df >= min_df}
                
                if not valid_nodes:
                    return BuildCommunitiesOut(
                        communities=[],
                        error=MCPErrorModel(
                            code="NOT_FOUND",
                            message=f"No nodes with df >= {min_df}"
                        ),
                    ).model_dump()
                
                # 限制节点数量
                if len(valid_nodes) > max_nodes:
                    # 保留 df 最高的节点
                    sorted_nodes = sorted(valid_nodes, key=lambda x: node_df[x], reverse=True)
                    valid_nodes = set(sorted_nodes[:max_nodes])
                
                # 4. 构建共现边
                edge_counts: dict[tuple[int, int], float] = defaultdict(float)
                
                for doc_id, nodes in paper_to_nodes.items():
                    valid_doc_nodes = [n for n in nodes if n in valid_nodes]
                    # 两两配对
                    for i, n1 in enumerate(valid_doc_nodes):
                        for n2 in valid_doc_nodes[i+1:]:
                            if n1 < n2:
                                key = (n1, n2)
                            else:
                                key = (n2, n1)
                            
                            # 获取边权重
                            weight = get_edge_weight(
                                node_info[n1]["type"],
                                node_info[n2]["type"]
                            )
                            edge_counts[key] += weight
                
                if not edge_counts:
                    return BuildCommunitiesOut(
                        communities=[],
                        error=MCPErrorModel(code="NOT_FOUND", message="No edges found"),
                    ).model_dump()
                
                # 5. 构建 igraph 图
                # 创建节点映射
                node_list = sorted(valid_nodes)
                node_to_idx = {nid: idx for idx, nid in enumerate(node_list)}
                
                edges = []
                weights = []
                for (n1, n2), w in edge_counts.items():
                    edges.append((node_to_idx[n1], node_to_idx[n2]))
                    weights.append(w)
                
                g = ig.Graph(n=len(node_list), edges=edges, directed=False)
                g.es["weight"] = weights
                
                # 6. Leiden 聚类
                partition = leidenalg.find_partition(
                    g,
                    leidenalg.RBConfigurationVertexPartition,
                    weights="weight",
                    resolution_parameter=resolution,
                )
                
                # 7. 写入数据库
                communities_result: list[CommunityBrief] = []
                
                # 收集每个社区的成员
                community_members_map: dict[int, list[tuple[int, float]]] = defaultdict(list)
                
                for node_idx, comm_idx in enumerate(partition.membership):
                    node_id = node_list[node_idx]
                    # 使用 df 作为权重
                    weight = float(node_df[node_id])
                    community_members_map[comm_idx].append((node_id, weight))
                
                # 写入社区
                with conn.cursor() as cur:
                    for comm_idx, members in community_members_map.items():
                        if len(members) < 2:  # 跳过太小的社区
                            continue
                        
                        # 创建社区
                        cur.execute(
                            """
                            INSERT INTO communities(level, method, params)
                            VALUES (%s, 'leiden', %s::jsonb)
                            RETURNING comm_id
                            """,
                            (level, json.dumps({
                                "resolution": resolution,
                                "min_df": min_df,
                                "original_community_idx": comm_idx,
                            }))
                        )
                        result = cur.fetchone()
                        comm_id = result["comm_id"]
                        
                        # 写入成员
                        for node_id, weight in members:
                            cur.execute(
                                """
                                INSERT INTO community_members(comm_id, entity_id, role, weight)
                                VALUES (%s, %s, 'member', %s)
                                """,
                                (comm_id, node_id, weight)
                            )
                        
                        # 排序获取 top entities
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
                        
                        communities_result.append(CommunityBrief(
                            comm_id=comm_id,
                            size=len(members),
                            top_entities=top_entities,
                        ))
                
                # 按大小排序
                communities_result.sort(key=lambda x: x.size, reverse=True)
                
                return BuildCommunitiesOut(
                    communities=communities_result,
                ).model_dump()
                
        except Exception as e:
            return BuildCommunitiesOut(
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

    @mcp.tool()
    def build_community_evidence_pack(
        comm_id: int,
        max_chunks: int = 100,
        per_doc_limit: int = 4,
    ) -> dict[str, Any]:
        """为社区构建证据包
        
        从社区 top entities 的 mentions 中采样 chunks，写入证据包。
        
        Args:
            comm_id: 社区 ID
            max_chunks: 最大 chunk 数量，默认 100
            per_doc_limit: 每篇文档最多 chunk 数，默认 4
            
        Returns:
            证据包信息，包含 pack_id、文档数和 chunk 数
        """
        try:
            # 验证社区存在
            community = query_one(
                "SELECT comm_id, level FROM communities WHERE comm_id = %s",
                (comm_id,)
            )
            
            if not community:
                return BuildCommunityEvidencePackOut(
                    pack_id=0,
                    docs=0,
                    chunks=0,
                    error=MCPErrorModel(code="NOT_FOUND", message=f"Community {comm_id} not found"),
                ).model_dump()
            
            # 获取社区成员（按权重排序）
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
                return BuildCommunityEvidencePackOut(
                    pack_id=0,
                    docs=0,
                    chunks=0,
                    error=MCPErrorModel(code="NOT_FOUND", message="No members in community"),
                ).model_dump()
            
            entity_ids = [m["entity_id"] for m in members]
            
            # 获取这些实体的 mentions -> chunks
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
            
            if not mentions:
                return BuildCommunityEvidencePackOut(
                    pack_id=0,
                    docs=0,
                    chunks=0,
                    error=MCPErrorModel(code="NOT_FOUND", message="No mentions found for community entities"),
                ).model_dump()
            
            # 应用 per_doc_limit
            doc_counts: dict[str, int] = defaultdict(int)
            selected_chunks: list[tuple[str, int]] = []
            
            for m in mentions:
                if doc_counts[m["doc_id"]] < per_doc_limit:
                    selected_chunks.append((m["doc_id"], m["chunk_id"]))
                    doc_counts[m["doc_id"]] += 1
                    
                    if len(selected_chunks) >= max_chunks:
                        break
            
            if not selected_chunks:
                return BuildCommunityEvidencePackOut(
                    pack_id=0,
                    docs=0,
                    chunks=0,
                    error=MCPErrorModel(code="NOT_FOUND", message="No chunks selected"),
                ).model_dump()
            
            # 创建证据包
            with get_db() as conn:
                with conn.cursor() as cur:
                    # 创建包
                    cur.execute(
                        """
                        INSERT INTO evidence_packs(query, params_json)
                        VALUES (%s, %s::jsonb)
                        RETURNING pack_id
                        """,
                        (
                            f"Community {comm_id} evidence",
                            json.dumps({
                                "comm_id": comm_id,
                                "max_chunks": max_chunks,
                                "per_doc_limit": per_doc_limit,
                            })
                        )
                    )
                    result = cur.fetchone()
                    pack_id = result["pack_id"]
                    
                    # 写入条目
                    for rank, (doc_id, chunk_id) in enumerate(selected_chunks):
                        cur.execute(
                            """
                            INSERT INTO evidence_pack_items(pack_id, doc_id, chunk_id, rank)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (pack_id, doc_id, chunk_id, rank)
                        )
            
            return BuildCommunityEvidencePackOut(
                pack_id=pack_id,
                docs=len(doc_counts),
                chunks=len(selected_chunks),
            ).model_dump()
            
        except Exception as e:
            return BuildCommunityEvidencePackOut(
                pack_id=0,
                docs=0,
                chunks=0,
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

