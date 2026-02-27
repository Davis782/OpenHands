
CREATE TABLE IF NOT EXISTS Alarms (
    alarm_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    alarm_time TEXT NOT NULL,
    message TEXT,
    recurrence TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);
