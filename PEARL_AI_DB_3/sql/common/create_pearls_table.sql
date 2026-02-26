
CREATE TABLE IF NOT EXISTS pearl_ids (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    attributes TEXT,
    x REAL,
    y REAL,
    z REAL
);
