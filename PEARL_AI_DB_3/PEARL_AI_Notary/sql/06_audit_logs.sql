-- Audit Logs table
CREATE TABLE IF NOT EXISTS notary_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_hash TEXT,
    action_type TEXT NOT NULL,
    actor_hash TEXT,
    actor_type TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_session ON notary_audit_logs(session_hash);
CREATE INDEX IF NOT EXISTS idx_audit_action ON notary_audit_logs(action_type);
