CREATE TABLE IF NOT EXISTS Accounting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pearl_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    type TEXT NOT NULL
);