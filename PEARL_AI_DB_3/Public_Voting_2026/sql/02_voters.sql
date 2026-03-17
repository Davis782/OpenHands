-- Public Voting 2026 - Voter Registration Schema
-- Manages voter registration and eligibility

CREATE TABLE IF NOT EXISTS voters (
    voter_id TEXT PRIMARY KEY,
    pearl_id TEXT NOT NULL,
    voter_display_name TEXT,
    email TEXT,
    registered_at TEXT DEFAULT (datetime('now')),
    is_eligible INTEGER DEFAULT 1,
    last_verified_at TEXT,
    UNIQUE (pearl_id)
);

CREATE TABLE IF NOT EXISTS voter_eligibility (
    eligibility_id TEXT PRIMARY KEY,
    voter_id TEXT NOT NULL,
    election_id TEXT NOT NULL,
    is_eligible INTEGER DEFAULT 1,
    eligibility_verified_at TEXT DEFAULT (datetime('now')),
    reason TEXT,
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id),
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    UNIQUE (voter_id, election_id)
);

CREATE INDEX IF NOT EXISTS idx_voters_pearl_id ON voters(pearl_id);
CREATE INDEX IF NOT EXISTS idx_voter_eligibility_voter ON voter_eligibility(voter_id);
CREATE INDEX IF NOT EXISTS idx_voter_eligibility_election ON voter_eligibility(election_id);
