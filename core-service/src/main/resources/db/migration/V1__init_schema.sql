-- Baseline schema migration for MSME Underwriting Copilot
-- Enables pgvector extension and defines foundational tables

CREATE EXTENSION IF NOT EXISTS vector;

-- Applicants
CREATE TABLE IF NOT EXISTS applicants (
    id VARCHAR(36) PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,
    legal_entity_type VARCHAR(50) NOT NULL,
    gstin VARCHAR(15),
    pan VARCHAR(10),
    incorporation_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36) NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    page_count INT,
    status VARCHAR(50) NOT NULL DEFAULT 'UPLOADED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document Extractions
CREATE TABLE IF NOT EXISTS extractions (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    extracted_value TEXT,
    confidence_score NUMERIC(5, 4) NOT NULL,
    source_page INT,
    source_line INT,
    bounding_box JSONB,
    extraction_method VARCHAR(50) NOT NULL,
    review_status VARCHAR(50) NOT NULL DEFAULT 'EXTRACTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Review Queue for low confidence fields
CREATE TABLE IF NOT EXISTS review_queue (
    id VARCHAR(36) PRIMARY KEY,
    extraction_id VARCHAR(36) NOT NULL REFERENCES extractions(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'NEEDS_REVIEW',
    assigned_to VARCHAR(100),
    reviewer_comments TEXT,
    corrected_value TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Financial Metrics (computed deterministically)
CREATE TABLE IF NOT EXISTS financial_metrics (
    id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36) NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    metric_code VARCHAR(100) NOT NULL,
    metric_value NUMERIC(15, 4) NOT NULL,
    metric_unit VARCHAR(50),
    time_period VARCHAR(50),
    computation_metadata JSONB,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Credit Memos
CREATE TABLE IF NOT EXISTS credit_memos (
    id VARCHAR(36) PRIMARY KEY,
    applicant_id VARCHAR(36) NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    recommendation VARCHAR(20),
    executive_summary TEXT,
    sections JSONB,
    citations JSONB,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Decision Records (Idempotent approval records)
CREATE TABLE IF NOT EXISTS decision_records (
    id VARCHAR(36) PRIMARY KEY,
    memo_id VARCHAR(36) NOT NULL REFERENCES credit_memos(id) ON DELETE CASCADE,
    applicant_id VARCHAR(36) NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(100) UNIQUE NOT NULL,
    decision VARCHAR(20) NOT NULL,
    approved_amount NUMERIC(15, 2),
    reviewer_notes TEXT,
    decided_by VARCHAR(100) NOT NULL,
    decided_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log (Immutable append-only audit trail)
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    action VARCHAR(50) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    payload JSONB,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Policy Embeddings table for Vector RAG
CREATE TABLE IF NOT EXISTS policy_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    clause_id VARCHAR(50) NOT NULL,
    section_title VARCHAR(255),
    content TEXT NOT NULL,
    chunk_strategy VARCHAR(50) NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_extractions_document_id ON extractions(document_id);
CREATE INDEX IF NOT EXISTS idx_metrics_applicant_id ON financial_metrics(applicant_id);
CREATE INDEX IF NOT EXISTS idx_memos_applicant_id ON credit_memos(applicant_id);
CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
