-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_hash TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT,
    pdf_hash TEXT,
    document_type TEXT,
    classification TEXT,
    risk_flags TEXT,
    seed TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(document_hash);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
