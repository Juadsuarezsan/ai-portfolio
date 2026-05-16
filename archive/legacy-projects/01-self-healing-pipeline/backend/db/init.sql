CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS episodic_errors (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    document_type   TEXT NOT NULL,
    error_type      TEXT NOT NULL,
    principle       TEXT NOT NULL,
    context         JSONB NOT NULL,
    resolution      TEXT,
    embedding       vector(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS episodic_errors_doctype_idx
    ON episodic_errors (document_type);

CREATE INDEX IF NOT EXISTS episodic_errors_embedding_idx
    ON episodic_errors USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id               BIGSERIAL PRIMARY KEY,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    document_type    TEXT NOT NULL,
    document_hash    TEXT NOT NULL,
    final_score      NUMERIC(4,3),
    retry_count      INT NOT NULL DEFAULT 0,
    success          BOOLEAN NOT NULL,
    final_output     JSONB,
    errors_history   JSONB
);

CREATE INDEX IF NOT EXISTS pipeline_runs_doctype_idx
    ON pipeline_runs (document_type, created_at DESC);

-- Production spot-check queue. Populated by SpotCheckLogger when a random
-- 1% (SPOTCHECK_RATE) of critic verdicts is flagged for human review.
-- Reviewers later set status='reviewed' and fill human_verdict.
-- Calibration uses the reviewed rows to compute production-side Cohen's kappa,
-- complementing the static gold-set calibration.
CREATE TABLE IF NOT EXISTS critic_disagreements (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at     TIMESTAMPTZ,
    document_type   TEXT NOT NULL,
    document_hash   TEXT NOT NULL,
    critic_report   JSONB NOT NULL,
    human_verdict   JSONB,
    status          TEXT NOT NULL DEFAULT 'pending_review'
                     CHECK (status IN ('pending_review','reviewed','dismissed')),
    reviewer        TEXT
);

CREATE INDEX IF NOT EXISTS critic_disagreements_status_idx
    ON critic_disagreements (status, created_at DESC);
