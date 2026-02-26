CREATE TABLE IF NOT EXISTS pearl_ids (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    attributes TEXT, -- Stored as JSON string
    x REAL,
    y REAL,
    z REAL,
    status TEXT DEFAULT 'active'
);