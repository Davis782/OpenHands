-- Signers table
CREATE TABLE IF NOT EXISTS signers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signer_hash TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    id_type TEXT,
    id_number TEXT,
    verification_score REAL,
    seed TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_signers_hash ON signers(signer_hash);
CREATE INDEX IF NOT EXISTS idx_signers_email ON signers(email);
