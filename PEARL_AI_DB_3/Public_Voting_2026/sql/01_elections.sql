-- Public Voting 2026 - Election Management Schema
-- Manages elections, voting periods, and candidates

CREATE TABLE IF NOT EXISTS elections (
    election_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'active', 'closed', 'cancelled')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    is_anonymous INTEGER DEFAULT 1,
    require_pearl_id_verification INTEGER DEFAULT 1,
    max_votes_per_voter INTEGER DEFAULT 1,
    allow_write_in_candidates INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id TEXT PRIMARY KEY,
    election_id TEXT NOT NULL,
    candidate_name TEXT NOT NULL,
    candidate_description TEXT,
    order_index INTEGER DEFAULT 0,
    is_write_in INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_election ON candidates(election_id);

-- Create election trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_election_timestamp
AFTER UPDATE ON elections
BEGIN
    UPDATE elections SET updated_at = datetime('now') WHERE election_id = NEW.election_id;
END;
