
CREATE TABLE IF NOT EXISTS Accounting (
    entry_id TEXT PRIMARY KEY,
    pearl_id TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    transaction_date TEXT,
    FOREIGN KEY (pearl_id) REFERENCES pearl_ids(id) ON DELETE CASCADE
);
