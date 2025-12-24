"""GraphRAG 关系规范化工具：canonicalize_relations_v1, export_relations_compact_v1"""

import hashlib
import json
from typing import Any

from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one
from paperlib_mcp.models_graph import (
    CanonicalizeRelationsIn,
    CanonicalizeRelationsOut,
    ExportRelationsCompactIn,
    ExportRelationsCompactOut,
    MCPErrorModel,
)


def compute_canonical_rel_hash(subj_id: int, predicate: str, obj_id: int, qualifiers_json: str) -> str:
    """计算规范化关系哈希 (v1.1: 使用明确分隔符)"""
    # 使用 \x1f (Unit Separator) 避免拼接歧义
    content = f"{subj_id}\x1f{predicate}\x1f{obj_id}\x1f{qualifiers_json}"
    return hashlib.sha256(content.encode()).hexdigest()


def normalize_qualifiers(qualifiers: dict | None, keys_keep: list[str]) -> str:
    """规范化 qualifiers 为稳定的 JSON 字符串 (v1.1)"""
    if not qualifiers:
        return "{}"
    # 只保留白名单字段，递归排序，紧凑格式
    filtered = {k: qualifiers[k] for k in sorted(keys_keep) if k in qualifiers and qualifiers[k] not in (None, "", [], {})}
    return json.dumps(filtered, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def register_graph_relation_canonicalize_tools(mcp: FastMCP) -> None:
    """注册关系规范化工具"""

    @mcp.tool()
    def canonicalize_relations_v1(
        scope: str = "all",
        predicate_whitelist: list[str] | None = None,
        qualifier_keys_keep: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """规范化关系并合并重复项，保留所有证据。
        
        Args:
            scope: 处理范围，"all", "doc_id:...", "comm_id:..."
            predicate_whitelist: 只处理这些谓词
            qualifier_keys_keep: 规范化时保留哪些 qualifier 字段
            dry_run: 仅计算建议，不写入数据库
        """
        try:
            if qualifier_keys_keep is None:
                qualifier_keys_keep = ["id_family", "measure_family", "setting_country", "sample_period_bin"]

            # 1. 构建查询范围
            params = []
            where_clauses = []
            
            if scope.startswith("doc_id:"):
                doc_id = scope.split(":", 1)[1]
                # 这里假设关系与文档的关联是通过 evidence 字段里的 doc_id
                # 或者通过关系关联的 subj/obj (Paper entity)
                where_clauses.append("r.evidence->>'doc_id' = %s")
                params.append(doc_id)
            elif scope.startswith("comm_id:"):
                comm_id = int(scope.split(":", 1)[1])
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM community_members cm 
                        WHERE cm.comm_id = %s AND (cm.entity_id = r.subj_entity_id OR cm.entity_id = r.obj_entity_id)
                    )
                """)
                params.append(comm_id)
            
            if predicate_whitelist:
                where_clauses.append("r.predicate = ANY(%s)")
                params.append(predicate_whitelist)
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # 2. 获取原始数据
            sql = f"""
                SELECT rel_id, subj_entity_id, predicate, obj_entity_id, qualifiers, confidence, evidence 
                FROM relations r
                {where_sql}
            """
            relations = query_all(sql, tuple(params))
            
            if not relations:
                return CanonicalizeRelationsOut(
                    new_canonical_relations=0,
                    new_evidence_records=0,
                    skipped_relations=0
                ).model_dump()

            # 3. 规范化并分组
            stats = {"new_canonical": 0, "new_evidence": 0, "skipped": 0}
            
            if dry_run:
                # 仅统计
                keys = set()
                for r in relations:
                    q_json = normalize_qualifiers(r["qualifiers"], qualifier_keys_keep)
                    key = compute_canonical_rel_hash(r["subj_entity_id"], r["predicate"], r["obj_entity_id"], q_json)
                    keys.add(key)
                return CanonicalizeRelationsOut(
                    new_canonical_relations=len(keys),
                    new_evidence_records=len(relations),
                    skipped_relations=0
                ).model_dump()

            # 4. 执行写入
            with get_db() as conn:
                for r in relations:
                    # 使用子事务（SAVEPOINT），即使某几条关系报错也不影响整批
                    try:
                        with conn.cursor() as cur:
                            with conn.transaction():
                                # 规范化 qualifiers (v1.1)
                                q_json = normalize_qualifiers(r["qualifiers"], qualifier_keys_keep)
                                key = compute_canonical_rel_hash(r["subj_entity_id"], r["predicate"], r["obj_entity_id"], q_json)
                                
                                # UPSERT canonical_relations
                                cur.execute("""
                                    INSERT INTO canonical_relations (subj_entity_id, predicate_norm, obj_entity_id, qualifiers_norm, canonical_key)
                                    VALUES (%s, %s, %s, %s::jsonb, %s)
                                    ON CONFLICT (canonical_key) DO UPDATE SET created_at = EXCLUDED.created_at
                                    RETURNING canon_rel_id
                                """, (r["subj_entity_id"], r["predicate"], r["obj_entity_id"], q_json, key))
                                canon_rel_id = cur.fetchone()["canon_rel_id"]
                                
                                # 插入证据
                                evidence_data = r["evidence"] or {}
                                doc_id = evidence_data.get("doc_id")
                                chunk_id = evidence_data.get("chunk_id")
                                quote = evidence_data.get("quote")
                                
                                cur.execute("""
                                    INSERT INTO canonical_relation_evidence (canon_rel_id, doc_id, chunk_id, quote, confidence, source_rel_id)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (canon_rel_id, source_rel_id) DO NOTHING
                                """, (canon_rel_id, doc_id, chunk_id, quote, r["confidence"], r["rel_id"]))
                                
                                stats["new_evidence"] += 1
                    except Exception as e:
                        print(f"Error processing relation {r['rel_id']}: {e}")
                        stats["skipped"] += 1
                
                # 计算实际新增的 canonical 关系数 (在 commit 前查询)
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) as count FROM canonical_relations")
                    stats["new_canonical"] = cur.fetchone()["count"]

            return CanonicalizeRelationsOut(
                new_canonical_relations=stats["new_canonical"],
                new_evidence_records=stats["new_evidence"],
                skipped_relations=stats["skipped"]
            ).model_dump()
            
        except Exception as e:
            return CanonicalizeRelationsOut(
                new_canonical_relations=0,
                new_evidence_records=0,
                skipped_relations=0,
                error=MCPErrorModel(code="SYSTEM_ERROR", message=str(e))
            ).model_dump()

    @mcp.tool()
    def export_relations_compact_v1(
        comm_id: int | None = None,
        pack_id: int | None = None,
    ) -> dict[str, Any]:
        """导出紧凑的关系视图（按 canonical 关系聚合）。"""
        try:
            where_clauses = []
            params = []
            
            if comm_id:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM community_members cm 
                        WHERE cm.comm_id = %s AND (cm.entity_id = cr.subj_entity_id OR cm.entity_id = cr.obj_entity_id)
                    )
                """)
                params.append(comm_id)
            elif pack_id:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM evidence_pack_items epi
                        JOIN canonical_relation_evidence cre ON cre.chunk_id = epi.chunk_id
                        WHERE epi.pack_id = %s AND cre.canon_rel_id = cr.canon_rel_id
                    )
                """)
                params.append(pack_id)
                
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            sql = f"""
                SELECT 
                    cr.canon_rel_id, 
                    s.canonical_name as subj_name, 
                    cr.predicate_norm, 
                    o.canonical_name as obj_name, 
                    cr.qualifiers_norm,
                    (SELECT COUNT(*) FROM canonical_relation_evidence cre WHERE cre.canon_rel_id = cr.canon_rel_id) as evidence_count
                FROM canonical_relations cr
                JOIN entities s ON s.entity_id = cr.subj_entity_id
                JOIN entities o ON o.entity_id = cr.obj_entity_id
                {where_sql}
                ORDER BY evidence_count DESC
            """
            rows = query_all(sql, tuple(params))
            
            return ExportRelationsCompactOut(relations=rows).model_dump()
            
        except Exception as e:
            return ExportRelationsCompactOut(
                error=MCPErrorModel(code="SYSTEM_ERROR", message=str(e))
            ).model_dump()
