"""GraphRAG v1.2 工具：词表管理、Claim Features、分组增强"""

import json
from collections import defaultdict
from typing import Any, Literal

from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one
from paperlib_mcp.models_graph import MCPErrorModel
from paperlib_mcp import config


# ============================================================
# 常量与规则版本
# ============================================================

V1_2_PARAMS = {
    "version": "1.2",
    "normalization": {
        "text_norm": "lower+punct+ws",
        "json_dumps": "sort_keys=True,separators=(',',':')",
        "sep": "\\u001f"
    },
    "grouping_fields": ["primary_topic_key", "outcome_family", "treatment_family", "sign", "id_family", "setting_bin"],
}


def normalize_text(text: str) -> str:
    """规范化文本：lower + 去标点 + 空格归一"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def register_graph_v12_tools(mcp: FastMCP) -> None:
    """注册 v1.2 GraphRAG 工具"""

    # ============================================================
    # Taxonomy 工具
    # ============================================================

    @mcp.tool()
    def taxonomy_list_terms(
        kind: str | None = None,
        enabled_only: bool = True,
    ) -> dict[str, Any]:
        """列出词表规则"""
        try:
            where = []
            params = []
            if kind:
                where.append("kind = %s")
                params.append(kind)
            if enabled_only:
                where.append("enabled = TRUE")
            where_sql = " WHERE " + " AND ".join(where) if where else ""
            
            rows = query_all(f"""
                SELECT term_id, kind, family, pattern, priority, enabled, notes
                FROM taxonomy_terms
                {where_sql}
                ORDER BY kind, priority ASC, family
            """, tuple(params))
            return {"terms": rows}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def taxonomy_upsert_term(
        kind: str,
        family: str,
        pattern: str,
        priority: int = 100,
        enabled: bool = True,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """添加或更新词表规则"""
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO taxonomy_terms (kind, family, pattern, priority, enabled, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        RETURNING term_id
                    """, (kind, family, pattern, priority, enabled, notes))
                    result = cur.fetchone()
                    term_id = result["term_id"] if result else None
            return {"term_id": term_id, "created": term_id is not None}
        except Exception as e:
            return {"error": str(e)}

    # ============================================================
    # Topic DF 缓存
    # ============================================================

    @mcp.tool()
    def compute_topic_df_cache() -> dict[str, Any]:
        """计算 Topic 实体的文档频率缓存"""
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    # 计算每个 Topic 出现在多少篇 Paper 中
                    cur.execute("""
                        INSERT INTO entity_stats (entity_id, doc_frequency)
                        SELECT x.entity_id, COUNT(DISTINCT p.entity_id)
                        FROM relations r
                        JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                        JOIN entities x ON x.entity_id = r.obj_entity_id AND x.type = 'Topic'
                        WHERE r.predicate = 'PAPER_HAS_TOPIC'
                        GROUP BY x.entity_id
                        ON CONFLICT (entity_id) DO UPDATE SET 
                            doc_frequency = EXCLUDED.doc_frequency,
                            updated_at = now()
                    """)
                    cur.execute("SELECT COUNT(*) as n FROM entity_stats WHERE doc_frequency > 0")
                    count = cur.fetchone()["n"]
            return {"topics_cached": count}
        except Exception as e:
            return {"error": str(e)}

    # ============================================================
    # Claim Features 分配
    # ============================================================

    @mcp.tool()
    def assign_claim_features_v1_2(
        scope: str = "all",
    ) -> dict[str, Any]:
        """为 claims 分配预计算特征（primary_topic, outcome/treatment family 等）"""
        try:
            # 1. 获取 taxonomy 规则
            outcome_rules = query_all("""
                SELECT family, pattern FROM taxonomy_terms 
                WHERE kind = 'outcome' AND enabled = TRUE 
                ORDER BY priority ASC
            """)
            treatment_rules = query_all("""
                SELECT family, pattern FROM taxonomy_terms 
                WHERE kind = 'treatment' AND enabled = TRUE 
                ORDER BY priority ASC
            """)

            def match_family(text: str, rules: list) -> str:
                text_norm = normalize_text(text)
                for rule in rules:
                    if rule["pattern"].lower() in text_norm:
                        return rule["family"]
                return "general"

            # 2. 获取 claims
            claims = query_all("SELECT claim_id, doc_id, claim_text, sign, conditions FROM claims")
            
            # 3. 获取每个 doc 的 primary topic (按 df 最小选择)
            doc_topics = query_all("""
                SELECT 
                    p.canonical_key as doc_id,
                    t.entity_id as topic_entity_id,
                    t.canonical_key as topic_key,
                    COALESCE(es.doc_frequency, 1000000) as df
                FROM relations r
                JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                JOIN entities t ON t.entity_id = r.obj_entity_id AND t.type = 'Topic'
                LEFT JOIN entity_stats es ON es.entity_id = t.entity_id
                WHERE r.predicate = 'PAPER_HAS_TOPIC'
                ORDER BY p.canonical_key, df ASC, t.entity_id ASC
            """)
            
            # 每个 doc 取 df 最小的 topic
            doc_primary_topic: dict[str, tuple] = {}
            for row in doc_topics:
                if row["doc_id"] not in doc_primary_topic:
                    doc_primary_topic[row["doc_id"]] = (row["topic_entity_id"], row["topic_key"])

            # 4. 获取每个 doc 的 id_family (从 PAPER_IDENTIFIES_WITH)
            doc_id_family = {}
            id_rels = query_all("""
                SELECT p.canonical_key as doc_id, e.canonical_key as id_key
                FROM relations r
                JOIN entities p ON p.entity_id = r.subj_entity_id AND p.type = 'Paper'
                JOIN entities e ON e.entity_id = r.obj_entity_id
                WHERE r.predicate = 'PAPER_IDENTIFIES_WITH'
            """)
            for row in id_rels:
                if row["doc_id"] not in doc_id_family:
                    doc_id_family[row["doc_id"]] = row["id_key"]

            # 5. 写入 claim_features
            params_json = json.dumps(V1_2_PARAMS, sort_keys=True)
            inserted = 0
            
            with get_db() as conn:
                for c in claims:
                    topic_info = doc_primary_topic.get(c["doc_id"], (None, "unknown_topic"))
                    outcome_fam = match_family(c["claim_text"], outcome_rules)
                    treatment_fam = match_family(c["claim_text"], treatment_rules)
                    id_fam = doc_id_family.get(c["doc_id"], "general")
                    
                    try:
                        with conn.cursor() as cur:
                            with conn.transaction():
                                cur.execute("""
                                    INSERT INTO claim_features 
                                    (claim_id, doc_id, primary_topic_entity_id, primary_topic_key,
                                     outcome_family, treatment_family, setting_bin, id_family, sign, params_json)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                                    ON CONFLICT (claim_id) DO UPDATE SET
                                        primary_topic_entity_id = EXCLUDED.primary_topic_entity_id,
                                        primary_topic_key = EXCLUDED.primary_topic_key,
                                        outcome_family = EXCLUDED.outcome_family,
                                        treatment_family = EXCLUDED.treatment_family,
                                        id_family = EXCLUDED.id_family,
                                        sign = EXCLUDED.sign,
                                        params_json = EXCLUDED.params_json,
                                        updated_at = now()
                                """, (
                                    c["claim_id"], c["doc_id"], 
                                    topic_info[0], topic_info[1],
                                    outcome_fam, treatment_fam, "general", id_fam,
                                    c["sign"], params_json
                                ))
                                inserted += 1
                    except Exception as e:
                        print(f"Error processing claim {c['claim_id']}: {e}")

            return {"claims_processed": inserted}
        except Exception as e:
            return {"error": str(e)}

    # ============================================================
    # v1.2 Grouping
    # ============================================================

    @mcp.tool()
    def build_claim_groups_v1_2(
        scope: str = "all",
    ) -> dict[str, Any]:
        """基于 claim_features 构建 v1.2 claim groups"""
        try:
            # 从 claim_features 读取，按 group_key 分组
            features = query_all("""
                SELECT claim_id, primary_topic_key, outcome_family, treatment_family, 
                       sign, id_family, setting_bin
                FROM claim_features
            """)
            
            if not features:
                return {"error": "No claim features found. Run assign_claim_features_v1_2 first."}

            groups: dict[str, list[int]] = defaultdict(list)
            group_meta: dict[str, dict] = {}
            
            for f in features:
                # v1.2 group_key 使用预计算的 features
                group_key = "|".join([
                    f["primary_topic_key"] or "unknown",
                    f["outcome_family"],
                    f["treatment_family"],
                    f["sign"] or "null",
                    f["id_family"] or "general",
                    f["setting_bin"],
                ])
                groups[group_key].append(f["claim_id"])
                
                if group_key not in group_meta:
                    # 查找 topic entity id
                    topic_ent = query_one(
                        "SELECT entity_id FROM entities WHERE canonical_key = %s",
                        (f["primary_topic_key"],)
                    )
                    group_meta[group_key] = {
                        "topic_entity_id": topic_ent["entity_id"] if topic_ent else None,
                        "sign": f["sign"],
                        "setting": f["setting_bin"],
                        "id_family": f["id_family"],
                    }

            # 写入 claim_groups (清空旧组后重建)
            params_json = json.dumps(V1_2_PARAMS, sort_keys=True)
            total_members = 0
            
            with get_db() as conn:
                with conn.cursor() as cur:
                    # 清空旧的 v1 组
                    cur.execute("DELETE FROM claim_group_members")
                    cur.execute("DELETE FROM claim_groups")
                
                for key, claim_ids in groups.items():
                    meta = group_meta[key]
                    try:
                        with conn.cursor() as cur:
                            with conn.transaction():
                                cur.execute("""
                                    INSERT INTO claim_groups 
                                    (group_key, topic_entity_id, sign, setting, id_family, params_json)
                                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                                    RETURNING group_id
                                """, (key, meta["topic_entity_id"], meta["sign"], 
                                      meta["setting"], meta["id_family"], params_json))
                                group_id = cur.fetchone()["group_id"]
                                
                                for cid in claim_ids:
                                    cur.execute("""
                                        INSERT INTO claim_group_members (group_id, claim_id)
                                        VALUES (%s, %s)
                                    """, (group_id, cid))
                                    total_members += 1
                    except Exception as e:
                        print(f"Error creating group {key}: {e}")

                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) as n FROM claim_groups")
                    group_count = cur.fetchone()["n"]

            return {"groups_created": group_count, "total_members": total_members}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def split_large_claim_groups_v1_2(
        split_threshold: int | None = None,
        target_size: int | None = None,
    ) -> dict[str, Any]:
        """拆分超大 claim groups (使用 TF-IDF + KMeans)"""
        try:
            # 使用配置默认值
            if split_threshold is None:
                split_threshold = config.claim_split_threshold()
            if target_size is None:
                target_size = config.claim_target_size()
            
            # 找出需要拆分的大组
            large_groups = query_all("""
                SELECT g.group_id, g.group_key, COUNT(*) as n
                FROM claim_groups g
                JOIN claim_group_members m ON m.group_id = g.group_id
                WHERE g.parent_group_id IS NULL
                GROUP BY g.group_id, g.group_key
                HAVING COUNT(*) > %s
            """, (split_threshold,))
            
            if not large_groups:
                return {"message": "No groups exceed threshold", "split_count": 0}

            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            import numpy as np

            split_count = 0
            
            for lg in large_groups:
                # 获取该组的 claims
                claims = query_all("""
                    SELECT c.claim_id, c.claim_text
                    FROM claim_group_members m
                    JOIN claims c ON c.claim_id = m.claim_id
                    WHERE m.group_id = %s
                    ORDER BY c.claim_id
                """, (lg["group_id"],))
                
                if len(claims) < 2:
                    continue
                
                # TF-IDF 向量化
                texts = [normalize_text(c["claim_text"]) for c in claims]
                vectorizer = TfidfVectorizer(max_features=500, min_df=2, max_df=0.9)
                try:
                    tfidf_matrix = vectorizer.fit_transform(texts)
                except ValueError:
                    continue  # 文本太少或太相似
                
                # KMeans 聚类
                k = max(2, int(np.ceil(len(claims) / target_size)))
                kmeans = KMeans(n_clusters=k, random_state=0, n_init=10)
                labels = kmeans.fit_predict(tfidf_matrix)
                
                # 为每个 cluster 创建子组
                with get_db() as conn:
                    for cluster_id in range(k):
                        cluster_claims = [claims[i]["claim_id"] for i, l in enumerate(labels) if l == cluster_id]
                        if not cluster_claims:
                            continue
                        
                        # 子组 key
                        subgroup_key = f"kmeans|cluster_{cluster_id}"
                        
                        with conn.cursor() as cur:
                            with conn.transaction():
                                cur.execute("""
                                    INSERT INTO claim_groups 
                                    (group_key, parent_group_id, subgroup_key, topic_entity_id, sign, setting, id_family, params_json)
                                    SELECT 
                                        group_key || '|' || %s,
                                        group_id,
                                        %s,
                                        topic_entity_id, sign, setting, id_family, params_json
                                    FROM claim_groups WHERE group_id = %s
                                    RETURNING group_id
                                """, (subgroup_key, subgroup_key, lg["group_id"]))
                                subgroup_id = cur.fetchone()["group_id"]
                                
                                # 迁移成员到子组
                                for cid in cluster_claims:
                                    cur.execute("""
                                        UPDATE claim_group_members SET group_id = %s
                                        WHERE claim_id = %s AND group_id = %s
                                    """, (subgroup_id, cid, lg["group_id"]))
                        
                        split_count += 1

            return {"split_count": split_count, "large_groups_processed": len(large_groups)}
        except ImportError:
            return {"error": "scikit-learn not installed. Run: pip install scikit-learn"}
        except Exception as e:
            return {"error": str(e)}

    # ============================================================
    # v1.2 Export 工具
    # ============================================================

    @mcp.tool()
    def export_claim_matrix_grouped_v1_2(
        comm_id: int | None = None,
        pack_id: int | None = None,
        top_k_per_group: int = 10,
        include_subgroups: bool = True,
    ) -> dict[str, Any]:
        """导出分组 claim 矩阵，每组返回 top-k 代表 claims (按 confidence 排序，sign 分层)"""
        try:
            # 构建过滤条件
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
            
            # 是否包含子组
            if not include_subgroups:
                where_clauses.append("g.parent_group_id IS NULL")
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # 获取分组
            groups = query_all(f"""
                SELECT 
                    g.group_id, g.group_key, g.parent_group_id, g.subgroup_key,
                    g.sign, g.id_family, g.setting,
                    e.canonical_name as topic_name,
                    (SELECT COUNT(*) FROM claim_group_members cgm WHERE cgm.group_id = g.group_id) as member_count
                FROM claim_groups g
                LEFT JOIN entities e ON e.entity_id = g.topic_entity_id
                {where_sql}
                ORDER BY member_count DESC
            """, tuple(params))
            
            # 为每个 group 获取 top-k claims（按 sign 分层 + confidence 排序）
            result_groups = []
            for g in groups:
                # 获取该组的 claims，按 sign 和 confidence 排序
                claims = query_all("""
                    SELECT c.claim_id, c.doc_id, c.claim_text, c.sign, c.confidence,
                           cf.outcome_family, cf.treatment_family
                    FROM claim_group_members cgm
                    JOIN claims c ON c.claim_id = cgm.claim_id
                    LEFT JOIN claim_features cf ON cf.claim_id = c.claim_id
                    WHERE cgm.group_id = %s
                    ORDER BY 
                        CASE c.sign 
                            WHEN 'positive' THEN 1 
                            WHEN 'negative' THEN 2 
                            WHEN 'mixed' THEN 3 
                            ELSE 4 
                        END,
                        c.confidence DESC
                    LIMIT %s
                """, (g["group_id"], top_k_per_group))
                
                result_groups.append({
                    "group_id": g["group_id"],
                    "group_key": g["group_key"],
                    "parent_group_id": g["parent_group_id"],
                    "subgroup_key": g["subgroup_key"],
                    "topic_name": g["topic_name"],
                    "sign": g["sign"],
                    "member_count": g["member_count"],
                    "top_claims": claims,
                })
            
            return {
                "total_groups": len(result_groups),
                "groups": result_groups
            }
        except Exception as e:
            return {"error": str(e)}
