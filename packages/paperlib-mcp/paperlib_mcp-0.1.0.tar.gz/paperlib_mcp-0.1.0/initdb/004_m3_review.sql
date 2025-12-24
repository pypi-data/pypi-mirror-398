-- M3 Migration: Review Infrastructure
-- 运行方式: psql -h localhost -U paper -d paperlib -f 004_m3_review.sql

-- ============================================================
-- 综述大纲主表 (review_outlines)
-- ============================================================

CREATE TABLE IF NOT EXISTS review_outlines (
  outline_id      TEXT PRIMARY KEY,               -- UUID
  topic           TEXT NOT NULL,
  outline_style   TEXT NOT NULL DEFAULT 'econ_finance_canonical',
  sources_json    JSONB,                          -- {comm_ids, doc_ids, ...}
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS review_outlines_topic_idx ON review_outlines(topic);
CREATE INDEX IF NOT EXISTS review_outlines_style_idx ON review_outlines(outline_style);

-- ============================================================
-- 大纲章节表 (review_outline_sections)
-- ============================================================

CREATE TABLE IF NOT EXISTS review_outline_sections (
  id              BIGSERIAL PRIMARY KEY,
  outline_id      TEXT NOT NULL REFERENCES review_outlines(outline_id) ON DELETE CASCADE,
  section_id      TEXT NOT NULL,                  -- research_question/measurement/identification/findings/debates/gaps
  title           TEXT NOT NULL,
  description     TEXT,
  ord             INT NOT NULL,                   -- display order
  sources_json    JSONB,                          -- section-specific sources {comm_ids, doc_ids}
  keywords        TEXT[],
  UNIQUE (outline_id, section_id)
);

CREATE INDEX IF NOT EXISTS review_outline_sections_outline_idx ON review_outline_sections(outline_id);

-- ============================================================
-- 章节 ↔ pack 缓存映射表 (review_section_packs)
-- ============================================================

CREATE TABLE IF NOT EXISTS review_section_packs (
  outline_id      TEXT NOT NULL,
  section_id      TEXT NOT NULL,
  pack_id         BIGINT NOT NULL REFERENCES evidence_packs(pack_id) ON DELETE CASCADE,
  params          JSONB NOT NULL,                 -- {max_chunks, per_doc_limit, ...}
  created_at      TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (outline_id, section_id)
);

CREATE INDEX IF NOT EXISTS review_section_packs_pack_idx ON review_section_packs(pack_id);

-- ============================================================
-- 验证表已创建
-- ============================================================

SELECT 'review_outlines' as table_name, COUNT(*) as row_count FROM review_outlines
UNION ALL
SELECT 'review_outline_sections', COUNT(*) FROM review_outline_sections
UNION ALL
SELECT 'review_section_packs', COUNT(*) FROM review_section_packs;
