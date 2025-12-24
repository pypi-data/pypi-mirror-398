-- M2 Migration: GraphRAG v1 表结构
-- 运行方式: psql -h localhost -U paper -d paperlib -f 003_m2_graphrag.sql

-- ============================================================
-- 实体表 (entities)
-- ============================================================

CREATE TABLE IF NOT EXISTS entities (
  entity_id       BIGSERIAL PRIMARY KEY,
  type            TEXT NOT NULL,                    -- Paper/Topic/MeasureProxy/IdentificationStrategy/Method/Setting/DataSource/Mechanism/LimitationGap
  canonical_name  TEXT NOT NULL,                    -- 规范名称
  canonical_key   TEXT NOT NULL,                    -- 规范键（用于去重）
  normalized      JSONB DEFAULT '{}'::jsonb,        -- 归一化元数据
  confidence      FLOAT DEFAULT 1.0,                -- 置信度
  is_locked       BOOLEAN DEFAULT FALSE,            -- 是否锁定（防止自动合并）
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE (type, canonical_key)
);

CREATE INDEX IF NOT EXISTS entities_type_idx ON entities(type);
CREATE INDEX IF NOT EXISTS entities_canonical_key_idx ON entities(canonical_key);
CREATE INDEX IF NOT EXISTS entities_is_locked_idx ON entities(is_locked) WHERE is_locked = TRUE;

-- ============================================================
-- 实体别名表 (entity_aliases)
-- ============================================================

CREATE TABLE IF NOT EXISTS entity_aliases (
  alias_id        BIGSERIAL PRIMARY KEY,
  entity_id       BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  alias           TEXT NOT NULL,                    -- 原始别名
  alias_norm      TEXT NOT NULL,                    -- 归一化别名
  alias_type      TEXT DEFAULT 'extracted',         -- extracted/manual/synonym
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS entity_aliases_entity_idx ON entity_aliases(entity_id);
CREATE INDEX IF NOT EXISTS entity_aliases_norm_idx ON entity_aliases(alias_norm);
CREATE UNIQUE INDEX IF NOT EXISTS entity_aliases_unique_idx ON entity_aliases(entity_id, alias_norm);

-- ============================================================
-- 实体提及表 (mentions) - 证据追溯核心
-- ============================================================

CREATE TABLE IF NOT EXISTS mentions (
  mention_id      BIGSERIAL PRIMARY KEY,
  entity_id       BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  doc_id          TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  chunk_id        BIGINT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  page_start      INT,
  page_end        INT,
  span_start      INT,                              -- 在 chunk 文本中的起始位置
  span_end        INT,                              -- 在 chunk 文本中的结束位置
  quote           TEXT,                             -- 原文引用
  confidence      FLOAT DEFAULT 1.0,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mentions_entity_idx ON mentions(entity_id);
CREATE INDEX IF NOT EXISTS mentions_doc_idx ON mentions(doc_id);
CREATE INDEX IF NOT EXISTS mentions_chunk_idx ON mentions(chunk_id);

-- ============================================================
-- 关系表 (relations)
-- ============================================================

CREATE TABLE IF NOT EXISTS relations (
  rel_id          BIGSERIAL PRIMARY KEY,
  subj_entity_id  BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  predicate       TEXT NOT NULL,                    -- PAPER_HAS_TOPIC/PAPER_USES_MEASURE/PAPER_IDENTIFIES_WITH/...
  obj_entity_id   BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  qualifiers      JSONB DEFAULT '{}'::jsonb,        -- 额外限定条件
  confidence      FLOAT DEFAULT 1.0,
  evidence        JSONB DEFAULT '{}'::jsonb,        -- {doc_id, chunk_id, quote, page_start, page_end}
  relation_hash   TEXT UNIQUE,                      -- 用于去重
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS relations_subj_idx ON relations(subj_entity_id);
CREATE INDEX IF NOT EXISTS relations_obj_idx ON relations(obj_entity_id);
CREATE INDEX IF NOT EXISTS relations_predicate_idx ON relations(predicate);

-- ============================================================
-- 结论/声明表 (claims)
-- ============================================================

CREATE TABLE IF NOT EXISTS claims (
  claim_id        BIGSERIAL PRIMARY KEY,
  doc_id          TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  chunk_id        BIGINT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  claim_text      TEXT NOT NULL,                    -- 结论原文
  sign            TEXT,                             -- positive/negative/mixed/null
  effect_size_text TEXT,                            -- 效应量描述
  conditions      JSONB DEFAULT '{}'::jsonb,        -- 适用条件
  confidence      FLOAT DEFAULT 1.0,
  evidence        JSONB DEFAULT '{}'::jsonb,        -- 额外证据信息
  claim_hash      TEXT UNIQUE,                      -- 用于去重
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS claims_doc_idx ON claims(doc_id);
CREATE INDEX IF NOT EXISTS claims_chunk_idx ON claims(chunk_id);
CREATE INDEX IF NOT EXISTS claims_sign_idx ON claims(sign);

-- ============================================================
-- 社区表 (communities)
-- ============================================================

CREATE TABLE IF NOT EXISTS communities (
  comm_id         BIGSERIAL PRIMARY KEY,
  level           TEXT NOT NULL DEFAULT 'macro',    -- macro/micro
  method          TEXT NOT NULL DEFAULT 'leiden',   -- leiden/louvain/...
  params          JSONB DEFAULT '{}'::jsonb,        -- 聚类参数 {resolution, min_df, ...}
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS communities_level_idx ON communities(level);

-- ============================================================
-- 社区成员表 (community_members)
-- ============================================================

CREATE TABLE IF NOT EXISTS community_members (
  id              BIGSERIAL PRIMARY KEY,
  comm_id         BIGINT NOT NULL REFERENCES communities(comm_id) ON DELETE CASCADE,
  entity_id       BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  role            TEXT DEFAULT 'member',            -- member/hub/...
  weight          FLOAT DEFAULT 1.0,                -- 成员权重
  created_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE (comm_id, entity_id)
);

CREATE INDEX IF NOT EXISTS community_members_comm_idx ON community_members(comm_id);
CREATE INDEX IF NOT EXISTS community_members_entity_idx ON community_members(entity_id);

-- ============================================================
-- 社区摘要表 (community_summaries)
-- ============================================================

CREATE TABLE IF NOT EXISTS community_summaries (
  id              BIGSERIAL PRIMARY KEY,
  comm_id         BIGINT NOT NULL REFERENCES communities(comm_id) ON DELETE CASCADE UNIQUE,
  summary_json    JSONB NOT NULL,                   -- {scope, measures, ids, consensus, debates, gaps, entry_points, ...}
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS community_summaries_comm_idx ON community_summaries(comm_id);

-- ============================================================
-- 实体合并日志表 (entity_merge_log)
-- ============================================================

CREATE TABLE IF NOT EXISTS entity_merge_log (
  id              BIGSERIAL PRIMARY KEY,
  from_entity_id  BIGINT NOT NULL,                  -- 被合并的实体（已删除）
  to_entity_id    BIGINT NOT NULL,                  -- 目标实体
  reason          TEXT,                             -- 合并原因
  merged_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS entity_merge_log_to_idx ON entity_merge_log(to_entity_id);

-- ============================================================
-- 验证表已创建
-- ============================================================

SELECT 'entities' as table_name, COUNT(*) as row_count FROM entities
UNION ALL
SELECT 'entity_aliases', COUNT(*) FROM entity_aliases
UNION ALL
SELECT 'mentions', COUNT(*) FROM mentions
UNION ALL
SELECT 'relations', COUNT(*) FROM relations
UNION ALL
SELECT 'claims', COUNT(*) FROM claims
UNION ALL
SELECT 'communities', COUNT(*) FROM communities
UNION ALL
SELECT 'community_members', COUNT(*) FROM community_members
UNION ALL
SELECT 'community_summaries', COUNT(*) FROM community_summaries
UNION ALL
SELECT 'entity_merge_log', COUNT(*) FROM entity_merge_log;

