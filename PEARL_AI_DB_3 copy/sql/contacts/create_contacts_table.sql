
CREATE TABLE IF NOT EXISTS contacts (
    contact_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    email TEXT,
    phone TEXT
);
