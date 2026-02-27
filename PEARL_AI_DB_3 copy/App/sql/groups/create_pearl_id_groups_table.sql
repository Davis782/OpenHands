CREATE TABLE IF NOT EXISTS pearl_id_groups (
    group_id TEXT PRIMARY KEY,
    group_name TEXT NOT NULL,
    description TEXT,
    master_key_id TEXT
);