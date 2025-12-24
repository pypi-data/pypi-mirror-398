"""GraphRAG v1 Pydantic 模型定义"""

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================
# 枚举类型
# ============================================================


class EntityType(str, Enum):
    """实体类型枚举"""
    Paper = "Paper"                         # 论文本身（canonical_key = doc_id）
    Topic = "Topic"                         # 研究主题
    MeasureProxy = "MeasureProxy"           # 度量/代理变量
    IdentificationStrategy = "IdentificationStrategy"  # 识别策略
    Method = "Method"                       # 研究方法
    Setting = "Setting"                     # 研究场景/背景
    DataSource = "DataSource"               # 数据来源
    Mechanism = "Mechanism"                 # 机制
    LimitationGap = "LimitationGap"         # 局限性/研究空白


class Predicate(str, Enum):
    """关系谓词枚举"""
    PAPER_HAS_TOPIC = "PAPER_HAS_TOPIC"
    PAPER_USES_MEASURE = "PAPER_USES_MEASURE"
    PAPER_IDENTIFIES_WITH = "PAPER_IDENTIFIES_WITH"
    PAPER_USES_METHOD = "PAPER_USES_METHOD"
    PAPER_IN_SETTING = "PAPER_IN_SETTING"
    PAPER_USES_DATA = "PAPER_USES_DATA"
    PAPER_PROPOSES_MECHANISM = "PAPER_PROPOSES_MECHANISM"
    PAPER_NOTES_LIMITATION = "PAPER_NOTES_LIMITATION"
    # 可扩展的关系类型
    CLAIM_SUPPORTS = "CLAIM_SUPPORTS"
    CLAIM_CONTRADICTS = "CLAIM_CONTRADICTS"


class ClaimSign(str, Enum):
    """结论方向枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NULL = "null"


# ============================================================
# 通用错误模型
# ============================================================


class MCPErrorModel(BaseModel):
    """统一错误返回模型"""
    code: str  # DB_CONN_ERROR, S3_ERROR, LLM_ERROR, VALIDATION_ERROR, NOT_FOUND
    message: str
    details: Optional[dict[str, Any]] = None


# ============================================================
# graph_health_check 工具模型
# ============================================================


class GraphHealthCheckIn(BaseModel):
    """graph_health_check 输入"""
    include_counts: bool = True


class GraphHealthCheckOut(BaseModel):
    """graph_health_check 输出"""
    ok: bool
    db_ok: bool
    tables_ok: bool
    indexes_ok: bool
    notes: list[str] = Field(default_factory=list)
    counts: Optional[dict[str, int]] = None
    error: Optional[MCPErrorModel] = None


# ============================================================
# select_high_value_chunks 工具模型
# ============================================================


class SelectHighValueChunksIn(BaseModel):
    """select_high_value_chunks 输入"""
    doc_id: Optional[str] = None
    pack_id: Optional[int] = None
    max_chunks: int = 60
    keyword_mode: Literal["default", "strict"] = "default"


class HighValueChunk(BaseModel):
    """高价值 chunk"""
    chunk_id: int
    doc_id: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    reason: str


class SelectHighValueChunksOut(BaseModel):
    """select_high_value_chunks 输出"""
    chunks: list[HighValueChunk] = Field(default_factory=list)
    error: Optional[MCPErrorModel] = None


# ============================================================
# extract_graph_v1 工具模型
# ============================================================


class ExtractGraphIn(BaseModel):
    """extract_graph_v1 输入"""
    doc_id: Optional[str] = None
    chunk_ids: Optional[list[int]] = None
    mode: Literal["high_value_only", "all"] = "high_value_only"
    max_chunks: int = 60
    llm_model: Optional[str] = None  # 默认使用环境变量 LLM_MODEL
    min_confidence: float = 0.8
    dry_run: bool = False


class ExtractGraphStats(BaseModel):
    """抽取统计"""
    processed_chunks: int
    new_entities: int
    new_mentions: int
    new_relations: int
    new_claims: int
    skipped_low_confidence: int


class ExtractGraphOut(BaseModel):
    """extract_graph_v1 输出"""
    doc_id: str
    stats: ExtractGraphStats
    error: Optional[MCPErrorModel] = None


# ============================================================
# LLM 抽取输出模型（用于 Pydantic 校验）
# ============================================================


class ExtractedEntity(BaseModel):
    """LLM 抽取的实体"""
    temp_id: str                            # 临时 ID，用于关联
    type: EntityType
    name: str                               # 实体名称
    normalized: Optional[dict[str, Any]] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class ExtractedMention(BaseModel):
    """LLM 抽取的提及"""
    entity_temp_id: str                     # 关联到 ExtractedEntity.temp_id
    quote: str                              # 原文引用
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class ExtractedRelation(BaseModel):
    """LLM 抽取的关系"""
    subject_temp_id: str                    # 主体临时 ID
    predicate: Predicate
    object_temp_id: str                     # 客体临时 ID
    qualifiers: Optional[dict[str, Any]] = None
    evidence_quote: str                     # 证据引用
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class ExtractedClaim(BaseModel):
    """LLM 抽取的结论"""
    claim_text: str
    sign: Optional[ClaimSign] = None
    effect_size_text: Optional[str] = None
    conditions: Optional[dict[str, Any]] = None
    evidence_quote: str                     # 证据引用
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class ChunkExtractionResult(BaseModel):
    """单个 chunk 的抽取结果"""
    entities: list[ExtractedEntity] = Field(default_factory=list)
    mentions: list[ExtractedMention] = Field(default_factory=list)
    relations: list[ExtractedRelation] = Field(default_factory=list)
    claims: list[ExtractedClaim] = Field(default_factory=list)


# ============================================================
# canonicalize_entities_v1 工具模型
# ============================================================


class CanonicalizeEntitiesIn(BaseModel):
    """canonicalize_entities_v1 输入"""
    types: list[EntityType] = Field(default_factory=lambda: [
        EntityType.Topic,
        EntityType.MeasureProxy,
        EntityType.IdentificationStrategy,
        EntityType.Method,
    ])
    suggest_only: bool = False
    max_groups: int = 5000


class MergeSuggestion(BaseModel):
    """合并建议"""
    type: EntityType
    canonical_key: str
    winner_entity_id: int
    merged_entity_ids: list[int]


class CanonicalizeEntitiesOut(BaseModel):
    """canonicalize_entities_v1 输出"""
    executed: bool
    merged_groups: int
    merged_entities: int
    suggestions: list[MergeSuggestion] = Field(default_factory=list)
    error: Optional[MCPErrorModel] = None


# ============================================================
# lock_entity / merge_entities 工具模型
# ============================================================


class LockEntityIn(BaseModel):
    """lock_entity 输入"""
    entity_id: int
    is_locked: bool = True


class LockEntityOut(BaseModel):
    """lock_entity 输出"""
    ok: bool
    error: Optional[MCPErrorModel] = None


class MergeEntitiesIn(BaseModel):
    """merge_entities 输入"""
    from_entity_id: int
    to_entity_id: int
    reason: str


class MergeEntitiesOut(BaseModel):
    """merge_entities 输出"""
    ok: bool
    error: Optional[MCPErrorModel] = None


# ============================================================
# build_communities_v1 工具模型
# ============================================================


class BuildCommunitiesIn(BaseModel):
    """build_communities_v1 输入"""
    level: Literal["macro", "micro"] = "macro"
    min_df: int = 3                         # 节点至少出现在 N 篇 paper
    resolution: float = 1.0                 # Leiden resolution
    max_nodes: int = 20000
    rebuild: bool = False                   # 是否清除同 level 旧结果


class CommunityBrief(BaseModel):
    """社区简要信息"""
    comm_id: int
    size: int
    top_entities: list[dict[str, Any]]      # [{entity_id, type, canonical_name, weight}, ...]


class BuildCommunitiesOut(BaseModel):
    """build_communities_v1 输出"""
    communities: list[CommunityBrief] = Field(default_factory=list)
    error: Optional[MCPErrorModel] = None


# ============================================================
# build_community_evidence_pack 工具模型
# ============================================================


class BuildCommunityEvidencePackIn(BaseModel):
    """build_community_evidence_pack 输入"""
    comm_id: int
    max_chunks: int = 100
    per_doc_limit: int = 4


class BuildCommunityEvidencePackOut(BaseModel):
    """build_community_evidence_pack 输出"""
    pack_id: int
    docs: int
    chunks: int
    error: Optional[MCPErrorModel] = None


# ============================================================
# summarize_community_v1 工具模型
# ============================================================


class SummarizeCommunityIn(BaseModel):
    """summarize_community_v1 输入"""
    comm_id: int
    pack_id: Optional[int] = None
    llm_model: Optional[str] = None  # 默认使用环境变量 LLM_MODEL
    max_chunks: int = 100
    style: Literal["econ_finance"] = "econ_finance"


class SummarizeCommunityOut(BaseModel):
    """summarize_community_v1 输出"""
    comm_id: int
    pack_id: int
    summary_json: dict[str, Any]
    markdown: str
    error: Optional[MCPErrorModel] = None


# ============================================================
# export_evidence_matrix_v1 工具模型
# ============================================================


class ExportEvidenceMatrixIn(BaseModel):
    """export_evidence_matrix_v1 输入"""
    comm_id: Optional[int] = None
    topic: Optional[str] = None             # topic 名称或 canonical_key
    format: Literal["json", "csv"] = "json"
    limit_docs: Optional[int] = None


class ExportEvidenceMatrixOut(BaseModel):
    """export_evidence_matrix_v1 输出"""
    paper_matrix: list[dict[str, Any]] = Field(default_factory=list)
    claim_matrix: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[MCPErrorModel] = None


# ============================================================
# 维护工具模型
# ============================================================


class GraphStatusIn(BaseModel):
    """graph_status 输入"""
    doc_id: Optional[str] = None


class GraphStatusOut(BaseModel):
    """graph_status 输出"""
    coverage: dict[str, Any]
    error: Optional[MCPErrorModel] = None


class ExtractGraphMissingIn(BaseModel):
    """extract_graph_missing 输入"""
    limit_docs: int = 50
    llm_model: Optional[str] = None  # 默认使用环境变量 LLM_MODEL
    min_confidence: float = 0.8


class ExtractGraphMissingOut(BaseModel):
    """extract_graph_missing 输出"""
    processed_docs: int
    doc_ids: list[str] = Field(default_factory=list)
    error: Optional[MCPErrorModel] = None


class ClearGraphIn(BaseModel):
    """clear_graph 输入"""
    doc_id: Optional[str] = None
    clear_all: bool = False


class ClearGraphOut(BaseModel):
    """clear_graph 输出"""
    ok: bool
    deleted_counts: Optional[dict[str, int]] = None
    error: Optional[MCPErrorModel] = None


# ============================================================
# canonicalize_relations_v1 工具模型
# ============================================================


class CanonicalizeRelationsIn(BaseModel):
    """canonicalize_relations_v1 输入"""
    scope: Literal["all"] | str = "all"  # "all", "doc_id:...", "comm_id:..."
    predicate_whitelist: Optional[list[str]] = None
    qualifier_keys_keep: list[str] = ["id_family", "measure_family", "setting_country", "sample_period_bin"]
    dry_run: bool = False


class CanonicalizeRelationsOut(BaseModel):
    """canonicalize_relations_v1 输出"""
    new_canonical_relations: int
    new_evidence_records: int
    skipped_relations: int
    error: Optional[MCPErrorModel] = None


class ExportRelationsCompactIn(BaseModel):
    """export_relations_compact_v1 输入"""
    comm_id: Optional[int] = None
    pack_id: Optional[int] = None


class ExportRelationsCompactOut(BaseModel):
    """export_relations_compact_v1 输出"""
    relations: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[MCPErrorModel] = None


# ============================================================
# build_claim_groups_v1 工具模型
# ============================================================


class BuildClaimGroupsIn(BaseModel):
    """build_claim_groups_v1 输入"""
    scope: Literal["all"] | str = "all"
    max_claims_per_doc: int = 20
    dry_run: bool = False


class BuildClaimGroupsOut(BaseModel):
    """build_claim_groups_v1 输出"""
    new_groups: int
    total_members: int
    error: Optional[MCPErrorModel] = None


class ExportClaimMatrixGroupedIn(BaseModel):
    """export_claim_matrix_grouped_v1 输入"""
    comm_id: Optional[int] = None
    pack_id: Optional[int] = None


class ExportClaimMatrixGroupedOut(BaseModel):
    """export_claim_matrix_grouped_v1 输出"""
    groups: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[MCPErrorModel] = None

