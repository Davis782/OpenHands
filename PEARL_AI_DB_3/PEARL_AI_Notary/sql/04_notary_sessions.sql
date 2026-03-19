-- Notary Sessions table
CREATE TABLE IF NOT EXISTS notary_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_hash TEXT UNIQUE NOT NULL,
    notary_hash TEXT NOT NULL,
    signer_hash TEXT NOT NULL,
    document_hash TEXT NOT NULL,
    state TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    payment_status TEXT DEFAULT 'pending',
    payment_receipt_hash TEXT,
    certificate_path TEXT,
    recording_url TEXT,
    rule_decisions TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (notary_hash) REFERENCES notaries(notary_hash),
    FOREIGN KEY (signer_hash) REFERENCES signers(signer_hash),
    FOREIGN KEY (document_hash) REFERENCES documents(document_hash)
);

CREATE INDEX IF NOT EXISTS idx_sessions_hash ON notary_sessions(session_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_notary ON notary_sessions(notary_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_signer ON notary_sessions(signer_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON notary_sessions(status);
