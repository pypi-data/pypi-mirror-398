"""GraphRAG 抽取工具：graph_health_check, select_high_value_chunks, extract_graph_v1"""

import hashlib
import json
import re
import asyncio
from typing import Any

import httpx
from fastmcp import FastMCP

from paperlib_mcp.db import get_db, query_all, query_one, execute_returning
from paperlib_mcp.settings import get_settings
from paperlib_mcp.models_graph import (
    EntityType,
    Predicate,
    ClaimSign,
    MCPErrorModel,
    GraphHealthCheckOut,
    HighValueChunk,
    SelectHighValueChunksOut,
    ExtractGraphStats,
    ExtractGraphOut,
    ChunkExtractionResult,
    ExtractedEntity,
    ExtractedMention,
    ExtractedRelation,
    ExtractedClaim,
)


# ============================================================
# 常量
# ============================================================

# 高价值 chunk 筛选关键词
HIGH_VALUE_KEYWORDS_DEFAULT = [
    "identification", "strategy", "instrument", "did", "difference-in-differences",
    "event study", "rdd", "regression discontinuity", "robustness", "placebo",
    "measurement", "proxy", "data", "we measure", "limitation", "threat", "caveat",
    "mechanism", "channel", "heterogeneous", "heterogeneity", "endogeneity",
    "instrumental variable", "iv", "fixed effect", "panel", "causal",
]

HIGH_VALUE_KEYWORDS_STRICT = [
    "identification strategy", "instrumental variable", "difference-in-differences",
    "regression discontinuity", "event study", "placebo test", "robustness check",
    "measurement error", "proxy variable", "causal effect", "endogeneity",
]

# M2 必需的表
REQUIRED_TABLES = [
    "entities", "entity_aliases", "mentions", "relations", "claims",
    "communities", "community_members", "community_summaries", "entity_merge_log",
]

# M2 必需的索引（检查存在性即可）
REQUIRED_INDEXES = [
    "entities_type_idx", "entities_canonical_key_idx",
    "mentions_entity_idx", "mentions_doc_idx", "mentions_chunk_idx",
    "relations_subj_idx", "relations_obj_idx", "relations_predicate_idx",
    "claims_doc_idx", "claims_sign_idx",
    "community_members_comm_idx", "community_members_entity_idx",
]


# ============================================================
# LLM 抽取 Prompt
# ============================================================

EXTRACTION_SYSTEM_PROMPT = """You are an expert academic research analyst specializing in economics and finance literature. 
Your task is to extract structured information from research paper excerpts.

You MUST output valid JSON following the exact schema provided. Do not include any text outside the JSON.
Every entity, relation, and claim MUST have an evidence quote from the original text."""

EXTRACTION_USER_PROMPT_TEMPLATE = """Analyze this excerpt from an academic paper and extract structured information.

## Text to analyze:
{chunk_text}

## Required JSON Schema:
{{
  "entities": [
    {{
      "temp_id": "e1",
      "type": "Topic|MeasureProxy|IdentificationStrategy|Method|Setting|DataSource|Mechanism|LimitationGap",
      "name": "specific entity name",
      "confidence": 0.8
    }}
  ],
  "mentions": [
    {{
      "entity_temp_id": "e1",
      "quote": "short identifiable substring",
      "confidence": 0.8
    }}
  ],
  "relations": [
    {{
      "subject_temp_id": "paper",
      "predicate": "PAPER_HAS_TOPIC|PAPER_USES_MEASURE|PAPER_IDENTIFIES_WITH|PAPER_USES_METHOD|PAPER_IN_SETTING|PAPER_USES_DATA|PAPER_PROPOSES_MECHANISM|PAPER_NOTES_LIMITATION",
      "object_temp_id": "e1",
      "evidence_quote": "short identifiable substring",
      "confidence": 0.8
    }}
  ],
  "claims": [
    {{
      "claim_text": "concise finding",
      "sign": "positive|negative|mixed|null",
      "confidence": 0.8,
      "evidence_quote": "short identifiable substring"
    }}
  ]
}}

## Guidelines:
1. **SELECTIVITY IS KEY**: Extract ONLY the most significant/novel entities (max 10 entities per chunk). Ignore generic terms (e.g., "data", "model", "results", "analysis").
2. **EVIDENCE QUOTES**:
   - For mentions and relations: Keep 'quote'/'evidence_quote' minimal (max 15 words) - just enough to locate the reference.
   - For claims: Use longer 'evidence_quote' (30-50 words) to capture the full finding with context, making it directly citable in literature reviews.
3. **IdentificationStrategy**: focus on specific methods (e.g., "IV with tariff shock", "DID staggered").
4. **MeasureProxy**: focus on specific variable constructions (e.g., "AI adoption via job postings").
5. **Claims**: Extract only the top 1-3 central empirical findings.
6. **Relations**: Do not create redundant relations if the entity itself implies the connection.
7. Output ONLY valid JSON.

"""


# ============================================================
# 辅助函数
# ============================================================


def normalize_alias(text: str) -> str:
    """归一化别名：小写、去标点、空白归一"""
    # 转小写
    text = text.lower()
    # 替换常见缩写
    replacements = {
        "difference-in-differences": "did",
        "diff-in-diff": "did",
        "regression discontinuity design": "rdd",
        "instrumental variable": "iv",
        "instrumental variables": "iv",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # 去标点，保留字母数字和空格
    text = re.sub(r"[^\w\s]", " ", text)
    # 空白归一
    text = " ".join(text.split())
    return text


def generate_canonical_key(entity_type: EntityType, name: str, normalized: dict | None = None) -> str:
    """生成 canonical_key"""
    alias_norm = normalize_alias(name)
    
    if entity_type == EntityType.Paper:
        # Paper 的 canonical_key 就是 doc_id
        return name
    elif entity_type == EntityType.Topic:
        return f"topic|{alias_norm}"
    elif entity_type == EntityType.MeasureProxy:
        proxy_family = normalized.get("proxy_family", "general") if normalized else "general"
        return f"measure|{proxy_family}|{alias_norm}"
    elif entity_type == EntityType.IdentificationStrategy:
        # 识别 ID family
        id_family = "other"
        name_lower = name.lower()
        if any(k in name_lower for k in ["iv", "instrument"]):
            id_family = "iv"
        elif any(k in name_lower for k in ["did", "difference"]):
            id_family = "did"
        elif any(k in name_lower for k in ["rdd", "discontinuity"]):
            id_family = "rdd"
        elif "event study" in name_lower:
            id_family = "event_study"
        elif any(k in name_lower for k in ["fixed effect", "fe"]):
            id_family = "fe"
        return f"id|{id_family}|{alias_norm}"
    elif entity_type == EntityType.Method:
        # Method 使用强枚举
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


def compute_relation_hash(subj_id: int, predicate: str, obj_id: int, quote: str) -> str:
    """计算关系哈希，用于去重"""
    content = f"{subj_id}|{predicate}|{obj_id}|{quote[:100]}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def compute_claim_hash(doc_id: str, chunk_id: int, claim_text: str) -> str:
    """计算 claim 哈希，用于去重"""
    content = f"{doc_id}|{chunk_id}|{claim_text[:200]}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]



async def acall_llm_extract(chunk_text: str, llm_model: str) -> ChunkExtractionResult | None:
    """调用 LLM 进行抽取 (Async)"""
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
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": EXTRACTION_USER_PROMPT_TEMPLATE.format(chunk_text=chunk_text)},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        # OpenRouter 格式：禁用推理模型的 reasoning tokens（如 GPT-5 Nano）
        # 使用 effort: low 最小化推理，exclude: true 不返回推理内容
        "reasoning": {
            "effort": "low",
            "exclude": True,
        },
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # 解析 JSON
        result_dict = json.loads(content)
        
        # 转换为 Pydantic 模型
        entities = []
        for e in result_dict.get("entities", []):
            try:
                entity_type = EntityType(e.get("type", "Topic"))
                entities.append(ExtractedEntity(
                    temp_id=e.get("temp_id", ""),
                    type=entity_type,
                    name=e.get("name", ""),
                    normalized=e.get("normalized"),
                    confidence=float(e.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        mentions = []
        for m in result_dict.get("mentions", []):
            try:
                mentions.append(ExtractedMention(
                    entity_temp_id=m.get("entity_temp_id", ""),
                    quote=m.get("quote", ""),
                    span_start=m.get("span_start"),
                    span_end=m.get("span_end"),
                    confidence=float(m.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        relations = []
        for r in result_dict.get("relations", []):
            try:
                predicate = Predicate(r.get("predicate", "PAPER_HAS_TOPIC"))
                relations.append(ExtractedRelation(
                    subject_temp_id=r.get("subject_temp_id", "paper"),
                    predicate=predicate,
                    object_temp_id=r.get("object_temp_id", ""),
                    qualifiers=r.get("qualifiers"),
                    evidence_quote=r.get("evidence_quote", ""),
                    confidence=float(r.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        claims = []
        for c in result_dict.get("claims", []):
            try:
                sign = None
                if c.get("sign"):
                    try:
                        sign = ClaimSign(c["sign"])
                    except ValueError:
                        pass
                claims.append(ExtractedClaim(
                    claim_text=c.get("claim_text", ""),
                    sign=sign,
                    effect_size_text=c.get("effect_size_text"),
                    conditions=c.get("conditions"),
                    evidence_quote=c.get("evidence_quote", ""),
                    confidence=float(c.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        return ChunkExtractionResult(
            entities=entities,
            mentions=mentions,
            relations=relations,
            claims=claims,
        )
    
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return None


def call_llm_extract(chunk_text: str, llm_model: str) -> ChunkExtractionResult | None:
    """调用 LLM 进行抽取"""
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
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": EXTRACTION_USER_PROMPT_TEMPLATE.format(chunk_text=chunk_text)},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        # OpenRouter 格式：禁用推理模型的 reasoning tokens（如 GPT-5 Nano）
        # 使用 effort: low 最小化推理，exclude: true 不返回推理内容
        "reasoning": {
            "effort": "low",
            "exclude": True,
        },
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # 解析 JSON
        result_dict = json.loads(content)
        
        # 转换为 Pydantic 模型
        entities = []
        for e in result_dict.get("entities", []):
            try:
                entity_type = EntityType(e.get("type", "Topic"))
                entities.append(ExtractedEntity(
                    temp_id=e.get("temp_id", ""),
                    type=entity_type,
                    name=e.get("name", ""),
                    normalized=e.get("normalized"),
                    confidence=float(e.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        mentions = []
        for m in result_dict.get("mentions", []):
            try:
                mentions.append(ExtractedMention(
                    entity_temp_id=m.get("entity_temp_id", ""),
                    quote=m.get("quote", ""),
                    span_start=m.get("span_start"),
                    span_end=m.get("span_end"),
                    confidence=float(m.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        relations = []
        for r in result_dict.get("relations", []):
            try:
                predicate = Predicate(r.get("predicate", "PAPER_HAS_TOPIC"))
                relations.append(ExtractedRelation(
                    subject_temp_id=r.get("subject_temp_id", "paper"),
                    predicate=predicate,
                    object_temp_id=r.get("object_temp_id", ""),
                    qualifiers=r.get("qualifiers"),
                    evidence_quote=r.get("evidence_quote", ""),
                    confidence=float(r.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        claims = []
        for c in result_dict.get("claims", []):
            try:
                sign = None
                if c.get("sign"):
                    try:
                        sign = ClaimSign(c["sign"])
                    except ValueError:
                        pass
                claims.append(ExtractedClaim(
                    claim_text=c.get("claim_text", ""),
                    sign=sign,
                    effect_size_text=c.get("effect_size_text"),
                    conditions=c.get("conditions"),
                    evidence_quote=c.get("evidence_quote", ""),
                    confidence=float(c.get("confidence", 0.8)),
                ))
            except (ValueError, KeyError):
                continue
        
        return ChunkExtractionResult(
            entities=entities,
            mentions=mentions,
            relations=relations,
            claims=claims,
        )
    
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return None


def upsert_entity(
    conn,
    entity_type: EntityType,
    canonical_name: str,
    canonical_key: str,
    normalized: dict | None,
    confidence: float,
) -> int:
    """Upsert 实体，返回 entity_id"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO entities(type, canonical_name, canonical_key, normalized, confidence, is_locked)
            VALUES (%s, %s, %s, %s::jsonb, %s, false)
            ON CONFLICT (type, canonical_key) DO UPDATE
            SET canonical_name = EXCLUDED.canonical_name,
                normalized = COALESCE(entities.normalized, '{}'::jsonb) || COALESCE(EXCLUDED.normalized, '{}'::jsonb),
                confidence = GREATEST(entities.confidence, EXCLUDED.confidence),
                updated_at = now()
            RETURNING entity_id
            """,
            (entity_type.value, canonical_name, canonical_key, json.dumps(normalized or {}), confidence)
        )
        result = cur.fetchone()
        return result["entity_id"]


def insert_alias(conn, entity_id: int, alias: str, alias_norm: str, alias_type: str = "extracted"):
    """插入别名（忽略冲突）"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO entity_aliases(entity_id, alias, alias_norm, alias_type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (entity_id, alias, alias_norm, alias_type)
        )


def insert_mention(
    conn,
    entity_id: int,
    doc_id: str,
    chunk_id: int,
    page_start: int | None,
    page_end: int | None,
    quote: str,
    confidence: float,
):
    """插入 mention"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO mentions(entity_id, doc_id, chunk_id, page_start, page_end, quote, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (entity_id, doc_id, chunk_id, page_start, page_end, quote, confidence)
        )


def insert_relation(
    conn,
    subj_entity_id: int,
    predicate: str,
    obj_entity_id: int,
    qualifiers: dict | None,
    confidence: float,
    evidence: dict,
    relation_hash: str,
) -> bool:
    """插入关系（返回是否成功插入）"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO relations(subj_entity_id, predicate, obj_entity_id, qualifiers, confidence, evidence, relation_hash)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s::jsonb, %s)
            ON CONFLICT (relation_hash) DO NOTHING
            RETURNING rel_id
            """,
            (subj_entity_id, predicate, obj_entity_id, json.dumps(qualifiers or {}), confidence, json.dumps(evidence), relation_hash)
        )
        result = cur.fetchone()
        return result is not None


def insert_claim(
    conn,
    doc_id: str,
    chunk_id: int,
    claim_text: str,
    sign: str | None,
    effect_size_text: str | None,
    conditions: dict | None,
    confidence: float,
    evidence: dict,
    claim_hash: str,
) -> bool:
    """插入 claim（返回是否成功插入）"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO claims(doc_id, chunk_id, claim_text, sign, effect_size_text, conditions, confidence, evidence, claim_hash)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s)
            ON CONFLICT (claim_hash) DO NOTHING
            RETURNING claim_id
            """,
            (doc_id, chunk_id, claim_text, sign, effect_size_text, json.dumps(conditions or {}), confidence, json.dumps(evidence), claim_hash)
        )
        result = cur.fetchone()
        return result is not None


# ============================================================
# 辅助函数：高价值 Chunk 筛选（供内部调用）
# ============================================================


def _select_high_value_chunks_internal(
    doc_id: str | None = None,
    pack_id: int | None = None,
    max_chunks: int = 60,
    keyword_mode: str = "default",
) -> dict[str, Any]:
    """高价值 chunk 筛选的核心逻辑（内部使用）"""
    if not doc_id and not pack_id:
        return {
            "chunks": [],
            "error": {"code": "VALIDATION_ERROR", "message": "Must provide either doc_id or pack_id"},
        }
    
    # 选择关键词集
    keywords = HIGH_VALUE_KEYWORDS_STRICT if keyword_mode == "strict" else HIGH_VALUE_KEYWORDS_DEFAULT
    
    # 构建 FTS 查询
    fts_query = " OR ".join(f"'{kw}'" for kw in keywords)
    
    if pack_id:
        # 从证据包获取
        results = query_all(
            """
            SELECT c.chunk_id, c.doc_id, c.page_start, c.page_end, c.text
            FROM evidence_pack_items i
            JOIN chunks c ON c.chunk_id = i.chunk_id
            WHERE i.pack_id = %s
            LIMIT %s
            """,
            (pack_id, max_chunks)
        )
        reason = "from evidence pack"
    else:
        # 使用 FTS 筛选
        results = query_all(
            """
            SELECT chunk_id, doc_id, page_start, page_end, text,
                   ts_rank(tsv, websearch_to_tsquery('english', %s)) AS rank
            FROM chunks
            WHERE doc_id = %s
              AND tsv @@ websearch_to_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
            """,
            (fts_query, doc_id, fts_query, max_chunks)
        )
        reason = "keyword match"
    
    # 构建返回结果
    chunks = []
    for r in results:
        # 识别命中的关键词
        text_lower = r["text"].lower() if r.get("text") else ""
        matched_keywords = [kw for kw in keywords if kw in text_lower]
        chunk_reason = f"{reason}: {', '.join(matched_keywords[:3])}" if matched_keywords else reason
        
        chunks.append({
            "chunk_id": r["chunk_id"],
            "doc_id": r["doc_id"],
            "page_start": r.get("page_start"),
            "page_end": r.get("page_end"),
            "reason": chunk_reason,
        })
    
    return {"chunks": chunks, "error": None}


# ============================================================
# 工具注册
# ============================================================



async def extract_graph_v1_run(
    doc_id: str | None = None,
    chunk_ids: list[int] | None = None,
    mode: str = "high_value_only",
    max_chunks: int = 60,
    llm_model: str | None = None,
    min_confidence: float = 0.8,
    dry_run: bool = False,
    concurrency: int = 60,
) -> dict[str, Any]:
    """抽取结构化图谱要素 (Internal Implementation)"""
    try:
        settings = get_settings()
        actual_llm_model = llm_model or settings.llm_model
        
        if not doc_id and not chunk_ids:
            return ExtractGraphOut(
                doc_id="",
                stats=ExtractGraphStats(
                    processed_chunks=0, new_entities=0, new_mentions=0,
                    new_relations=0, new_claims=0, skipped_low_confidence=0
                ),
                error=MCPErrorModel(code="VALIDATION_ERROR", message="Must provide either doc_id or chunk_ids"),
            ).model_dump()
        
        # --- 1. 确定要处理的 chunks (Sync DB Query) ---
        if chunk_ids:
            chunks = query_all(
                """
                SELECT chunk_id, doc_id, page_start, page_end, text
                FROM chunks
                WHERE chunk_id = ANY(%s)
                ORDER BY chunk_id
                LIMIT %s
                """,
                (chunk_ids, max_chunks)
            )
            actual_doc_id = chunks[0]["doc_id"] if chunks else doc_id or ""
        else:
            if mode == "high_value_only":
                hv_result = _select_high_value_chunks_internal(doc_id=doc_id, max_chunks=max_chunks)
                if hv_result.get("error"):
                    return ExtractGraphOut(
                        doc_id=doc_id or "",
                        stats=ExtractGraphStats(
                            processed_chunks=0, new_entities=0, new_mentions=0,
                            new_relations=0, new_claims=0, skipped_low_confidence=0
                        ),
                        error=MCPErrorModel(**hv_result["error"]),
                    ).model_dump()
                
                chunk_id_list = [c["chunk_id"] for c in hv_result.get("chunks", [])]
                if not chunk_id_list:
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
                else:
                    chunks = query_all(
                        """
                        SELECT chunk_id, doc_id, page_start, page_end, text
                        FROM chunks
                        WHERE chunk_id = ANY(%s)
                        ORDER BY chunk_id
                        """,
                        (chunk_id_list,)
                    )
            else:
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
            actual_doc_id = doc_id or ""
        
        if not chunks:
            return ExtractGraphOut(
                doc_id=actual_doc_id,
                stats=ExtractGraphStats(
                    processed_chunks=0, new_entities=0, new_mentions=0,
                    new_relations=0, new_claims=0, skipped_low_confidence=0
                ),
                error=MCPErrorModel(code="NOT_FOUND", message="No chunks found"),
            ).model_dump()
        
        # --- 2. 并行处理 LLM 抽取 (Async) ---
        sem = asyncio.Semaphore(concurrency)  # 使用参数控制并发
        
        async def process_single_chunk(chunk):
            async with sem:
                extraction = await acall_llm_extract(chunk["text"], actual_llm_model)
                return chunk, extraction

        tasks = [process_single_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        
        # --- 3. 结果入库 (Sync Transaction) ---
        stats = {
            "processed_chunks": 0,
            "new_entities": 0,
            "new_mentions": 0,
            "new_relations": 0,
            "new_claims": 0,
            "skipped_low_confidence": 0,
        }
        
        with get_db() as conn:
            # 确保 Paper entity 存在
            paper_entity_id = upsert_entity(
                conn, EntityType.Paper, actual_doc_id, actual_doc_id, {}, 1.0
            )
            
            for chunk, extraction in results:
                if not extraction:
                    continue
                    
                stats["processed_chunks"] += 1
                
                if dry_run:
                    stats["new_entities"] += len(extraction.entities)
                    stats["new_mentions"] += len(extraction.mentions)
                    stats["new_relations"] += len(extraction.relations)
                    stats["new_claims"] += len(extraction.claims)
                    continue
                
                chunk_id = chunk["chunk_id"]
                chunk_doc_id = chunk["doc_id"]
                page_start = chunk.get("page_start")
                page_end = chunk.get("page_end")
                
                # temp_id -> entity_id 映射
                temp_to_entity: dict[str, int] = {"paper": paper_entity_id}
                
                # 处理实体
                for entity in extraction.entities:
                    if entity.confidence < min_confidence:
                        stats["skipped_low_confidence"] += 1
                        continue
                    
                    canonical_key = generate_canonical_key(
                        entity.type, entity.name, entity.normalized
                    )
                    entity_id = upsert_entity(
                        conn,
                        entity.type,
                        entity.name,
                        canonical_key,
                        entity.normalized,
                        entity.confidence,
                    )
                    temp_to_entity[entity.temp_id] = entity_id
                    stats["new_entities"] += 1
                    
                    alias_norm = normalize_alias(entity.name)
                    insert_alias(conn, entity_id, entity.name, alias_norm)
                
                # 处理 mentions
                for mention in extraction.mentions:
                    if mention.confidence < min_confidence:
                        stats["skipped_low_confidence"] += 1
                        continue
                    
                    entity_id = temp_to_entity.get(mention.entity_temp_id)
                    if not entity_id:
                        continue
                    
                    insert_mention(
                        conn, entity_id, chunk_doc_id, chunk_id,
                        page_start, page_end, mention.quote, mention.confidence
                    )
                    stats["new_mentions"] += 1
                
                # 处理关系
                for relation in extraction.relations:
                    if relation.confidence < min_confidence:
                        stats["skipped_low_confidence"] += 1
                        continue
                    
                    subj_id = temp_to_entity.get(relation.subject_temp_id)
                    obj_id = temp_to_entity.get(relation.object_temp_id)
                    if not subj_id or not obj_id:
                        continue
                    
                    relation_hash = compute_relation_hash(
                        subj_id, relation.predicate.value, obj_id, relation.evidence_quote
                    )
                    evidence = {
                        "doc_id": chunk_doc_id,
                        "chunk_id": chunk_id,
                        "quote": relation.evidence_quote,
                        "page_start": page_start,
                        "page_end": page_end,
                    }
                    
                    if insert_relation(
                        conn, subj_id, relation.predicate.value, obj_id,
                        relation.qualifiers, relation.confidence, evidence, relation_hash
                    ):
                        stats["new_relations"] += 1
                
                # 处理 claims
                for claim in extraction.claims:
                    if claim.confidence < min_confidence:
                        stats["skipped_low_confidence"] += 1
                        continue
                    
                    claim_hash = compute_claim_hash(chunk_doc_id, chunk_id, claim.claim_text)
                    evidence = {
                        "quote": claim.evidence_quote,
                        "page_start": page_start,
                        "page_end": page_end,
                    }
                    sign_value = claim.sign.value if claim.sign else None
                    
                    if insert_claim(
                        conn, chunk_doc_id, chunk_id, claim.claim_text,
                        sign_value, claim.effect_size_text, claim.conditions,
                        claim.confidence, evidence, claim_hash
                    ):
                        stats["new_claims"] += 1
        
        return ExtractGraphOut(
            doc_id=actual_doc_id,
            stats=ExtractGraphStats(**stats),
        ).model_dump()
        
    except Exception as e:
        return ExtractGraphOut(
            doc_id=doc_id or "",
            stats=ExtractGraphStats(
                processed_chunks=0, new_entities=0, new_mentions=0,
                new_relations=0, new_claims=0, skipped_low_confidence=0
            ),
            error=MCPErrorModel(code="LLM_ERROR", message=str(e)),
        ).model_dump()


def register_graph_extract_tools(mcp: FastMCP) -> None:
    """注册 GraphRAG 抽取工具"""

    @mcp.tool()
    def graph_health_check(include_counts: bool = True) -> dict[str, Any]:
        """检查 GraphRAG 层健康状态
        
        验证 M2 GraphRAG 所需的表和索引是否存在，并返回统计信息。
        
        Args:
            include_counts: 是否包含各表的行数统计，默认 True
            
        Returns:
            健康状态信息，包含：
            - ok: 整体状态是否正常
            - db_ok: 数据库连接状态
            - tables_ok: 必要表是否存在
            - indexes_ok: 必要索引是否存在
            - counts: 各表行数（可选）
        """
        try:
            notes = []
            
            # 检查表存在性
            tables_result = query_all(
                """
                SELECT table_name 
                FROM information_schema.tables
                WHERE table_schema = 'public' 
                AND table_name = ANY(%s)
                """,
                (REQUIRED_TABLES,)
            )
            existing_tables = {r["table_name"] for r in tables_result}
            missing_tables = set(REQUIRED_TABLES) - existing_tables
            tables_ok = len(missing_tables) == 0
            
            if missing_tables:
                notes.append(f"Missing tables: {', '.join(sorted(missing_tables))}")
            
            # 检查索引存在性
            indexes_result = query_all(
                """
                SELECT indexname 
                FROM pg_indexes
                WHERE schemaname = 'public' 
                AND indexname = ANY(%s)
                """,
                (REQUIRED_INDEXES,)
            )
            existing_indexes = {r["indexname"] for r in indexes_result}
            missing_indexes = set(REQUIRED_INDEXES) - existing_indexes
            indexes_ok = len(missing_indexes) == 0
            
            if missing_indexes:
                notes.append(f"Missing indexes: {', '.join(sorted(missing_indexes))}")
            
            # 获取统计信息
            counts = None
            if include_counts and tables_ok:
                counts = {}
                for table in REQUIRED_TABLES:
                    if table in existing_tables:
                        result = query_one(f"SELECT COUNT(*) as count FROM {table}")
                        counts[table] = result["count"] if result else 0
            
            ok = tables_ok and indexes_ok
            
            return GraphHealthCheckOut(
                ok=ok,
                db_ok=True,
                tables_ok=tables_ok,
                indexes_ok=indexes_ok,
                notes=notes,
                counts=counts,
            ).model_dump()
            
        except Exception as e:
            return GraphHealthCheckOut(
                ok=False,
                db_ok=False,
                tables_ok=False,
                indexes_ok=False,
                notes=[str(e)],
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

    @mcp.tool()
    def select_high_value_chunks(
        doc_id: str | None = None,
        pack_id: int | None = None,
        max_chunks: int = 60,
        keyword_mode: str = "default",
    ) -> dict[str, Any]:
        """筛选高价值 chunks
        
        从指定文档或证据包中筛选包含关键方法/识别/结果相关内容的 chunks。
        
        Args:
            doc_id: 文档 ID（与 pack_id 二选一）
            pack_id: 证据包 ID（与 doc_id 二选一）
            max_chunks: 最大返回数量，默认 60
            keyword_mode: 关键词模式，"default" 或 "strict"
            
        Returns:
            高价值 chunk 列表，每个包含 chunk_id、doc_id、页码和命中原因
        """
        try:
            # 调用内部函数
            result = _select_high_value_chunks_internal(doc_id, pack_id, max_chunks, keyword_mode)
            
            if result.get("error"):
                return SelectHighValueChunksOut(
                    error=MCPErrorModel(**result["error"]),
                ).model_dump()
            
            # 转换为 Pydantic 模型
            chunks = [
                HighValueChunk(
                    chunk_id=c["chunk_id"],
                    doc_id=c["doc_id"],
                    page_start=c.get("page_start"),
                    page_end=c.get("page_end"),
                    reason=c["reason"],
                )
                for c in result.get("chunks", [])
            ]
            
            return SelectHighValueChunksOut(chunks=chunks).model_dump()
            
        except Exception as e:
            return SelectHighValueChunksOut(
                error=MCPErrorModel(code="DB_CONN_ERROR", message=str(e)),
            ).model_dump()

    @mcp.tool()
    async def extract_graph_v1(
        doc_id: str | None = None,
        chunk_ids: list[int] | None = None,
        mode: str = "high_value_only",
        max_chunks: int = 60,
        llm_model: str | None = None,
        min_confidence: float = 0.8,
        dry_run: bool = False,
        concurrency: int = 60,
    ) -> dict[str, Any]:
        """抽取结构化图谱要素 (Async Parallel)
        
        从文档的 chunks 中抽取实体、关系和结论，写入 GraphRAG 表。
        使用并行处理以加快速度。
        
        Args:
            concurrency: 并发请求数，默认 60。OpenRouter 支持较高并发 (500 RPS)。
        """
        return await extract_graph_v1_run(
            doc_id=doc_id,
            chunk_ids=chunk_ids,
            mode=mode,
            max_chunks=max_chunks,
            llm_model=llm_model,
            min_confidence=min_confidence,
            dry_run=dry_run,
            concurrency=concurrency,
        )


