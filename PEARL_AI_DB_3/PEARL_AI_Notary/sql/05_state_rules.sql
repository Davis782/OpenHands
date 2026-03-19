-- State Rules table
CREATE TABLE IF NOT EXISTS state_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT UNIQUE NOT NULL,
    state_name TEXT NOT NULL,
    ron_allowed INTEGER DEFAULT 1,
    notary_location_required INTEGER DEFAULT 1,
    signer_location_allowed TEXT,
    id_verification TEXT,
    retention_years INTEGER DEFAULT 5,
    certificate_template TEXT,
    allowed_documents TEXT,
    vendor_requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_state_rules_code ON state_rules(state_code);
