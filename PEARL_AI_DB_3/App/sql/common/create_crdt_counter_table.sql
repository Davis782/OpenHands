
CREATE TABLE IF NOT EXISTS crdt_counter (
    counter_name TEXT NOT NULL,
    site_id TEXT NOT NULL,
    increments INTEGER DEFAULT 0,
    decrements INTEGER DEFAULT 0,
    PRIMARY KEY (counter_name, site_id)
);
