CREATE TABLE IF NOT EXISTS Alarms (
    alarm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    pearl_id TEXT NOT NULL,
    alarm_time TEXT NOT NULL,
    message TEXT,
    recurrence TEXT DEFAULT 'once',
    start_date TEXT,
    end_date TEXT,
    snooze_until TEXT,
    dismissed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
);