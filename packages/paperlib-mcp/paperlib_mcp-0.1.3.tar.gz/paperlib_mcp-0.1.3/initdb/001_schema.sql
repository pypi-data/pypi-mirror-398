CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  doc_id          TEXT PRIMARY KEY,          -- 建议用 pdf_sha256
  title           TEXT,
  authors         TEXT,
  year            INT,
  venue           TEXT,
  doi             TEXT,
  url             TEXT,
  pdf_bucket      TEXT NOT NULL DEFAULT 'papers',
  pdf_key         TEXT NOT NULL,              -- papers/{sha256}.pdf
  pdf_sha256      TEXT UNIQUE,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
  chunk_id        BIGSERIAL PRIMARY KEY,
  doc_id          TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  chunk_index     INT NOT NULL,
  section         TEXT,
  page_start      INT,
  page_end        INT,
  text            TEXT NOT NULL,
  token_count     INT,
  tsv             TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
  UNIQUE (doc_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS chunks_doc_idx ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING GIN (tsv);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
  chunk_id        BIGINT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  embedding_model TEXT NOT NULL,
  embedding       VECTOR(1536) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunk_emb_hnsw_cos
ON chunk_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS citations (
  doc_id          TEXT PRIMARY KEY REFERENCES documents(doc_id) ON DELETE CASCADE,
  bibtex          TEXT,
  apa             TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

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
