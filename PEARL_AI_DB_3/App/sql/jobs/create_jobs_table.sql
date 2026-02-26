CREATE TABLE IF NOT EXISTS Jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    description TEXT,
    budget REAL,
    start_date TEXT,
    end_date TEXT,
    pearl_id TEXT NOT NULL
);