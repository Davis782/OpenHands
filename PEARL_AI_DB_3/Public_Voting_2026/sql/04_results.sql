-- Public Voting 2026 - Results and Audit Schema
-- Stores vote tallies and audit logs

CREATE TABLE IF NOT EXISTS election_results (
    result_id TEXT PRIMARY KEY,
    election_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    vote_count INTEGER DEFAULT 0,
    percentage REAL DEFAULT 0.0,
    is_final INTEGER DEFAULT 0,
    calculated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
    UNIQUE (election_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    election_id TEXT,
    action_type TEXT NOT NULL,
    actor_id TEXT,
    actor_type TEXT CHECK(actor_type IN ('admin', 'voter', 'system')),
    details TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    ip_address TEXT,
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_election_results_election ON election_results(election_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_election ON audit_log(election_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
