CREATE EXTENSION IF NOT EXISTS vector;

-- Workflow memory — past successful (goal, dag, metrics) tuples, embedded for similarity search.
CREATE TABLE IF NOT EXISTS workflow_memory (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    goal            TEXT NOT NULL,
    dag             JSONB NOT NULL,
    metrics         JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding       vector(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS workflow_memory_embedding_idx
    ON workflow_memory USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

-- Per-run audit log
CREATE TABLE IF NOT EXISTS workflow_runs (
    id              BIGSERIAL PRIMARY KEY,
    workflow_id     TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    goal            TEXT,
    success         BOOLEAN NOT NULL,
    completed_nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
    failed_nodes    JSONB NOT NULL DEFAULT '[]'::jsonb,
    duration_ms     INTEGER
);

CREATE INDEX IF NOT EXISTS workflow_runs_created_idx
    ON workflow_runs (created_at DESC);
