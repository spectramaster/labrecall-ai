-- Run this migration against the target database in DATABASE_URL.
-- Vector indexes are enabled by default on current CockroachDB Cloud Basic clusters.

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY,
    namespace STRING NOT NULL,
    pipeline STRING NOT NULL,
    error STRING NOT NULL,
    environment STRING NOT NULL,
    attempted_actions JSONB NOT NULL DEFAULT '[]',
    constraints JSONB NOT NULL DEFAULT '[]',
    embedding VECTOR(1024) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE VECTOR INDEX IF NOT EXISTS incidents_embedding_idx
ON incidents (namespace, embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS outcomes (
    incident_id UUID PRIMARY KEY REFERENCES incidents(id),
    status STRING NOT NULL CHECK (status IN ('worked', 'failed', 'partial')),
    action_taken STRING NOT NULL,
    observation STRING NOT NULL,
    side_effects JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS repair_memories (
    id UUID PRIMARY KEY,
    source_incident_id UUID UNIQUE NOT NULL REFERENCES incidents(id),
    namespace STRING NOT NULL,
    failure_signature STRING NOT NULL,
    repair_action STRING NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    successful_outcomes INT8 NOT NULL DEFAULT 1,
    failed_outcomes INT8 NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE VECTOR INDEX IF NOT EXISTS repair_memories_embedding_idx
ON repair_memories (namespace, embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY,
    namespace STRING NOT NULL,
    event_type STRING NOT NULL,
    subject_id UUID NOT NULL,
    evidence_ids UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    detail JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
