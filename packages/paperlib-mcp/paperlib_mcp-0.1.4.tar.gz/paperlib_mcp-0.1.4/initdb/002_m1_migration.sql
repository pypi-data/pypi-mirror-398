-- M1 Migration: 添加导入状态管理和证据包表
-- 运行方式: psql -h localhost -U paper -d paperlib -f 002_m1_migration.sql

-- ============================================================
-- 导入状态管理表
-- ============================================================

-- 导入作业主表
CREATE TABLE IF NOT EXISTS ingest_jobs (
  job_id        BIGSERIAL PRIMARY KEY,
  doc_id        TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'pending',  -- pending/running/completed/failed
  current_stage TEXT,                              -- HASHED/UPLOADED/EXTRACTED/CHUNKED/EMBEDDED/COMMITTED
  started_at    TIMESTAMPTZ DEFAULT now(),
  finished_at   TIMESTAMPTZ,
  error         TEXT
);

CREATE INDEX IF NOT EXISTS ingest_jobs_doc_idx ON ingest_jobs(doc_id);
CREATE INDEX IF NOT EXISTS ingest_jobs_status_idx ON ingest_jobs(status);

-- 导入阶段详情表
CREATE TABLE IF NOT EXISTS ingest_job_items (
  id          BIGSERIAL PRIMARY KEY,
  job_id      BIGINT NOT NULL REFERENCES ingest_jobs(job_id) ON DELETE CASCADE,
  stage       TEXT NOT NULL,   -- HASHED/UPLOADED/EXTRACTED/CHUNKED/EMBEDDED/COMMITTED
  status      TEXT NOT NULL,   -- pending/running/completed/failed
  message     TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ingest_job_items_job_idx ON ingest_job_items(job_id);

-- ============================================================
-- 证据包表
-- ============================================================

-- 证据包主表
CREATE TABLE IF NOT EXISTS evidence_packs (
  pack_id     BIGSERIAL PRIMARY KEY,
  query       TEXT NOT NULL,
  params_json JSONB,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- 证据包条目表
CREATE TABLE IF NOT EXISTS evidence_pack_items (
  id        BIGSERIAL PRIMARY KEY,
  pack_id   BIGINT NOT NULL REFERENCES evidence_packs(pack_id) ON DELETE CASCADE,
  doc_id    TEXT NOT NULL,
  chunk_id  BIGINT NOT NULL,
  rank      INT                -- 在包内的排序位置
);

CREATE INDEX IF NOT EXISTS evidence_pack_items_pack_idx ON evidence_pack_items(pack_id);

-- 验证表已创建
SELECT 'ingest_jobs' as table_name, COUNT(*) as row_count FROM ingest_jobs
UNION ALL
SELECT 'ingest_job_items', COUNT(*) FROM ingest_job_items
UNION ALL
SELECT 'evidence_packs', COUNT(*) FROM evidence_packs
UNION ALL
SELECT 'evidence_pack_items', COUNT(*) FROM evidence_pack_items;

