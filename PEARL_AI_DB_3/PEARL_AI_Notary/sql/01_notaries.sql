-- Notaries table
CREATE TABLE IF NOT EXISTS notaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notary_hash TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    commission_number TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    commission_expiry DATE NOT NULL,
    seed TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notaries_hash ON notaries(notary_hash);
CREATE INDEX IF NOT EXISTS idx_notaries_jurisdiction ON notaries(jurisdiction);
