BEGIN;

CREATE TABLE tenants (
    tenant_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(tenant_id) > 0)
);

CREATE TABLE documents (
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, document_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
);

CREATE TABLE document_revisions (
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    revision_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    source_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, revision_id),
    UNIQUE (tenant_id, document_id, revision_id),
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES documents (tenant_id, document_id) ON DELETE CASCADE,
    CHECK (length(content_hash) > 0),
    CHECK (length(source_version) > 0)
);

CREATE TABLE chunks (
    tenant_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    revision_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, chunk_id),
    UNIQUE (tenant_id, revision_id, ordinal),
    FOREIGN KEY (tenant_id, revision_id)
        REFERENCES document_revisions (tenant_id, revision_id) ON DELETE CASCADE,
    CHECK (ordinal >= 0),
    CHECK (length(content_hash) > 0),
    CHECK (length(content) > 0)
);

CREATE TABLE evaluation_runs (
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    pipeline_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, run_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE,
    CHECK (length(dataset_id) > 0),
    CHECK (length(dataset_version) > 0),
    CHECK (length(pipeline_version) > 0)
);

CREATE TABLE evaluation_queries (
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    relevant_ids JSONB NOT NULL,
    PRIMARY KEY (tenant_id, run_id, query_id),
    FOREIGN KEY (tenant_id, run_id)
        REFERENCES evaluation_runs (tenant_id, run_id) ON DELETE CASCADE,
    CHECK (jsonb_typeof(relevant_ids) = 'array')
);

CREATE TABLE retrieved_items (
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    score DOUBLE PRECISION,
    citation TEXT,
    PRIMARY KEY (tenant_id, run_id, query_id, rank),
    FOREIGN KEY (tenant_id, run_id, query_id)
        REFERENCES evaluation_queries (tenant_id, run_id, query_id) ON DELETE CASCADE,
    CHECK (rank > 0),
    UNIQUE (tenant_id, run_id, query_id, item_id)
);

CREATE TABLE comparison_reports (
    tenant_id TEXT NOT NULL,
    report_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    baseline_run_id TEXT NOT NULL,
    candidate_run_id TEXT NOT NULL,
    cutoff_k INTEGER NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, report_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, baseline_run_id)
        REFERENCES evaluation_runs (tenant_id, run_id),
    FOREIGN KEY (tenant_id, candidate_run_id)
        REFERENCES evaluation_runs (tenant_id, run_id),
    CHECK (cutoff_k > 0),
    CHECK (jsonb_typeof(result) = 'object')
);

CREATE INDEX evaluation_runs_dataset_idx
    ON evaluation_runs (tenant_id, dataset_id, dataset_version);

CREATE INDEX chunks_revision_idx
    ON chunks (tenant_id, revision_id, ordinal);

CREATE INDEX retrieved_items_lookup_idx
    ON retrieved_items (tenant_id, query_id, run_id, rank);

CREATE INDEX comparison_reports_dataset_idx
    ON comparison_reports (tenant_id, dataset_id, dataset_version, created_at DESC);

COMMIT;
