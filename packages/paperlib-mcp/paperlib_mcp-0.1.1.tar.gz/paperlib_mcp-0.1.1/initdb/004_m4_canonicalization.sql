-- Relation Canonicalization v1
-- 把“很多条几乎同义的关系”归并为一个 canonical relation，但不丢证据。

-- 1) canonical_relations: 表示“合并后的关系键”
CREATE TABLE IF NOT EXISTS canonical_relations (
    canon_rel_id SERIAL PRIMARY KEY,
    subj_entity_id INT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    predicate_norm TEXT NOT NULL,
    obj_entity_id INT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    qualifiers_norm JSONB DEFAULT '{}',
    canonical_key TEXT UNIQUE NOT NULL, -- sha256( subj_entity_id | predicate_norm | obj_entity_id | qualifiers_norm_core )
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2) canonical_relation_evidence: 表示“这个关系键有哪些证据支撑”
CREATE TABLE IF NOT EXISTS canonical_relation_evidence (
    id SERIAL PRIMARY KEY,
    canon_rel_id INT NOT NULL REFERENCES canonical_relations(canon_rel_id) ON DELETE CASCADE,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_id INT REFERENCES chunks(chunk_id) ON DELETE SET NULL,
    quote TEXT,
    confidence REAL DEFAULT 0.8,
    source_rel_id INT REFERENCES relations(rel_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引，方便查询
CREATE INDEX IF NOT EXISTS idx_canonical_relations_subj ON canonical_relations(subj_entity_id);
CREATE INDEX IF NOT EXISTS idx_canonical_relations_obj ON canonical_relations(obj_entity_id);
CREATE INDEX IF NOT EXISTS idx_canonical_relation_evidence_rel ON canonical_relation_evidence(canon_rel_id);
CREATE INDEX IF NOT EXISTS idx_canonical_relation_evidence_doc ON canonical_relation_evidence(doc_id);


-- Claim Grouping v1
-- 对 claim 进行分组/聚类（grouping）

-- 1) claim_groups: 结论簇
CREATE TABLE IF NOT EXISTS claim_groups (
    group_id SERIAL PRIMARY KEY,
    group_key TEXT UNIQUE NOT NULL, -- (topic_key, outcome_family, treatment_family, sign, id_family, setting_country_bin)
    topic_entity_id INT REFERENCES entities(entity_id) ON DELETE SET NULL,
    sign TEXT,
    setting TEXT,
    id_family TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2) claim_group_members: 分组内的 claim
CREATE TABLE IF NOT EXISTS claim_group_members (
    id SERIAL PRIMARY KEY,
    group_id INT NOT NULL REFERENCES claim_groups(group_id) ON DELETE CASCADE,
    claim_id INT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    similarity REAL DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(group_id, claim_id)
);

CREATE INDEX IF NOT EXISTS idx_claim_group_members_group ON claim_group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_claim_group_members_claim ON claim_group_members(claim_id);
