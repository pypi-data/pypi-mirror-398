"""GraphRAG 结论分组工具：build_claim_groups_v1, export_claim_matrix_grouped_v1"""

import hashlib
import json
from collections import defaultdict
from typing import Any

from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one
from paperlib_mcp import config
from paperlib_mcp.models_graph import (
    BuildClaimGroupsIn,
    BuildClaimGroupsOut,
    ExportClaimMatrixGroupedIn,
    ExportClaimMatrixGroupedOut,
    MCPErrorModel,
)


def extract_family(text: str, default: str = "general") -> str:
    """从文本中提取家族（简单规则）"""
    text = text.lower()
    if any(k in text for k in ["earnings", "profit", "accrual"]):
        return "earnings"
    if any(k in text for k in ["esg", "csr", "environment", "social"]):
        return "esg"
    if any(k in text for k in ["innovation", "r&d", "patent"]):
        return "innovation"
    if any(k in text for k in ["governance", "board", "ceo"]):
        return "governance"
    return default


def register_graph_claim_grouping_tools(mcp: FastMCP) -> None:
    """注册结论分组工具"""

    @mcp.tool()
    def build_claim_groups_v1(
        scope: str = "all",
        max_claims_per_doc: int = 100,  # v1.1: raised from 20 to improve coverage
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """对结论进行分组/聚类。
        
        Args:
            scope: 处理范围，"all", "comm_id:...", "doc_ids:id1,id2"
            max_claims_per_doc: 每个文档最多处理多少条结论
            dry_run: 是否仅预览
        """
        try:
            # 1. 确定范围
            params = []
            where_clauses = []
            
            if scope.startswith("comm_id:"):
                comm_id = int(scope.split(":", 1)[1])
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM community_members cm
                        JOIN mentions m ON m.entity_id = cm.entity_id
                        WHERE cm.comm_id = %s AND m.doc_id = c.doc_id
                    )
                """)
                params.append(comm_id)
            elif scope.startswith("doc_ids:"):
                doc_ids = scope.split(":", 1)[1].split(",")
                where_clauses.append("c.doc_id = ANY(%s)")
                params.append(doc_ids)

            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # 2. 获取结论及关联信息
            sql = f"""
                SELECT 
                    c.claim_id, c.doc_id, c.claim_text, c.sign, c.conditions,
                    (SELECT e.canonical_key FROM relations r 
                     JOIN entities e ON e.entity_id = r.obj_entity_id
                     WHERE r.subj_entity_id = (SELECT entity_id FROM entities WHERE type='Paper' AND canonical_key = c.doc_id)
                     AND r.predicate = 'PAPER_HAS_TOPIC' LIMIT 1) as topic_key,
                    (SELECT e.canonical_key FROM relations r 
                     JOIN entities e ON e.entity_id = r.obj_entity_id
                     WHERE r.subj_entity_id = (SELECT entity_id FROM entities WHERE type='Paper' AND canonical_key = c.doc_id)
                     AND r.predicate = 'PAPER_IDENTIFIES_WITH' LIMIT 1) as id_family
                FROM claims c
                {where_sql}
                ORDER BY c.doc_id, c.confidence DESC
            """
            claims = query_all(sql, tuple(params))
            
            if not claims:
                return BuildClaimGroupsOut(new_groups=0, total_members=0).model_dump()

            # 3. 分组逻辑
            groups: dict[str, list[int]] = defaultdict(list)
            group_details: dict[str, dict] = {}
            
            doc_counts: dict[str, int] = defaultdict(int)
            
            for c in claims:
                if doc_counts[c["doc_id"]] >= max_claims_per_doc:
                    continue
                doc_counts[c["doc_id"]] += 1
                
                # 构造 group_key
                topic_key = c["topic_key"] or "unknown_topic"
                sign = c["sign"] or "null"
                id_family = c["id_family"] or "general"
                
                # 尝试从 conditions 或 claim_text 提取 outcome/treatment
                conditions = c["conditions"] or {}
                outcome_family = conditions.get("outcome_family") or extract_family(c["claim_text"], "outcome_gen")
                treatment_family = conditions.get("treatment_family") or extract_family(c["claim_text"], "treatment_gen")
                setting = conditions.get("setting") or "general"
                
                group_key = f"{topic_key}|{outcome_family}|{treatment_family}|{sign}|{id_family}|{setting}"
                groups[group_key].append(c["claim_id"])
                
                if group_key not in group_details:
                    # 查找 topic_entity_id
                    topic_ent = query_one("SELECT entity_id FROM entities WHERE canonical_key = %s", (topic_key,))
                    group_details[group_key] = {
                        "topic_entity_id": topic_ent["entity_id"] if topic_ent else None,
                        "sign": sign,
                        "setting": setting,
                        "id_family": id_family
                    }

            if dry_run:
                return BuildClaimGroupsOut(
                    new_groups=len(groups),
                    total_members=sum(len(v) for v in groups.values())
                ).model_dump()

            # 4. 写入数据库
            total_members = 0
            with get_db() as conn:
                for key, claim_ids in groups.items():
                    details = group_details[key]
                    try:
                        with conn.cursor() as cur:
                            with conn.transaction():
                                cur.execute("""
                                    INSERT INTO claim_groups (group_key, topic_entity_id, sign, setting, id_family)
                                    VALUES (%s, %s, %s, %s, %s)
                                    ON CONFLICT (group_key) DO UPDATE SET updated_at = now()
                                    RETURNING group_id
                                """, (key, details["topic_entity_id"], details["sign"], details["setting"], details["id_family"]))
                                group_id = cur.fetchone()["group_id"]
                                
                                for cid in claim_ids:
                                    cur.execute("""
                                        INSERT INTO claim_group_members (group_id, claim_id)
                                        VALUES (%s, %s)
                                        ON CONFLICT (group_id, claim_id) DO NOTHING
                                    """, (group_id, cid))
                                    total_members += cur.rowcount
                    except Exception as e:
                        print(f"Error processing group {key}: {e}")

                # 计算总数 (在 commit 前查询)
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) as count FROM claim_groups")
                    new_groups_total = cur.fetchone()["count"]

            return BuildClaimGroupsOut(
                new_groups=new_groups_total,
                total_members=total_members
            ).model_dump()

        except Exception as e:
            return BuildClaimGroupsOut(
                new_groups=0,
                total_members=0,
                error=MCPErrorModel(code="SYSTEM_ERROR", message=str(e))
            ).model_dump()

    @mcp.tool()
    def export_claim_matrix_grouped_v1(
        comm_id: int | None = None,
        pack_id: int | None = None,
    ) -> dict[str, Any]:
        """导出按分组聚合的结论矩阵。"""
        try:
            where_clauses = []
            params = []
            
            if comm_id:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM claim_group_members cgm
                        JOIN claims c ON c.claim_id = cgm.claim_id
                        JOIN mentions m ON m.doc_id = c.doc_id
                        JOIN community_members cm ON cm.entity_id = m.entity_id
                        WHERE cm.comm_id = %s AND cgm.group_id = g.group_id
                    )
                """)
                params.append(comm_id)
            elif pack_id:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM claim_group_members cgm
                        JOIN claims c ON c.claim_id = cgm.claim_id
                        JOIN evidence_pack_items epi ON epi.chunk_id = c.chunk_id
                        WHERE epi.pack_id = %s AND cgm.group_id = g.group_id
                    )
                """)
                params.append(pack_id)
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            sql = f"""
                SELECT 
                    g.group_id, g.group_key, g.sign, g.id_family, g.setting,
                    e.canonical_name as topic_name,
                    (SELECT COUNT(*) FROM claim_group_members cgm WHERE cgm.group_id = g.group_id) as member_count,
                    (
                        SELECT json_agg(json_build_object(
                            'claim_id', c.claim_id,
                            'doc_id', c.doc_id,
                            'claim_text', c.claim_text,
                            'confidence', c.confidence
                        ))
                        FROM claim_group_members cgm
                        JOIN claims c ON c.claim_id = cgm.claim_id
                        WHERE cgm.group_id = g.group_id
                        LIMIT 5
                    ) as top_claims
                FROM claim_groups g
                LEFT JOIN entities e ON e.entity_id = g.topic_entity_id
                {where_sql}
                ORDER BY member_count DESC
            """
            rows = query_all(sql, tuple(params))
            
            return ExportClaimMatrixGroupedOut(groups=rows).model_dump()
            
        except Exception as e:
            return ExportClaimMatrixGroupedOut(
                error=MCPErrorModel(code="SYSTEM_ERROR", message=str(e))
            ).model_dump()
