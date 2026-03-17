-- Public Voting 2026 - Vote Recording Schema
-- Stores encrypted votes and ensures one-person-one-vote

CREATE TABLE IF NOT EXISTS votes (
    vote_id TEXT PRIMARY KEY,
    election_id TEXT NOT NULL,
    voter_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    vote_timestamp TEXT DEFAULT (datetime('now')),
    vote_hash TEXT NOT NULL,
    encrypted_vote_data TEXT,
    receipt_code TEXT UNIQUE,
    is_valid INTEGER DEFAULT 1,
    validation_message TEXT,
    ip_address TEXT,
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
    UNIQUE (voter_id, election_id)  -- Enforces one-person-one-vote per election
);

CREATE TABLE IF NOT EXISTS vote_receipts (
    receipt_code TEXT PRIMARY KEY,
    vote_id TEXT NOT NULL,
    election_id TEXT NOT NULL,
    voter_id TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    is_voided INTEGER DEFAULT 0,
    void_reason TEXT,
    FOREIGN KEY (vote_id) REFERENCES votes(vote_id),
    FOREIGN KEY (election_id) REFERENCES elections(election_id),
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id)
);

CREATE INDEX IF NOT EXISTS idx_votes_election ON votes(election_id);
CREATE INDEX IF NOT EXISTS idx_votes_voter ON votes(voter_id);
CREATE INDEX IF NOT EXISTS idx_votes_candidate ON votes(candidate_id);
CREATE INDEX IF NOT EXISTS idx_vote_receipts_code ON vote_receipts(receipt_code);
