"""GraphRAG 规范化工具：canonicalize_entities_v1, lock_entity, merge_entities"""

import re
from typing import Any

from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one
from paperlib_mcp.models_graph import (
    EntityType,
    MCPErrorModel,
    MergeSuggestion,
    CanonicalizeEntitiesOut,
    LockEntityOut,
    MergeEntitiesOut,
)


# ============================================================
# 归一化规则
# ============================================================

# 常见缩写和同义词映射
ALIAS_MAPPINGS = {
    # 识别策略
    "difference-in-differences": "did",
    "diff-in-diff": "did",
    "diff in diff": "did",
    "difference in differences": "did",
    "regression discontinuity design": "rdd",
    "regression discontinuity": "rdd",
    "instrumental variable": "iv",
    "instrumental variables": "iv",
    "two-stage least squares": "2sls",
    "2sls": "2sls",
    "tsls": "2sls",
    "fixed effects": "fe",
    "fixed effect": "fe",
    "panel fixed effects": "panel_fe",
    "firm fixed effects": "firm_fe",
    "year fixed effects": "year_fe",
    "event study": "event_study",
    
    # 方法
    "ordinary least squares": "ols",
    "logistic regression": "logit",
    "probit regression": "probit",
    "maximum likelihood": "mle",
    "generalized method of moments": "gmm",
    
    # 常见主题缩写
    "artificial intelligence": "ai",
    "machine learning": "ml",
    "research and development": "r&d",
    "initial public offering": "ipo",
    "mergers and acquisitions": "m&a",
    "environmental social governance": "esg",
    "corporate social responsibility": "csr",
}

# 识别策略家族
ID_FAMILY_KEYWORDS = {
    "iv": ["iv", "instrument", "2sls", "tsls", "two-stage"],
    "did": ["did", "difference-in-differences", "diff-in-diff", "parallel trend"],
    "rdd": ["rdd", "regression discontinuity", "discontinuity", "cutoff", "threshold"],
    "event_study": ["event study", "event-study", "abnormal return"],
    "fe": ["fixed effect", "fe", "panel"],
    "psm": ["propensity score", "matching", "psm"],
    "synthetic_control": ["synthetic control", "synthetic"],
}


def normalize_alias(text: str) -> str:
    """归一化别名：小写、去标点、空白归一、应用映射"""
    # 转小写
    text = text.lower().strip()
    
    # 应用映射
    for old, new in ALIAS_MAPPINGS.items():
        if old in text:
            text = text.replace(old, new)
    
    # 去标点，保留字母数字和空格
    text = re.sub(r"[^\w\s]", " ", text)
    
    # 空白归一
    text = " ".join(text.split())
    
    return text


def identify_id_family(name: str) -> str:
    """识别 IdentificationStrategy 的家族"""
    name_lower = name.lower()
    
    for family, keywords in ID_FAMILY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return family
    
    return "other"


def generate_canonical_key_for_type(entity_type: EntityType, canonical_name: str) -> str:
    """根据实体类型生成规范键"""
    alias_norm = normalize_alias(canonical_name)
    
    if entity_type == EntityType.Paper:
        return canonical_name  # Paper 的 key 就是 doc_id
    elif entity_type == EntityType.Topic:
        return f"topic|{alias_norm}"
    elif entity_type == EntityType.MeasureProxy:
        # 简化处理：使用归一化名称
        return f"measure|{alias_norm}"
    elif entity_type == EntityType.IdentificationStrategy:
        id_family = identify_id_family(canonical_name)
        return f"id|{id_family}|{alias_norm}"
    elif entity_type == EntityType.Method:
        # Method 使用第一个词作为 family
        method_family = alias_norm.split()[0] if alias_norm else "other"
        return f"method|{method_family}"
    elif entity_type == EntityType.Setting:
        return f"setting|{alias_norm}"
    elif entity_type == EntityType.DataSource:
        return f"data|{alias_norm}"
    elif entity_type == EntityType.Mechanism:
        return f"mechanism|{alias_norm}"
    elif entity_type == EntityType.LimitationGap:
        return f"gap|{alias_norm}"
    else:
        return f"other|{alias_norm}"


def execute_merge(conn, winner_id: int, loser_ids: list[int], reason: str = "auto_canonicalize"):
    """执行实体合并"""
    with conn.cursor() as cur:
        # 1. Remap mentions
        cur.execute(
            "UPDATE mentions SET entity_id = %s WHERE entity_id = ANY(%s)",
            (winner_id, loser_ids)
        )
        
        # 2. Remap relations (both subj and obj)
        cur.execute(
            "UPDATE relations SET subj_entity_id = %s WHERE subj_entity_id = ANY(%s)",
            (winner_id, loser_ids)
        )
        cur.execute(
            "UPDATE relations SET obj_entity_id = %s WHERE obj_entity_id = ANY(%s)",
            (winner_id, loser_ids)
        )
        
        # 3. Remap aliases
        cur.execute(
            "UPDATE entity_aliases SET entity_id = %s WHERE entity_id = ANY(%s)",
            (winner_id, loser_ids)
        )
        
        # 4. 记录合并日志
        for loser_id in loser_ids:
            cur.execute(
                """
                INSERT INTO entity_merge_log(from_entity_id, to_entity_id, reason)
                VALUES (%s, %s, %s)
                """,
                (loser_id, winner_id, reason)
            )
        
        # 5. 删除被合并的实体
        cur.execute(
            "DELETE FROM entities WHERE entity_id = ANY(%s)",
            (loser_ids,)
        )


# ============================================================
# 工具注册
# ============================================================


def register_graph_canonicalize_tools(mcp: FastMCP) -> None:
    """注册 GraphRAG 规范化工具"""

    @mcp.tool()
    def canonicalize_entities_v1(
        types: list[str] | None = None,
        suggest_only: bool = False,
        max_groups: int = 5000,
    ) -> dict[str, Any]:
        """规范化并合并重复实体
        
        对指定类型的实体进行规范化处理，合并同一 canonical_key 的重复实体。
        
        Args:
            types: 要处理的实体类型列表，默认 ["Topic", "MeasureProxy", "IdentificationStrategy", "Method"]
            suggest_only: 是否只返回建议而不执行合并，默认 False
            max_groups: 最大处理组数，默认 5000
            
        Returns:
            合并统计信息和建议列表
        """
        try:
            # 默认处理的类型
            if types is None:
                types = ["Topic", "MeasureProxy", "IdentificationStrategy", "Method"]
            
            # 验证类型
            valid_types = []
            for t in types:
                try:
                    valid_types.append(EntityType(t))
                except ValueError:
                    pass
            
            if not valid_types:
                return CanonicalizeEntitiesOut(
                    executed=False,
                    merged_groups=0,
                    merged_entities=0,
                    error=MCPErrorModel(code="VALIDATION_ERROR", message="No valid entity types provided"),
                ).model_dump()
            
            type_values = [t.value for t in valid_types]
            
            suggestions: list[MergeSuggestion] = []
            merged_groups = 0
            merged_entities = 0
            
            with get_db() as conn:
                # 1. 首先更新所有实体的 canonical_key（基于新的规范化规则）
                entities = query_all(
                    """
                    SELECT entity_id, type, canonical_name, canonical_key, confidence, is_locked
                    FROM entities
                    WHERE type = ANY(%s) AND is_locked IS NOT TRUE
                    ORDER BY entity_id
                    """,
                    (type_values,)
                )
                
                # 计算新的 canonical_key
                entity_new_keys: dict[int, str] = {}
                for entity in entities:
                    entity_type = EntityType(entity["type"])
                    new_key = generate_canonical_key_for_type(entity_type, entity["canonical_name"])
                    if new_key != entity["canonical_key"]:
                        entity_new_keys[entity["entity_id"]] = new_key
                
                # 更新 canonical_key（跳过会导致冲突的实体）
                skipped_conflicts = 0
                if not suggest_only and entity_new_keys:
                    with conn.cursor() as cur:
                        for entity_id, new_key in entity_new_keys.items():
                            # 使用条件更新来避免唯一约束冲突
                            # 只有当新 key 不会与其他实体冲突时才更新
                            cur.execute(
                                """
                                UPDATE entities SET canonical_key = %s, updated_at = now()
                                WHERE entity_id = %s
                                AND NOT EXISTS (
                                    SELECT 1 FROM entities e2
                                    WHERE e2.type = (SELECT type FROM entities WHERE entity_id = %s)
                                    AND e2.canonical_key = %s
                                    AND e2.entity_id != %s
                                )
                                """,
                                (new_key, entity_id, entity_id, new_key, entity_id)
                            )
                            if cur.rowcount == 0:
                                skipped_conflicts += 1
                
                # 2. 找出重复组
                duplicate_groups = query_all(
                    """
                    SELECT type, canonical_key, 
                           array_agg(entity_id ORDER BY confidence DESC, entity_id ASC) AS ids,
                           array_agg(canonical_name ORDER BY confidence DESC, entity_id ASC) AS names,
                           array_agg(confidence ORDER BY confidence DESC, entity_id ASC) AS confidences
                    FROM entities
                    WHERE type = ANY(%s) AND is_locked IS NOT TRUE
                    GROUP BY type, canonical_key
                    HAVING COUNT(*) > 1
                    ORDER BY COUNT(*) DESC
                    LIMIT %s
                    """,
                    (type_values, max_groups)
                )
                
                # 3. 处理每个重复组
                for group in duplicate_groups:
                    entity_type = EntityType(group["type"])
                    canonical_key = group["canonical_key"]
                    ids = group["ids"]
                    
                    if len(ids) < 2:
                        continue
                    
                    winner_id = ids[0]  # confidence 最高的
                    loser_ids = ids[1:]
                    
                    suggestion = MergeSuggestion(
                        type=entity_type,
                        canonical_key=canonical_key,
                        winner_entity_id=winner_id,
                        merged_entity_ids=loser_ids,
                    )
                    suggestions.append(suggestion)
                    
                    if not suggest_only:
                        execute_merge(conn, winner_id, loser_ids, "auto_canonicalize")
                        merged_groups += 1
                        merged_entities += len(loser_ids)
            
            return CanonicalizeEntitiesOut(
                executed=not suggest_only,
                merged_groups=merged_groups,
                merged_entities=merged_entities,
                suggestions=suggestions,
            ).model_dump()
            
        except Exception as e:
            return CanonicalizeEntitiesOut(
                executed=False,
                merged_groups=0,
                merged_entities=0,
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

    @mcp.tool()
    def lock_entity(entity_id: int, is_locked: bool = True) -> dict[str, Any]:
        """锁定或解锁实体
        
        锁定的实体不会被自动规范化合并。
        
        Args:
            entity_id: 实体 ID
            is_locked: 是否锁定，默认 True
            
        Returns:
            操作结果
        """
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE entities SET is_locked = %s, updated_at = now()
                        WHERE entity_id = %s
                        RETURNING entity_id
                        """,
                        (is_locked, entity_id)
                    )
                    result = cur.fetchone()
                    
                    if not result:
                        return LockEntityOut(
                            ok=False,
                            error=MCPErrorModel(code="NOT_FOUND", message=f"Entity {entity_id} not found"),
                        ).model_dump()
            
            return LockEntityOut(ok=True).model_dump()
            
        except Exception as e:
            return LockEntityOut(
                ok=False,
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

    @mcp.tool()
    def merge_entities(from_entity_id: int, to_entity_id: int, reason: str) -> dict[str, Any]:
        """手动合并两个实体
        
        将 from_entity 的所有引用迁移到 to_entity，然后删除 from_entity。
        
        Args:
            from_entity_id: 要被合并的实体 ID
            to_entity_id: 目标实体 ID
            reason: 合并原因
            
        Returns:
            操作结果
        """
        try:
            # 验证两个实体都存在
            from_entity = query_one(
                "SELECT entity_id, type FROM entities WHERE entity_id = %s",
                (from_entity_id,)
            )
            to_entity = query_one(
                "SELECT entity_id, type FROM entities WHERE entity_id = %s",
                (to_entity_id,)
            )
            
            if not from_entity:
                return MergeEntitiesOut(
                    ok=False,
                    error=MCPErrorModel(code="NOT_FOUND", message=f"From entity {from_entity_id} not found"),
                ).model_dump()
            
            if not to_entity:
                return MergeEntitiesOut(
                    ok=False,
                    error=MCPErrorModel(code="NOT_FOUND", message=f"To entity {to_entity_id} not found"),
                ).model_dump()
            
            # 类型检查（可选：只允许同类型合并）
            if from_entity["type"] != to_entity["type"]:
                return MergeEntitiesOut(
                    ok=False,
                    error=MCPErrorModel(
                        code="VALIDATION_ERROR",
                        message=f"Cannot merge different types: {from_entity['type']} -> {to_entity['type']}"
                    ),
                ).model_dump()
            
            with get_db() as conn:
                execute_merge(conn, to_entity_id, [from_entity_id], reason)
            
            return MergeEntitiesOut(ok=True).model_dump()
            
        except Exception as e:
            return MergeEntitiesOut(
                ok=False,
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

