
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_name TEXT NOT NULL,
    description TEXT,
    budget REAL,
    start_date TEXT,
    end_date TEXT
);
